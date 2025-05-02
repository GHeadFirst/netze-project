from packet import Packet

class DataPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        super.__init__(transmission_id, sequence_number)
        self.data = data

    def get_transmission_id(self) -> int:
        return self.transmission_id
    
    def get_sequence_number(self) -> int:
        return self.sequence_number

    def get_data(self) -> bytes:
        return self.data
    