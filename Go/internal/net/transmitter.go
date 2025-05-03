package net

import (
	"crypto/md5"
	"log"
	"net"
	"os"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

func Transmission(filename string) {
	const packetSize = 1024
	const headerSize = 6

	var (
		sequence    int = 0
		packet_list []udp_packets.Packet
		id          string = "randomnumber"

		count int = 0 // counts if theres any information left to read in the file

		packet  []byte = make([]byte, packetSize)
		header  []byte = make([]byte, headerSize)
		payload []byte = make([]byte, len(packet)-len(header))
	)
	// MD5 berechnen
	file_md5, err := os.ReadFile(filename)
	md5 := md5.Sum(file_md5)

	//open
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal("Pennercode kann die Datei nicht öffnen!")
	}

	// udp
	conn, err := net.Dial("udp", "127.0.0.1:4010")
	if err != nil {
		log.Fatal("Pennercode hat nicht geschafft sich zu verbinden!")
	}
	defer conn.Close()

	// store first packet
	firsthead := udp_packets.Header{
		Transmission_id: id,
		Sequence_number: sequence,
	}
	first := udp_packets.First_packet{
		Head:                firsthead,
		Max_sequence_number: 0, // zero at first because the max is not known yet --> fixup needed
		File_Name:           filename,
	}
	packet_list = append(packet_list, &first)

	// storing all data_packets into an array called packet_list
	for {
		sequence++
		// read
		count, err = file.Read(payload)
		if err != nil {
			log.Fatal("Pennercode kann nicht die Datei lesen")
		}
		// if nothing was read, break
		if count == 0 {
			break
		}
		// everytime a new header with a new sequencenumber but same id
		head := udp_packets.Header{
			Transmission_id: id,
			Sequence_number: sequence,
		}
		data_packet := udp_packets.Data_packet{
			Head: head,
			Data: payload,
		}
		packet_list = append(packet_list, &data_packet)
	}

	// store last packet
	lasthead := udp_packets.Header{
		Transmission_id: id,
		Sequence_number: sequence,
	}
	last := udp_packets.Last_packet{
		Head: lasthead,
		MD5:  md5[:], // [:] means converting an array to a slice
	}
	packet_list = append(packet_list, &last)

	// fixup the max_sequence value in the first packet
	fixup_sequence := packet_list[0].(*udp_packets.First_packet)
	fixup_sequence.Max_sequence_number = sequence - 1
}
