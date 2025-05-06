from abc import ABC, abstractmethod
import struct

class Packet(ABC):
    def __init__(self, transmission_id: int, sequence_number: int ) -> None: 
        self.transmission_id = transmission_id
        self.sequence_number = sequence_number

    @abstractmethod
    def serialization(self):
        pass
    
    @classmethod
    @abstractmethod
    def deserialization(cls):
        pass # Because it is an abstract method, implement code in subclass

    def __str__(self):
        return f"Packet tx_id:{self.transmission_id} \nPacket seq_nummer:{self.sequence_number} \n"

    # def __repr__(self):

