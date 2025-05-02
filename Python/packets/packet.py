from abc import ABC, abstractmethod

class Packet(ABC):
    def __init__(self, transmission_id: int, sequence_number: int ) -> None: 
        self.transmission_id = transmission_id
        self.sequence_number = sequence_number

    def get_transmission_id(self) -> int:
        return self.transmission_id
    
    def get_sequence_number(self) -> int:
        return self.sequence_number

