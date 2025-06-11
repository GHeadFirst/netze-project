import socket
from packets import *
import math
from pathlib import Path
from hashlib import md5
import time
import sys
import os


# file_name = test_data.txt
project_root = Path(__file__).resolve().parent.parent
transmission_id = 0
max_sequence_number = None

class FileReader():

    def __init__(self,file_name) -> None:
        file_to_read = project_root / file_name
        self.file = file_to_read
        self.file_name = file_to_read.name
        try:
            file_size = file_to_read.stat().st_size
            self.file_size = file_size
            with file_to_read.open("rb") as f:
                contents = f.read()
                self.contents = contents
                self.md5_hash = md5(self.contents).digest() 
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file_name} not found.")

    def get_chunk(self,offset,amount_of_bytes) -> bytes:
        if offset >= self.file_size:
            raise ValueError(f"Offset {offset} exceeds file size {self.file_size}")

        if amount_of_bytes <= 0:
           raise ValueError("amount_of_bytes must be positive")

        chunk_of_data = self.contents[offset: offset + amount_of_bytes]
        return chunk_of_data
    
    def get_total_chunks(self,buffer_size) -> int:
        return math.ceil(self.file_size / buffer_size)


class PacketBuilder():
    def __init__(self,file_name,buffer_size,transmission_id) -> None:
        # Our class Variables
        self.sequence_number = 0
        self.transmission_id = transmission_id

        file = FileReader(file_name)
        self.file = file
        self.buffer_size = buffer_size
        self.first_packet = None
        self.data_packets = []
        self.last_packet = None

    def create_first_packet(self) -> FirstPacket:
        self.max_sequence_number = self.file.get_total_chunks(self.buffer_size)
        self.first_packet = FirstPacket(self.transmission_id, self.sequence_number,
            self.max_sequence_number, self.file.file_name)
        self.sequence_number += 1

    def create_data_packet(self) -> DataPacket:
        # Create data packets from 1 to max_sequence_number
        for i in range(1, self.max_sequence_number + 1):
            offset = (i - 1) * self.buffer_size
            chunk = self.file.get_chunk(offset, self.buffer_size)
            new_data_packet = DataPacket(self.transmission_id, i, chunk)
            self.data_packets.append(new_data_packet)

    def create_last_packet(self) -> LastPacket:
        # Last packet should be at max_sequence_number + 1
        self.last_packet = LastPacket(self.transmission_id, self.max_sequence_number + 1, self.file.md5_hash) 

    def get_all_packets(self) -> list:
        self.create_first_packet()
        self.create_data_packet()
        self.create_last_packet()
        return [self.first_packet] + self.data_packets + [self.last_packet]

class Transmitter:
    transmission_id = 0  # Class variable to track transmission IDs
    DEFAULT_TIMEOUT = 1.0  # Default timeout in seconds

    def __init__(self, target_ip_address, target_port):
        self.udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Get timeout from environment variable or use default
        timeout = float(os.environ.get("UDP_TIMEOUT", self.DEFAULT_TIMEOUT))
        self.udp_client_socket.settimeout(timeout)
        self.target_address = (target_ip_address, target_port)
        print(f"UDP socket created and bound (timeout: {timeout}s).")

    def send_packet_with_ack(self, packet):
        """Send a packet and wait for ACK"""
        max_retries = 3
        retries = 0
        
        while retries < max_retries:
            try:
                # Send the packet
                packet_in_bytes = packet.serialization()
                self.udp_client_socket.sendto(packet_in_bytes, self.target_address)
                print(f"Sending packet tx_id={packet.transmission_id} seq={packet.sequence_number}")
                
                # Wait for ACK
                while True:
                    try:
                        data, addr = self.udp_client_socket.recvfrom(1024)
                        if data == b'ACK':
                            print(f"Received ACK for packet {packet.sequence_number}")
                            return True
                    except socket.timeout:
                        print(f"Timeout waiting for ACK for packet {packet.sequence_number}")
                        break
                
                retries += 1
                print(f"Retrying packet {packet.sequence_number} (attempt {retries}/{max_retries})")
                
            except Exception as e:
                print(f"Error sending packet: {e}")
                retries += 1
        
        print(f"Failed to send packet {packet.sequence_number} after {max_retries} attempts")
        return False

    def send_packets(self, packets: list):
        """Send packets using Stop-and-Wait protocol"""
        for packet in packets:
            if not self.send_packet_with_ack(packet):
                print(f"Failed to send packet {packet.sequence_number}, aborting transmission")
                self.close_socket()
                return False
        
        self.close_socket()
        return True

    def close_socket(self) -> str:
        self.udp_client_socket.close()
        return "Socket closed"

def main():
    # Get current transmission ID and increment for next use
    current_tx_id = Transmitter.transmission_id
    Transmitter.transmission_id += 1
    
    # Get file name and target IP from command line or use defaults
    file_name = sys.argv[1] if len(sys.argv) > 1 else "test_data.txt"
    target_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    
    builder = PacketBuilder(file_name, 1024, current_tx_id)
    tx = Transmitter(target_ip, 4010)
    success = tx.send_packets(builder.get_all_packets())
    
    if not success:
        print("Transmission failed")
        sys.exit(1)
    else:
        print("Transmission completed successfully")

if __name__ == "__main__":
    main()
