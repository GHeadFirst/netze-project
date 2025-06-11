import socket
import time
from datetime import datetime
from pathlib import Path
import struct
from packets import *
import signal
import sys

class ReceiverThroughputLogger:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "transmissions": []
        }
        self.current_transmission = None

    def start_transmission(self, transmission_id, transmitter_type):
        self.current_transmission = {
            "transmission_id": transmission_id,
            "transmitter": transmitter_type,
            "start_time": time.time(),
            "packets_received": 0,
            "acks_sent": 0,
            "file_size": 0
        }

    def log_packet(self, packet_size):
        if self.current_transmission:
            self.current_transmission["packets_received"] += 1
            self.current_transmission["acks_sent"] += 1
            self.current_transmission["file_size"] += packet_size

    def end_transmission(self):
        if self.current_transmission:
            self.current_transmission["end_time"] = time.time()
            self.current_transmission["duration"] = (
                self.current_transmission["end_time"] - 
                self.current_transmission["start_time"]
            )
            self.current_transmission["throughput"] = (
                self.current_transmission["file_size"] / 
                self.current_transmission["duration"]
            )
            self.results["transmissions"].append(self.current_transmission)
            self.current_transmission = None

    def save_results(self):
        # Create results directory if it doesn't exist
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"receiver_throughput_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("RECEIVER THROUGHPUT RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for tx in self.results["transmissions"]:
                f.write(f"Transmission ID: {tx['transmission_id']}\n")
                f.write(f"Transmitter: {tx['transmitter'].upper()}\n")
                f.write(f"Duration: {tx['duration']:.2f} seconds\n")
                f.write(f"File Size: {tx['file_size']/1024:.2f} KB\n")
                f.write(f"Throughput: {tx['throughput']/1024:.2f} KB/s\n")
                f.write(f"Packets Received: {tx['packets_received']}\n")
                f.write(f"ACKs Sent: {tx['acks_sent']}\n")
                f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"\nResults saved to: {output_file}")

def receive_loop(udp_server_socket, logger):
    transmissions = {}
    current_tx_id = None

    while True:
        data, addr = udp_server_socket.recvfrom(5000)

        if data == b'q':
            print("Connection closed from client.")
            break

        transmission_id, sequence_number = struct.unpack('!HI', data[:6])

        # Start new transmission if needed
        if transmission_id != current_tx_id:
            if current_tx_id is not None:
                logger.end_transmission()
            current_tx_id = transmission_id
            # Assume Python transmitter for now - could be enhanced to detect Go
            logger.start_transmission(transmission_id, "python")

        if transmission_id not in transmissions:
            transmissions[transmission_id] = {
                "packets": {},
                "file_name": None,
                "sequence_numbers": set(),
                "max_sequence_number": None
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
        
        # Log packet and send ACK
        logger.log_packet(len(data))
        udp_server_socket.sendto(b'ACK', addr)
            
        max_seq = tx["max_sequence_number"]
        if max_seq is not None:
            expected_packets = max_seq + 2  # +2 for first and last packets
            received_packets = len(tx["packets"])
            print(f"Received {received_packets} of {expected_packets} packets")
            
            if received_packets == expected_packets:
                print("\nAll packets received, saving file...")
                handle_complete_transmission(transmission_id, tx, addr)
                del transmissions[transmission_id]

def main():
    local_ip = "0.0.0.0"
    local_port = 4010
    
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server_socket.bind((local_ip, local_port))
    print(f"UDP receiver running on {local_ip}:{local_port}")
    
    logger = ReceiverThroughputLogger()
    
    try:
        receive_loop(udp_server_socket, logger)
    except KeyboardInterrupt:
        print("\n == Manual shutdown (Ctrl+C) ==")
    finally:
        logger.end_transmission()  # End any ongoing transmission
        logger.save_results()
        udp_server_socket.close()
        print("Socket closed.")

if __name__ == "__main__":
    main() 