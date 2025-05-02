from packet import Packet

class FirstPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int ) -> None: 
        super.__init__(transmission_id, sequence_number)

    def get_transmission_id(self) -> int:
        return self.transmission_id
    
    def get_sequence_number(self) -> int:
        return self.sequence_number

    def get_max_sequence_number(self) -> int:
            return self.get_max_sequence_number

    def get_file_name(self) -> str:
            return self.get_file_name