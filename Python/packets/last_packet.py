import struct
from packet import Packet

class LastPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, md5: bytes) -> None:
        super().__init__(transmission_id, sequence_number)
        if len(self.md5 != 16):
            raise ValueError("falsche Größe von MD5!")
        self.md5 = md5(16)

    def serialisieren(self) -> bytes:
        header = struct.pack("!HI", self.transmission_id, self.sequence_number)
        return header + self.md5
     
    
    def get_md5(self) -> bytes:
        return self.md5