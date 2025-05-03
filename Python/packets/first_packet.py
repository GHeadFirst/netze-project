import struct 
from packet import Packet


class FirstPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, max_sequence_number: int, file_name: str) -> None: 
        super().__init__(transmission_id, sequence_number)
        self.max_sequence_number = max_sequence_number
        self.file_name = file_name

    def serialization(self) -> bytes:
        header = struct.pack('!HII', self.transmission_id, self.sequence_number, self.max_sequence_number)
        return header + self.file_name.encode("utf-8")

    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "FirstPacket":
        # Add struct.calcsize() to estimate the length of the variable field and then slice the rest of the packet
        # Something like the following HEADER_FORMAT = "!HI"  # tx_id, seq_nr
        # HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
        # payload = data[HEADER_SIZE:]
        HEADER_FORMAT = '!HII'
        HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


        transmission_id, sequence_number, max_sequence_number = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
        file_name = raw[HEADER_SIZE:].decode("utf-8")
        return cls(transmission_id,sequence_number,max_sequence_number,file_name)

    def __str__(self):
        return super().__str__() + f"Packet max_sequence_number: {self.max_sequence_number} \nPacket file name: {self.file_name}\n" 

