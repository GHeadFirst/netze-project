import socket
import struct
from hashlib import md5
import time
from datetime import datetime
import json
from pathlib import Path
import sys
from packets import packet
from packets.packet import DataPacket, FirstPacket, LastPacket
from packets import *

class ReceiverTester:
    def __init__(self, receiver_type):
        self.receiver_type = receiver_type
        self.logger = ReceiverLogger()
        self.buffer_size = 5000
        self.local_ip = "0.0.0.0"
        self.local_port = 4010
        self.transmissions = {}
        self.runs_completed = 0
        self.max_runs = 10
        self.socket = None

    def setup_socket(self):
        # Create socket with SO_REUSEADDR option
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((self.local_ip, self.local_port))
            print(f"UDP receiver running on {self.local_ip}:{self.local_port}")
            return True
        except OSError as e:
            print(f"Error binding to port {self.local_port}: {e}")
            print("Please make sure no other receiver is running")
            return False

    def cleanup(self):
        if self.socket:
            self.socket.close()
            print("Socket closed.")

    def handle_complete_transmission(self, transmission_id, tx):
        print(f"\nTransmission {transmission_id} complete. Saving file...")
        file_path = f"received-{tx['file_name']}"    
        try:
            with open(file_path, 'wb') as f:
                for i in range(1, tx["max_sequence_number"] + 1):
                    if i not in tx["packets"]:
                        print(f"Warning: Missing packet {i} in transmission {transmission_id}")
                        continue
                    f.write(tx["packets"][i].data)

            with open(file_path, 'rb') as f:
                md5_actual = md5(f.read()).digest()
                last_pkt = tx["packets"][tx["max_sequence_number"] + 1]
                md5_expected = last_pkt.md5

            # Calculate throughput
            file_size = Path(file_path).stat().st_size
            duration = time.time() - tx["start_time"]
            throughput = file_size / duration

            # Log results
            self.logger.log_run(
                run_number=self.runs_completed + 1,
                file_name=tx["file_name"],
                file_size=file_size,
                duration=duration,
                throughput=throughput,
                md5_match=(md5_actual == md5_expected)
            )

            if md5_actual == md5_expected:
                print(f"✅ [tx {transmission_id}] MD5 matched for file '{file_path}'")
            else:
                print(f"❌ [tx {transmission_id}] MD5 mismatch for file '{file_path}'")
                print(f"Expected MD5: {md5_expected.hex()}")
                print(f"Actual MD5: {md5_actual.hex()}")

            self.runs_completed += 1
            if self.runs_completed >= self.max_runs:
                print(f"\nCompleted {self.max_runs} runs!")
                self.logger.save_results()
                return True

        except Exception as e:
            print(f"❌ [tx {transmission_id}] Unexpected error: {e}")
        return False

    def receive_loop(self, udp_server_socket):
        print(f"\n{'='*50}")
        print(f"Starting {self.receiver_type.upper()} receiver test")
        print(f"Waiting for {self.max_runs} transmissions...")
        print(f"{'='*50}\n")

        while True:
            data, addr = udp_server_socket.recvfrom(self.buffer_size)
            transmission_id, sequence_number = struct.unpack('!HI', data[:6])

            if transmission_id not in self.transmissions:
                self.transmissions[transmission_id] = {
                    "packets": {},
                    "file_name": None,
                    "sequence_numbers": set(),
                    "max_sequence_number": None,
                    "start_time": time.time()
                }
                print(f"\nNew Transmission: {transmission_id}")

            tx = self.transmissions[transmission_id]

            if sequence_number == 0:
                pkt = FirstPacket.deserialization(data)
                tx["file_name"] = pkt.file_name
                tx["max_sequence_number"] = pkt.max_sequence_number
                print(f"First packet received. Expecting {pkt.max_sequence_number + 1} total packets")
            elif sequence_number == tx["max_sequence_number"] + 1:
                pkt = LastPacket.deserialization(data)
                print("Last packet received")
            else:
                pkt = DataPacket.deserialization(data)

            tx["packets"][sequence_number] = pkt
            tx["sequence_numbers"].add(sequence_number)
            print(f"Received packet from transmission_id: {transmission_id} with sequence_number: {sequence_number}")
                
            max_seq = tx["max_sequence_number"]
            if max_seq is not None:
                expected_packets = max_seq + 2
                received_packets = len(tx["packets"])
                print(f"Received {received_packets} of {expected_packets} packets")
                
                if received_packets == expected_packets:
                    if self.handle_complete_transmission(transmission_id, tx):
                        break

class ReceiverLogger:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "runs": []
        }

    def log_run(self, run_number, file_name, file_size, duration, throughput, md5_match):
        self.results["runs"].append({
            "run": run_number,
            "timestamp": datetime.now().isoformat(),
            "file_name": file_name,
            "file_size_bytes": file_size,
            "duration_seconds": duration,
            "throughput_bytes_per_second": throughput,
            "throughput_kb_per_second": throughput/1024,
            "md5_match": md5_match
        })

    def save_results(self):
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"receiver_results_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("RECEIVER TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            # Write individual run results
            for run in self.results["runs"]:
                f.write(f"Run {run['run']}:\n")
                f.write(f"  File: {run['file_name']}\n")
                f.write(f"  Duration: {run['duration_seconds']:.2f} seconds\n")
                f.write(f"  Throughput: {run['throughput_kb_per_second']:.2f} KB/s\n")
                f.write(f"  File Size: {run['file_size_bytes']/1024:.2f} KB\n")
                f.write(f"  MD5 Match: {'✅' if run['md5_match'] else '❌'}\n")
                f.write("\n")
            
            # Calculate and write summary statistics
            throughputs = [r["throughput_kb_per_second"] for r in self.results["runs"]]
            durations = [r["duration_seconds"] for r in self.results["runs"]]
            
            f.write("Summary Statistics:\n")
            f.write(f"  Average Duration: {sum(durations)/len(durations):.2f} seconds\n")
            f.write(f"  Average Throughput: {sum(throughputs)/len(throughputs):.2f} KB/s\n")
            f.write(f"  Min Throughput: {min(throughputs):.2f} KB/s\n")
            f.write(f"  Max Throughput: {max(throughputs):.2f} KB/s\n")
            f.write(f"  Successful Transfers: {sum(1 for r in self.results['runs'] if r['md5_match'])}/{len(self.results['runs'])}\n")
        
        print(f"\nResults saved to: {output_file}")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["python", "go"]:
        print("Usage: python receiver_test.py [python|go]")
        sys.exit(1)

    receiver_type = sys.argv[1]
    tester = ReceiverTester(receiver_type)
    
    if not tester.setup_socket():
        sys.exit(1)
    
    try:
        tester.receive_loop(tester.socket)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 