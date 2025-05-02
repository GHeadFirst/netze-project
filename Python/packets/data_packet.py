class DataPacket:
    def __init__(self, transmission_id: int, sequence_number: int, data: bytes) -> None: 
        self.transmission_id = transmission_id
        self.sequence_number = sequence_number
        self.data = data

    def get_transmission_id(self) -> int:
        return self.transmission_id
    
    def get_sequence_number(self) -> int:
        return self.sequence_number

    def get_data(self) -> bytes:
        return self.data
    