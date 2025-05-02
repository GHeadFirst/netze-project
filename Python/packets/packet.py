from abc import ABC, abstractmethod

class Packet(ABC):

    @abstractmethod
    def get_transmission_id(self) -> int:
        pass # pass means there is no implementation here cause --> abstract
    
    @abstractmethod
    def get_sequence_number(self) -> int:
        pass

