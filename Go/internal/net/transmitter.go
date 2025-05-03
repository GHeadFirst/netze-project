package net

import (
	"crypto/md5"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

func Transmission(filename string) {

	const headerSize = 6
	const packetSize = 1024

	var (
		sequence    uint32 = 0
		packet_list []udp_packets.Packet
		id          string = "bu"

		count int = 0 // counts if theres any information left to read in the file

		packet  []byte = make([]byte, packetSize)
		header  []byte = make([]byte, headerSize)
		payload []byte = make([]byte, len(packet)-len(header))
	)
	// MD5 berechnen
	file_md5, _ := os.ReadFile(filename)
	md5_byte := md5.Sum(file_md5)

	//open
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal("Pennercode kann die Datei nicht öffnen!", err)
	}

	// udp
	conn, err := net.Dial("udp", "127.0.0.1:4010")
	if err != nil {
		log.Fatal("Pennercode hat nicht geschafft sich zu verbinden!", err)
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
			log.Fatal("Pennercode kann nicht die Datei lesen", err)
		}
		// if nothing was read, break
		if count == 0 {
			break
		}
		fmt.Println("payload len:", len(payload))
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
		payload = nil
	}

	// store last packet
	lasthead := udp_packets.Header{
		Transmission_id: id,
		Sequence_number: sequence,
	}
	last := udp_packets.Last_packet{
		Head: lasthead,
		MD5:  md5_byte,
	}
	packet_list = append(packet_list, &last)

	// fixup the max_sequence value in the first packet
	fixup_sequence := packet_list[0].(*udp_packets.First_packet)
	fixup_sequence.Max_sequence_number = sequence - 1

	// sending part
	for _, x := range packet_list {
		header = nil
		payload = nil
		packet = nil

		switch pkt := x.(type) {

		case *udp_packets.First_packet:
			var transmission_byte [2]byte
			var sequence_byte [4]byte
			var max_sequence_byte [32]byte
			var file_name_byte [256]byte

			copy(transmission_byte[:], []byte(pkt.Head.Transmission_id))
			binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)
			binary.BigEndian.PutUint32(max_sequence_byte[:], pkt.Max_sequence_number)
			copy(file_name_byte[:], []byte(pkt.File_Name))

			header = append(header, transmission_byte[:]...)
			header = append(header, sequence_byte[:]...)
			payload = append(payload, max_sequence_byte[:]...)
			payload = append(payload, file_name_byte[:]...)
			packet = append(packet, header...)
			packet = append(packet, payload...)

		case *udp_packets.Data_packet:
			var transmission_byte [2]byte
			var sequence_byte [4]byte
			// data is already in bytes

			copy(transmission_byte[:], []byte(pkt.Head.Transmission_id))
			binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

			header = append(header, transmission_byte[:]...)
			header = append(header, sequence_byte[:]...)
			payload = append(payload, pkt.Data...)
			packet = append(packet, header...)
			packet = append(packet, payload...)

		case *udp_packets.Last_packet:
			var transmission_byte [2]byte
			var sequence_byte [4]byte
			//md5 is already in [16]byte

			copy(transmission_byte[:], []byte(pkt.Head.Transmission_id))
			binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

			header = append(header, transmission_byte[:]...)
			header = append(header, sequence_byte[:]...)
			payload = append(payload, md5_byte[:]...)
			packet = append(packet, header...)
			packet = append(packet, payload...)
		}
		_, err := conn.Write(packet)
		if err != nil {
			log.Fatal("Pennercode hat es nicht geschafft das packet zu senden!", err)
		}
	}
}
