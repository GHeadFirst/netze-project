import struct
from hashlib import md5
import socket
from Python import packets
from Python.packets.packet import DataPacket, FirstPacket
from packets import *

buffer_size = 5000
local_ip = "0.0.0.0"
local_port = 4010


def handle_complete_transmission(transmission_id, tx):
    print(f"\nTransmission {transmission_id} complete. Saving file...")
    file_path = tx["file_name"]
    
    with open(file_path, 'wb') as f:
        for i in range(1, tx["max_sequence_number"] + 1):
            f.write(tx["packets"][i].data)

    with open(file_path, 'rb') as f:
        md5_actual = md5(f.read()).digest()
        last_pkt_raw = tx["packets"][tx["max_sequence_number"] + 1].serialization()
        last_pkt = LastPacket.deserialization(last_pkt_raw)
        md5_expected = last_pkt.md5

    if md5_actual == md5_expected:
        print(f"✅ [tx {transmission_id}] MD5 matched for file '{file_path}'")
    else:
        print(f"❌ [tx {transmission_id}] MD5 mismatch for file '{file_path}'")


def receive_loop(udp_server_socket):
    transmissions = {}

    while True:

        data, addr = udp_server_socket.recvfrom(buffer_size)


        if data == b'q':
            print("Connection closed from client.")
            break

        transmission_id, sequence_number = struct.unpack('!HI', data[:6])

        if transmission_id not in transmissions:
            transmissions[transmission_id] = {
                "packets" : {},
                "file_name" : None,
                "sequence_numbers": set(),
                "max_sequence_number": None
            }
            print(f"\n New Transmission: {transmission_id}")

        tx = transmissions[transmission_id]

        if sequence_number == 0:
            pkt = FirstPacket.deserialization(data)
            tx["file_name"] = pkt.file_name
            tx["max_sequence_number"] = pkt.max_sequence_number

        else:
            pkt = DataPacket.deserialization(data)

        tx["packets"][sequence_number] = pkt
        tx["sequence_numbers"].add(sequence_number)
        print(f"Received packet from transmission_id: {transmission_id} with sequence_number: {sequence_number}")
            
        max_seq = tx["max_sequence_number"]
        if max_seq is not None:
            expected = set(range(0, max_seq + 2))
            if tx["sequence_numbers"] == expected:
                handle_complete_transmission(transmission_id, tx)
                del transmissions[transmission_id]


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