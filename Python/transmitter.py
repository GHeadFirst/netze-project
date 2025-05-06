import socket
from packets import *
import math
from pathlib import Path
from hashlib import md5

# file_name = test_data.txt
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
                self.md5_hash = md5(self.contents).hexdigest() 
            
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
    def __init__(self,file_name,buffer_size) -> None:
        # Our class Variables
        self.sequence_number = 0

        file = FileReader(file_name)
        self.file = file
        self.buffer_size = buffer_size
        self.first_packet = None
        self.data_packets = []
        self.last_packet = None

    def create_first_packet(self) -> FirstPacket:
        self.max_sequence_number = self.file.get_total_chunks(self.buffer_size)
        self.first_packet = FirstPacket(transmission_id,self.sequence_number,self.file.get_total_chunks(self.buffer_size),self.file.file_name)
        self.sequence_number += 1

    def create_data_packet(self) -> DataPacket:
        max_amount_of_packets = self.file.get_total_chunks(self.buffer_size)
        offset = 0
        current_packet = 0
        while (current_packet < max_amount_of_packets):
            chunk = self.file.get_chunk(offset,self.buffer_size)
            offset += self.buffer_size
            new_data_packet = DataPacket(transmission_id,self.sequence_number,chunk)
            self.sequence_number += 1
            self.data_packets.append(new_data_packet)
            current_packet += 1


    def create_last_packet(self) -> LastPacket:
        self.last_packet = LastPacket(transmission_id,self.sequence_number,self.file.md5_hash) 

    def get_all_packets(self) -> list:
        self.create_first_packet()
        self.create_data_packet()
        self.create_last_packet()
        return [self.first_packet] + self.data_packets + [self.last_packet]
class Transmitter:

    # Wichtige hinweis hier, unserer Receiver, ist eigentlich unsere UDP server, unserer UDP client ist unserer Transmitter
    # Transmmiter (UDP client) schickt an Receiver(UDP server) packeten, und der Server hört einfach über den Port hin
    def __init__(self, target_ip_address,target_port):
        self.udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.target_address = (target_ip_address,target_port)
        
        print("UDP socket created and bound.")


    def send_packets(self,packets:list):
        for packet in packets:
            if (type(packet) == DataPacket):
                packet = packet.serialization(self.buffer_size)
            else:
                packet = packet.serialization()
            self.udp_client_socket.sendto(packet,self.target_address)
            print(f"Sending packet seq={packet.sequence_number}")
        self.close_socket()

    def close_socket(self) -> str:
        self.udp_client_socket.close()
        return "Socket closed"

def main():
    builder = PacketBuilder("test_data.txt", 1024)
    tx = Transmitter("127.0.0.1", 4010)
    tx.send_packets(builder.get_all_packets())

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent




    main()
