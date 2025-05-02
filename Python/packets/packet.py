from abc import ABC, abstractmethod

class Packet(ABC):
    def __init__(self, transmission_id: int, sequence_number: int ) -> None: 
        self.transmission_id = transmission_id
        self.sequence_number = sequence_number

    @abstractmethod
    def get_transmission_id(self) -> int:
        pass # pass means there is no implementation here cause --> abstract
    
    @abstractmethod
    def get_sequence_number(self) -> int:
        pass

