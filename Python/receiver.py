import struct
from hashlib import md5
import socket
import time
import os
from packets import *

local_ip = "127.0.0.1"
local_port = 4010
buffer_size = 5000

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_server_socket.bind((local_ip, local_port))

packet_map = {}
transmission_id = 0
max_sequence_number = None
file_name = None

print("UDP server listening...")

# start timing
start = time.time()

while True:
    data, addr = udp_server_socket.recvfrom(buffer_size)

    # end of transmission marker
    if data == b'q':
        print("Connection closed from client.")
        break
    
    # unpack sequence number
    sequence_number = struct.unpack('!HI', data[:6])[1]

    if sequence_number == 0:
        pkt = FirstPacket.deserialization(data)
        raw_name = pkt.file_name
        clean_name = raw_name.rstrip('\x00')
        file_name = f"received-{clean_name}"
        max_sequence_number = pkt.max_sequence_number
    else:
        pkt = DataPacket.deserialization(data)
    
    packet_map[sequence_number] = pkt

    # last packet of this run?
    if max_sequence_number is not None and sequence_number == max_sequence_number + 1:
        transmission_id += 1
        break

print("\nSave file...")

# reconstruct last-packet object so we can get its MD5
raw_last = packet_map[max_sequence_number + 1].data
last_pkt = LastPacket(
    packet_map[max_sequence_number + 1].transmission_id,
    max_sequence_number + 1,
    raw_last
)
packet_map[max_sequence_number + 1] = last_pkt

# write data packets
if file_name is None:
    print("Filename missing. Terminated.")
else:
    with open(file_name, 'wb') as f:
        for key in range(1, max_sequence_number + 1):
            if key not in packet_map:
                print(f"missing packet {key}")
                continue
            f.write(packet_map[key].data)

    # MD5 validation
    with open(file_name, 'rb') as f:
        calculated_md5 = md5(f.read()).digest()
        received_md5   = packet_map[max_sequence_number + 1].md5

        if calculated_md5 == received_md5:
            print("File correctly received, MD5 are same!")
        else:
            print("File received, MD5 are different!")

# stop timing
end = time.time()
duration = end - start

# compute throughput
size_bytes = os.path.getsize(file_name)
kb_s   = size_bytes / duration / 1024
mbit_s = size_bytes * 8 / duration / 1_000_000

print(f"\n→ Duration:  {duration:.3f} s")
print(f"→ Throughput: {kb_s:.1f} KB/s   ({mbit_s:.2f} Mbit/s)")

udp_server_socket.close()
