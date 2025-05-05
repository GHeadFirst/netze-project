import struct
from .packet import Packet

class DataPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        super().__init__(transmission_id, sequence_number)
        self.data = data


    def serialization(self,max_packet_size) -> bytes:
        header = struct.pack('!HI', self.transmission_id, self.sequence_number)

        packet_size = struct.calcsize(header) + len(self.data)
        if (packet_size > 1024):
            raise ValueError(f"Data packet is too big, size is {packet_size} Bytes, max size allowed is 1024 Bytes")
            
        return header + self.data
    
    
    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "DataPacket":
        HEADER_FORMAT = '!HI'
        HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


        transmission_id, sequence_number, max_sequence_number = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
        payload = raw[HEADER_SIZE:]
        return cls(transmission_id,sequence_number,payload)
    
    def __str__(self):
        return super().__str__() + f"Packet Data: {self.data} \nPacket Data Decoded (UTF-8): {self.data.decode()}\n" 