import struct
from hashlib import md5
import socket
from packets import packet
from packets.packet import DataPacket, FirstPacket, LastPacket
from packets import *
import time
from datetime import datetime
from pathlib import Path

buffer_size = 5000
local_ip = "0.0.0.0"
local_port = 4010

class ReceiverLogger:
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.results_dir / "results-python-receiver.txt"
        self.transmission_count = 0
        
    def log_transmission(self, stats):
        with open(self.log_file, 'a') as f:
            f.write("\n" + "="*50 + "\n")
            f.write(f"Transmission {self.transmission_count + 1}/10 at {datetime.now().isoformat()}\n")
            f.write(f"File: {stats['file_name']}\n")
            f.write(f"File Size: {stats['file_size']/1024:.2f} KB\n")
            f.write(f"Duration: {stats['duration']:.2f} seconds\n")
            f.write(f"Throughput: {stats['throughput']/1024:.2f} KB/s\n")
            f.write(f"Total Packets: {stats['total_packets']}\n")
            f.write(f"ACKs Sent: {stats['acks_sent']}\n")
            f.write(f"MD5 Match: {stats['md5_match']}\n")
            f.write("="*50 + "\n")
        self.transmission_count += 1

def handle_complete_transmission(transmission_id, tx, logger):
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
            md5_match = md5_actual == md5_expected

        if md5_match:
            print(f"✅ [tx {transmission_id}] MD5 matched for file '{file_path}'")
        else:
            print(f"❌ [tx {transmission_id}] MD5 mismatch for file '{file_path}'")
            print(f"Expected MD5: {md5_expected.hex()}")
            print(f"Actual MD5: {md5_actual.hex()}")

        # Calculate file size and throughput
        file_size = Path(file_path).stat().st_size
        duration = time.time() - tx["start_time"]
        throughput = file_size / duration

        # Log statistics
        stats = {
            'file_name': tx['file_name'],
            'file_size': file_size,
            'duration': duration,
            'throughput': throughput,
            'total_packets': len(tx["packets"]),
            'acks_sent': tx['acks_sent'],
            'md5_match': md5_match
        }
        logger.log_transmission(stats)

        print(f"\nTransmission Statistics:")
        print(f"File: {tx['file_name']}")
        print(f"File Size: {file_size/1024:.2f} KB")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Throughput: {throughput/1024:.2f} KB/s")
        print(f"Total packets received: {len(tx['packets'])}")
        print(f"Total ACKs sent: {tx['acks_sent']}")
        print(f"MD5 Match: {'Yes' if md5_match else 'No'}")
        
        if logger.transmission_count >= 10:
            print("\nReceived 10 transmissions. Shutting down...")
            return True

    except Exception as e:
        print(f"❌ [tx {transmission_id}] Unexpected error: {e}")
    
    return False

def receive_loop(udp_server_socket):
    transmissions = {}
    total_acks_sent = 0
    logger = ReceiverLogger()
    print("\nWaiting for 10 transmissions...")
    print("="*50)

    while True:
        data, addr = udp_server_socket.recvfrom(buffer_size)

        if data == b'q':
            print("Connection closed from client.")
            break

        transmission_id, sequence_number = struct.unpack('!HI', data[:6])

        if transmission_id not in transmissions:
            transmissions[transmission_id] = {
                "packets": {},
                "file_name": None,
                "sequence_numbers": set(),
                "max_sequence_number": None,
                "acks_sent": 0,
                "start_time": time.time()
            }
            print(f"\nNew Transmission: {transmission_id}")

        tx = transmissions[transmission_id]

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
        
        # Send ACK for the received packet
        udp_server_socket.sendto(b'ACK', addr)
        tx["acks_sent"] += 1
        total_acks_sent += 1
            
        max_seq = tx["max_sequence_number"]
        if max_seq is not None:
            expected_packets = max_seq + 2  # +2 for first and last packets
            received_packets = len(tx["packets"])
            print(f"Received {received_packets} of {expected_packets} packets")
            
            if received_packets == expected_packets:
                print("\nAll packets received, saving file...")
                if handle_complete_transmission(transmission_id, tx, logger):
                    break
                del transmissions[transmission_id]

    print(f"\nTotal ACKs sent across all transmissions: {total_acks_sent}")
    print(f"Results have been saved to results/results-python-receiver.txt")

def main():
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server_socket.bind((local_ip, local_port))
    print(f"UDP receiver running on {local_ip}:{local_port}")
    
    try:
        receive_loop(udp_server_socket)
    except KeyboardInterrupt:
        print("\n == Manual shutdown (Ctrl+C) ==")
    finally:
        udp_server_socket.close()
        print("Socket closed.")

if __name__ =="__main__":
    main()