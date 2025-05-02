package udp_packets

import (
	"fmt"
)

type packet interface {
	get_transmission_id()
	get_sequence_number()
}

type header struct {
	transmission_id int
	sequence_number int
}

type first_packet struct {
	header packet
	max_sequence_number int
}

type data_packet struct {
	header packet 
	data byte
}

type last_packet struct {
	header packet
	md5 string
}