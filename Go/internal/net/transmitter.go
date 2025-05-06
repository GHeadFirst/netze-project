package net

import (
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net"
	"os"
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

func Transmitter(filename string) {

	const headerSize = 6
	const packetSize = 1024

	var (
		ip   string = "127.0.0.1"
		port string = "4010"
	)
	fmt.Println("File: ", filename)
	md5_byte := CalcMD5(filename)

	// udp connection
	conn, err := net.Dial("udp", ip+":"+port)
	if err != nil {
		log.Fatal("Error: ", err)
	}
	defer conn.Close()

	packet_list, sequence := storePacketsIntoArray(filename, packetSize-headerSize, md5_byte)

	// fixup the max_sequence value in the first packet
	packet_list[0].(*udp_packets.First_packet).Max_sequence_number = sequence - 1

	// sending part
	fmt.Println("Sending file...")
	for _, pkt := range packet_list {
		packet := BuildPacket(pkt, md5_byte)
		_, err := conn.Write(packet)
		if err != nil {
			log.Fatal("Error: ", err)
		}
		time.Sleep(5 * time.Millisecond) // timer to avoid that some packet are not being send due to packetqueue
	}
}

func BuildPacket(x udp_packets.Packet, md5_byte [16]byte) []byte {
	var packet []byte

	switch pkt := x.(type) {

	case *udp_packets.First_packet:
		var transmission_byte [2]byte
		var sequence_byte [4]byte
		var max_sequence_byte [4]byte
		var file_name_byte [256]byte

		binary.BigEndian.PutUint16(transmission_byte[:], uint16(pkt.Head.Transmission_id))
		binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)
		binary.BigEndian.PutUint32(max_sequence_byte[:], pkt.Max_sequence_number)
		copy(file_name_byte[:], []byte(pkt.File_Name))

		packet = append(packet, transmission_byte[:]...)
		packet = append(packet, sequence_byte[:]...)
		packet = append(packet, max_sequence_byte[:]...)
		packet = append(packet, file_name_byte[:]...)

	case *udp_packets.Data_packet:
		var transmission_byte [2]byte
		var sequence_byte [4]byte
		// data is already in bytes

		binary.BigEndian.PutUint16(transmission_byte[:], uint16(pkt.Head.Transmission_id))
		binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

		packet = append(packet, transmission_byte[:]...)
		packet = append(packet, sequence_byte[:]...)
		packet = append(packet, pkt.Data...)

	case *udp_packets.Last_packet:
		var transmission_byte [2]byte
		var sequence_byte [4]byte
		//md5 is already in [16]byte

		binary.BigEndian.PutUint16(transmission_byte[:], uint16(pkt.Head.Transmission_id))
		binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

		packet = append(packet, transmission_byte[:]...)
		packet = append(packet, sequence_byte[:]...)
		packet = append(packet, md5_byte[:]...)
	}

	return packet
}

func storePacketsIntoArray(filename string, dataSize int, md5_byte [16]byte) ([]udp_packets.Packet, uint32) {
	var (
		id          uint16 = uint16(rand.Intn(65536)) // random 16 bit integer
		sequence    uint32 = 0
		packet_list []udp_packets.Packet
	)

	//open
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal("Error: ", err)
	}

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
		buf := make([]byte, dataSize)
		// read
		count, err := file.Read(buf)
		if err != nil && err != io.EOF {
			log.Fatal("Error: ", err)
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
			Data: buf[:count], // only store the real bytes, so there is no unnecessery zero bytes in the last data packet
		}
		packet_list = append(packet_list, &data_packet)
		// payload = nil
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

	return packet_list, sequence
}
