import struct
from .packet import Packet

class LastPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, md5: bytes) -> None:
        super().__init__(transmission_id, sequence_number)
        if len(md5) != 16:
            raise ValueError("falsche Größe von MD5!")
        self.md5 = md5

    def serialization(self) -> bytes:
        packet = struct.pack('!HII', self.transmission_id, self.sequence_number)
        return packet + self.md5

    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "LastPacket":
        # Add struct.calcsize() to estimate the length of the variable field and then slice the rest of the packet
        # Something like the following HEADER_FORMAT = "!HI"  # tx_id, seq_nr
        # HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
        # payload = data[HEADER_SIZE:]
        HEADER_FORMAT = '!HII16s'
        transmission_id, sequence_number, md5 = struct.unpack(HEADER_FORMAT, raw)
        return cls(transmission_id,sequence_number,md5)

    def __str__(self):
        return super().__str__() + f"Packet MD5: {self.md5} \nPacket MD5 Decoded (UTF-8): {self.md5.decode('UTF-8')}\n" 
 