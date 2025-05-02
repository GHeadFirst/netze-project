from packet import Packet

class LastPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, md5: str) -> None:
        self.transmission_id = transmission_id
        self.sequence_number = sequence_number
        self.md5 = md5

    def get_transmission_id(self) -> int:
        return self.transmission_id
    
    def get_sequence_number(self) -> int:
        return self.sequence_number
    
    def get_md5(self) -> str:
        return self.md5