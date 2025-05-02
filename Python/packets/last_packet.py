from packet import Packet

class LastPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, md5: str) -> None:
        super().__init__(transmission_id, sequence_number)
        self.md5 = md5

    
    def get_md5(self) -> str:
        return self.md5