import struct
import hashlib
import socket # spricht mit deinem OS, und sagt Windows,Linux oder Mac, hey offnene ein Socket

from packets import Packet, FirstPacket, DataPacket, LastPacket


local_ip= "127.0.0.1"
local_port = 4010
buffer_size = 1024 #  And in real-world networks (with MTU ~1500), you usually don't want to send more than about 1400 bytes per packet — or else you risk fragmentation and packet loss.


# message to client
msg_from_server = "Hello UDP Client\n"

# Hinweis hier, socket.socket() erstellt einfach ein socket, dieses socket erlaubt uns unseren Netzwerk hinzuhören
# wenn wir type = socket-SOCK_DGRAM als argument eingeben wir sagen hey OS, mach für uns ein UDP socket
# und dass uns erlaubt UDP pakete zu bekommen, das erste Argument, AF_INET bedeuet benutze IPv4, 

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

udp_server_socket.bind((local_ip, local_port))

max_sequence_number = None
file_name = None
packet_map= {}
                      
print("UDP server up and listning")

while True:
    
    # Receive data
    print(f"Received data:")
    data, addr = udp_server_socket.recvfrom(1024)

    if (data.decode() == 'q'):
        print("Connection closed from Receiver (UDP SERVER)")
        break

    header_format = '!HI'
    header_size = struct.calcsize(header_format)
    transmission_id, sequence_number = struct.unpack('!HI', data[:6])

    if (sequence_number == 0):
        current_packet = FirstPacket.deserialization(data)
        file_name = current_packet.file_name
        max_sequence_number = current_packet.max_sequence_number
        packet_map[sequence_number] = current_packet
        print(f"Firstpacket erhalten - Datei: {file_name}, max_seq: {max_sequence_number}")
    
    elif max_sequence_number is not None and sequence_number == max_sequence_number:
        current_packet = LastPacket.deserialization(data)
        packet_map[sequence_number] = current_packet
        print(f"Lastpaket erhalten !")

    else:
        current_packet = DataPacket.deserialization(data)
        packet_map[sequence_number] = current_packet
        print(f"Datapaket erhaltne ! - Seq: {sequence_number}, Größe: {len(current_packet.data)} Bytes")        
print ("\n Datei speichern")

with open(file_name, 'wb') as f:
    for seq in sorted(packet_map.keys()):
        pkt = packet_map[seq]
        if isinstance(pkt, DataPacket):
            f.write(pkt.data)

with open(file_name, 'rb') as f:
    hasher = hashlib.md5()
    hasher.update(f.read())

    recieved_md5 = packet_map[max_sequence_number].md5
    calc_md5 = hasher.digest()
    
    if recieved_md5 == calc_md5 :
        print("Nachricht vollständig und korrekt übertragen !")
    else:
        print("Datei nicht korrekt übertragen, Vorsicht !")
udp_server_socket.close()


