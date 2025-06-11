import socket
from packets import *
import math
from pathlib import Path
from hashlib import md5
import time
import sys
from datetime import datetime


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

class TransmitterLogger:
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.results_dir / "results-python-transmitter.txt"
        
    def log_transmission(self, stats):
        with open(self.log_file, 'a') as f:
            f.write("\n" + "="*50 + "\n")
            f.write(f"Transmission at {datetime.now().isoformat()}\n")
            f.write(f"File: {stats['file_name']}\n")
            f.write(f"File Size: {stats['file_size']/1024:.2f} KB\n")
            f.write(f"Duration: {stats['duration']:.2f} seconds\n")
            f.write(f"Throughput: {stats['throughput']/1024:.2f} KB/s\n")
            f.write(f"Total Packets: {stats['total_packets']}\n")
            f.write(f"ACKs Received: {stats['acks_received']}\n")
            f.write(f"Retries: {stats['retries']}\n")
            f.write(f"Success Rate: {stats['success_rate']:.1f}%\n")
            f.write("="*50 + "\n")

class Transmitter:
    transmission_id = 0  # Class variable to track transmission IDs
    DEFAULT_TIMEOUT = 1.0  # Default timeout in seconds

    def __init__(self, target_ip_address, target_port):
        self.udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_client_socket.settimeout(self.DEFAULT_TIMEOUT)
        self.target_address = (target_ip_address, target_port)
        self.acks_received = 0
        self.retries = 0
        self.logger = TransmitterLogger()
        print("UDP socket created and bound.")

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
                            self.acks_received += 1
                            print(f"Received ACK for packet {packet.sequence_number}")
                            return True
                    except socket.timeout:
                        print(f"Timeout waiting for ACK for packet {packet.sequence_number}")
                        break
                
                retries += 1
                self.retries += 1
                print(f"Retrying packet {packet.sequence_number} (attempt {retries}/{max_retries})")
                
            except Exception as e:
                print(f"Error sending packet: {e}")
                retries += 1
        
        print(f"Failed to send packet {packet.sequence_number} after {max_retries} attempts")
        return False

    def send_packets(self, packets: list, file_name: str, file_size: int):
        """Send packets using Stop-and-Wait protocol"""
        total_packets = len(packets)
        start_time = time.time()
        
        for packet in packets:
            if not self.send_packet_with_ack(packet):
                print(f"Failed to send packet {packet.sequence_number}, aborting transmission")
                self.close_socket()
                return False
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = file_size / duration
        
        stats = {
            'file_name': file_name,
            'file_size': file_size,
            'duration': duration,
            'throughput': throughput,
            'total_packets': total_packets,
            'acks_received': self.acks_received,
            'retries': self.retries,
            'success_rate': (self.acks_received/total_packets)*100
        }
        
        # Log statistics
        self.logger.log_transmission(stats)
        
        print(f"\nTransmission Statistics:")
        print(f"File: {file_name}")
        print(f"File Size: {file_size/1024:.2f} KB")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Throughput: {throughput/1024:.2f} KB/s")
        print(f"Total packets sent: {total_packets}")
        print(f"Total ACKs received: {self.acks_received}")
        print(f"Total retries needed: {self.retries}")
        print(f"Success rate: {(self.acks_received/total_packets)*100:.1f}%")
        
        self.close_socket()
        return True

    def close_socket(self) -> str:
        self.udp_client_socket.close()
        return "Socket closed"

def run_transmission(file_name, target_ip, transmission_id):
    file_size = Path(file_name).stat().st_size
    builder = PacketBuilder(file_name, 1024, transmission_id)
    tx = Transmitter(target_ip, 4010)
    success = tx.send_packets(builder.get_all_packets(), file_name, file_size)
    
    if not success:
        print(f"Transmission {transmission_id} failed")
        return False
    else:
        print(f"Transmission {transmission_id} completed successfully")
        return True

def main():
    # Get file name from command line or use default
    file_name = sys.argv[1] if len(sys.argv) > 1 else "test_50mb.bin"
    target_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    
    print(f"\nStarting 10 transmissions of {file_name} to {target_ip}")
    print("="*50)
    
    successful_transmissions = 0
    for i in range(10):
        current_tx_id = Transmitter.transmission_id
        Transmitter.transmission_id += 1
        
        print(f"\nStarting transmission {i+1}/10 (ID: {current_tx_id})")
        if run_transmission(file_name, target_ip, current_tx_id):
            successful_transmissions += 1
        print(f"Completed transmission {i+1}/10")
        print("-"*50)
    
    print(f"\nTransmission Summary:")
    print(f"Total transmissions: 10")
    print(f"Successful: {successful_transmissions}")
    print(f"Failed: {10 - successful_transmissions}")
    print(f"Success rate: {(successful_transmissions/10)*100:.1f}%")
    print(f"Results have been saved to results/results-python-transmitter.txt")

if __name__ == "__main__":
    main()
