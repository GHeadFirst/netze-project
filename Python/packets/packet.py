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


class DataPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        super().__init__(transmission_id, sequence_number)
        self.data = data


    def serialization(self) -> bytes:
        header = struct.pack('!HI', self.transmission_id, self.sequence_number)
        return header + self.data
    
    
    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "DataPacket":
        HEADER_FORMAT = '!HI'
        HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


        transmission_id, sequence_number = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
        payload = raw[HEADER_SIZE:]
        return cls(transmission_id,sequence_number,payload)
    
    def __str__(self):
        length = len(self.data)
        # show up to first 8 bytes in hex, so you can see real content or emptiness
        preview = self.data[:8].hex() + ("…" if length > 8 else "")
        return (
            super().__str__() +
            f"DataPacket length={length} bytes, preview(hex)={preview}\n"
        )

class LastPacket(Packet):
    def __init__(self, transmission_id: int, sequence_number: int, md5: bytes) -> None:
        super().__init__(transmission_id, sequence_number)
        """ if len(md5) != 16:
            raise ValueError("falsche Größe von MD5!") """
        self.md5 = md5

    def serialization(self) -> bytes:
        packet = struct.pack('!HI', self.transmission_id, self.sequence_number)
        return packet + self.md5

    @classmethod # Class method is like a second constructor
    def deserialization(cls,raw:bytes) -> "LastPacket":
        # Add struct.calcsize() to estimate the length of the variable field and then slice the rest of the packet
        # Something like the following HEADER_FORMAT = "!HI"  # tx_id, seq_nr
        # HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
        # payload = data[HEADER_SIZE:]
        HEADER_FORMAT = '!HI16s'
        transmission_id, sequence_number, md5 = struct.unpack(HEADER_FORMAT, raw)
        return cls(transmission_id,sequence_number,md5)

    def __str__(self):
        return super().__str__() + f"MD5 (hex): {self.md5}\n"

