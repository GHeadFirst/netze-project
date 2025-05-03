package udp_packets

type Packet interface {
	isPacket()
}

type Header struct {
	Transmission_id string
	Sequence_number int
}

type First_packet struct {
	Head                Header
	Max_sequence_number int
	File_Name           string
}

type Data_packet struct {
	Head Header
	Data []byte
}

type Last_packet struct {
	Head Header
	MD5  string
}

// "marker interface" just to group
func (p First_packet) isPacket() {}
func (p Data_packet) isPacket()  {}
func (p Last_packet) isPacket()  {}
