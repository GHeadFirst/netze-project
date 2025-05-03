import socket # spricht mit deinem OS, und sagt Windows,Linux oder Mac, hey offnene ein Socket
from packets import Packet,FirstPacket,DataPacket,LastPacket
import os

# Wichtige hinweis hier, unserer Receiver, ist eigentlich unsere UDP server, unserer UDP client ist unserer Transmitter
# Transmmiter (UDP client) schickt an Receiver(UDP server) packeten, und der Server hört einfach über den Port hin

local_ip= "127.0.0.1"
local_port = 4010
buffer_size = 1024 #  And in real-world networks (with MTU ~1500), you usually don't want to send more than about 1400 bytes per packet — or else you risk fragmentation and packet loss.


# message to client
msg_from_server = "Hello UDP Client\n"

message_as_bytes = str.encode(msg_from_server)

# Hinweis hier, socket.socket() erstellt einfach ein socket, dieses socket erlaubt uns unseren Netzwerk hinzuhören
# wenn wir type = socket-SOCK_DGRAM als argument eingeben wir sagen hey OS, mach für uns ein UDP socket
# und dass uns erlaubt UDP pakete zu bekommen, das erste Argument, AF_INET bedeuet benutze IPv4, 

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

udp_server_socket.bind((localIP,localPort))

max_sequence_number = None
file_name = None

packet_map = {}
                      
print("UDP server up and listning")

while True:
    
    # Receive data
    print(f"Received data:")
    data, addr = udp_server_socket.recvfrom(1024)

    if (data.decode() == 'q'):
        print("Connection closed from Receiver (UDP SERVER)")
        break

    current_transmission_id, current_sequence_number = data.struct.unpack('!HI',transmission_id, sequence_number)

    if (current_sequence_number == 0):
        current_packet = FirstPacket(data)
        

    
udp_server_socket.close()




