import socket # spricht mit deinem OS, und sagt Windows,Linux oder Mac, hey offnene ein Socket
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

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

UDPServerSocket.bind((localIP,localPort))

print("UDP server up and listning")