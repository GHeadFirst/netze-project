import struct
from .packet import Packet

class DataPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        super().__init__(transmission_id, sequence_number)
        self.data = data


    def serialization(self) -> bytes:
        header = struct.pack('!HI', self.transmission_id, self.sequence_number)
        return header + self.data
    
    
    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "DataPacket":
        HEADER_FORMAT = '!HI'
        HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


        transmission_id, sequence_number = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
        payload = raw[HEADER_SIZE:]
        return cls(transmission_id,sequence_number,payload)
    
    def __str__(self):
        length = len(self.data)
        # show up to first 8 bytes in hex, so you can see real content or emptiness
        preview = self.data[:8].hex() + ("…" if length > 8 else "")
        return (
            super().__str__() +
            f"DataPacket length={length} bytes, preview(hex)={preview}\n"
        )