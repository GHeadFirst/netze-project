package udp_packets

type Packet interface {
	isPacket()
}

type Header struct {
	Transmission_id uint16
	Sequence_number uint32
}

type First_packet struct {
	Head                Header
	Max_sequence_number uint32
	File_Name           string
}

type Data_packet struct {
	Head Header
	Data []byte
}

type Last_packet struct {
	Head Header
	MD5  [16]byte
}

// "marker interface" just to group
func (p First_packet) isPacket() {}
func (p Data_packet) isPacket()  {}
func (p Last_packet) isPacket()  {}
