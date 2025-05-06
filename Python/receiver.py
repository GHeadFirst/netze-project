import struct
import hashlib
import socket

local_ip = "127.0.0.1"
local_port = 4010
buffer_size = 1024

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_server_socket.bind((local_ip, local_port))

packet_map = {}
max_sequence_number = None
file_name = None

print("UDP server listening...")

while True:
    data, addr = udp_server_socket.recvfrom(buffer_size)

    # Vermeide decode() bei Binärdaten!
    if data == b'q':
        print("Connection closed from client.")
        break

    # Header lesen (6 Byte)
    if len(data) < 6:
        continue  # Ungültiges Paket
    transmission_id, sequence_number = struct.unpack("!HI", data[:6])

    if sequence_number == 0:
        max_sequence_number = struct.unpack("!I", data[6:10])[0]
        file_name = data[10:266].rstrip(b"\x00").decode()
        packet_map[sequence_number] = ("first", None)
        print(f"FirstPacket received – file: {file_name}, max_seq: {max_sequence_number}")
    elif sequence_number == max_sequence_number+1:
        md5_value = data[6:22]
        packet_map[sequence_number] = ("last", md5_value)
        print("LastPacket received")
        break
    else:
        packet_map[sequence_number] = ("data", data[6:])
        print(f"DataPacket received – Seq: {sequence_number}, Size: {len(data[6:])} Bytes")

print("\nSave file...")

if file_name is None:
    print("Filename missing. Terminated.")
else:
    with open(file_name, 'wb') as f:
        for seq in sorted(packet_map.keys()):
            kind, content = packet_map[seq]
            if kind == "data":
                f.write(content)

    with open(file_name, 'rb') as f:
        calculated_md5 = hashlib.md5(f.read()).digest()
        received_md5 = packet_map[max_sequence_number+1][1]

        if calculated_md5 == received_md5:
            print("File correctly received, MD5 are same!")
        else:
            print("File received, MD5 are different!")

udp_server_socket.close()
