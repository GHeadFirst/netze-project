import struct
from hashlib import md5
import socket
from packets import *

local_ip = "127.0.0.1"
local_port = 4010
buffer_size = 1024

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_server_socket.bind((local_ip, local_port))

packet_map = {}
transmission_id = 0
max_sequence_number = None
file_name = None

print("UDP server listening...")

while True:
    data, addr = udp_server_socket.recvfrom(buffer_size)

    # Vermeide decode() bei Binärdaten!
    if data == b'q':
        print("Connection closed from client.")
        break
    
    # First we extract our sequence number, since it says what data_packekt we are dealing with
    sequence_number = struct.unpack('!HI', data[:6])[1]

    # Check what the sequence number is equal to
    if sequence_number == 0:
        pkt = FirstPacket.deserialization(data)
        max_sequence_number = pkt.sequence_number
        file_name = "received-"+ pkt.file_name 
    else:
        pkt = DataPacket.deserialization(data)
    
    packet_map[sequence_number] = pkt

    if max_sequence_number is not None and sequence_number == max_sequence_number + 1:
        transmission_id += 1
        break

print("\nSave file...")

raw_last = packet_map[max_sequence_number + 1].data
last_pkt = LastPacket(packet_map[max_sequence_number + 1].transmission_id,
                      max_sequence_number + 1,
                      raw_last)
packet_map[max_sequence_number + 1] = last_pkt

if file_name is None:
    print("Filename missing. Terminated.")
else:
    with open(file_name, 'wb') as f:
        for key in range(1, max_sequence_number + 1):
            try:
                pkt = packet_map[key]
            except KeyError:
                print(f"missing packet {key}")
                continue
            f.write(pkt.data)

    with open(file_name, 'rb') as f:
        calculated_md5 = md5(f.read()).digest()
        received_md5 = packet_map[max_sequence_number+1].md5 # We get bytes not a hash here

        if calculated_md5 == received_md5:
            print("File correctly received, MD5 are same!")
        else:
            print("File received, MD5 are different!")

udp_server_socket.close()
