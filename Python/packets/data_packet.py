import struct
from packet import Packet

class DataPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        super.__init__(transmission_id, sequence_number)
        self.data = data


    def serialisieren(self) -> bytes:
        header = struct.pack("!HI", self.transmission_id, self.sequence_number)
        return header + self.data
    
    #def deserialisieren(data: bytes):
    
    
    def get_data(self) -> bytes:
        return self.data
    