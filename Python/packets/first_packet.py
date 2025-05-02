import struct 
from packet import Packet


class FirstPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, max_sequence_number: int, file_name: str) -> None: 
        super().__init__(transmission_id, sequence_number)
        self.max_sequence_number = max_sequence_number
        self.file_name = file_name

    def serialisieren(self) -> bytes:
        header = struct.pack("!HII", self.transmission_id, self.sequence_number, self.max_sequence_number)
        return header + self.file_name.encode("utf-8")


    def get_max_sequence_number(self) -> int:
        return self.max_sequence_number
        
    def get_file_name(self) -> str:
        return self.file_name
