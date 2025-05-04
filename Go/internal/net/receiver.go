package net

import (
	"encoding/binary"
	"fmt"
	"log"
	"net"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

func Receive() {
	var (
		file_name    string
		max_sequence uint32
		payload      []byte
		md5_re       []byte
	)

	addr, err := net.ResolveUDPAddr("udp", ":4010")
	if err != nil {
		log.Fatal("Pennercode ist scheiße")
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal("Session terminated your code is ASS!")
	}
	defer conn.Close()

	buf := make([]byte, 1024)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			log.Fatal("Fehler beim Lesen:", err)
		}

		if n == 0 {
			break
		}

		id := binary.BigEndian.Uint16(buf[0:2])
		sequence := binary.BigEndian.Uint32(buf[2:6])
		head := udp_packets.Header{
			Transmission_id: id,
			Sequence_number: sequence,
		}
		fmt.Println("Sequence_ID: ", id)
		fmt.Println("Sequence_number: ", sequence)

		switch sequence {
		case 0:
			max_sequence = binary.BigEndian.Uint32(buf[6:10])
			file_name = string(buf[10:n])
			first := udp_packets.First_packet{
				Head:                head,
				Max_sequence_number: max_sequence,
				File_Name:           file_name,
			}
			fmt.Println(first)
		case max_sequence + 1:
			md5_re = buf[6:n]
			last := udp_packets.Last_packet{
				Head: head,
				MD5:  [16]byte(md5_re),
			}
			fmt.Println(last)
		default:
			payload = buf[6:n]
			data := udp_packets.Data_packet{
				Head: head,
				Data: payload,
			}
			fmt.Println(data)
		}
		fmt.Println("---------------------------")
	}
}
