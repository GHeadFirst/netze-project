import struct
from hashlib import md5
import socket
from packets import *

local_ip = "0.0.0.0"
local_port = 4010
buffer_size = 5000

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_server_socket.bind((local_ip, local_port))

packet_map = {}
current_transmission_id = None
max_sequence_number = None
file_name = None

print("UDP server listening...")

while True:
    data, addr = udp_server_socket.recvfrom(buffer_size)

    if data == b'q':
        print("Connection closed from client.")
        break
    
    # Extract transmission ID and sequence number
    transmission_id, sequence_number = struct.unpack('!HI', data[:6])

    # If this is a new transmission, reset our state
    if current_transmission_id is None or transmission_id != current_transmission_id:
        current_transmission_id = transmission_id
        packet_map.clear()
        max_sequence_number = None
        file_name = None
        print(f"\nStarting new transmission with ID: {transmission_id}")

    # Process packet based on sequence number
    if sequence_number == 0:
        pkt = FirstPacket.deserialization(data)
        raw_name = pkt.file_name
        clean_name = raw_name.rstrip('\x00')
        file_name = f"received-{clean_name}"
        max_sequence_number = pkt.max_sequence_number
        print(f"Received first packet. Expecting {max_sequence_number + 1} total packets")
    elif sequence_number == max_sequence_number + 1:
        pkt = LastPacket.deserialization(data)
    else:
        pkt = DataPacket.deserialization(data)
    
    packet_map[sequence_number] = pkt
    print(f"Received packet {sequence_number} of {max_sequence_number + 1}")

    # Check if we have all packets for this transmission
    if max_sequence_number is not None:
        expected_packets = max_sequence_number + 2  # +2 for first and last packets
        if len(packet_map) == expected_packets:
            print("\nAll packets received, saving file...")
            break

if file_name is None:
    print("Filename missing. Terminated.")
else:
    with open(file_name, 'wb') as f:
        for key in range(1, max_sequence_number + 1):
            try:
                pkt = packet_map[key]
            except KeyError:
                print(f"Missing packet {key}")
                continue
            f.write(pkt.data)

    with open(file_name, 'rb') as f:
        calculated_md5 = md5(f.read()).digest()
        received_md5 = packet_map[max_sequence_number+1].md5

        if calculated_md5 == received_md5:
            print("File correctly received, MD5 are same!")
        else:
            print("File received, MD5 are different!")

udp_server_socket.close()
