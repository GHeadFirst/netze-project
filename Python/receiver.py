import struct
from hashlib import md5
import socket
from packets import packet
from packets.packet import DataPacket, FirstPacket, LastPacket
from packets import *

buffer_size = 5000
local_ip = "0.0.0.0"
local_port = 4010


def handle_complete_transmission(transmission_id, tx, client_address):
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

        if md5_actual == md5_expected:
            print(f"✅ [tx {transmission_id}] MD5 matched for file '{file_path}'")
        else:
            print(f"❌ [tx {transmission_id}] MD5 mismatch for file '{file_path}'")
            print(f"Expected MD5: {md5_expected.hex()}")
            print(f"Actual MD5: {md5_actual.hex()}")
    except Exception as e:
        print(f"❌ [tx {transmission_id}] Unexpected error: {e}")


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
        print(f"Received packet from transmission_id: {transmission_id} with sequence_number: {sequence_number}")
        
        # Send ACK for the received packet
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