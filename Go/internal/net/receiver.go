package net

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

func Receiver() {
	var (
		port string = "4010"

		file_name    string
		max_sequence uint32
		md5_old      []byte
		packet_list  = make(map[uint32]udp_packets.Packet) // map because received packets could be unsorted
	)

	addr, err := net.ResolveUDPAddr("udp", ":"+port)
	if err != nil {
		log.Fatal("Error: ", err)
	}
	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal("Receiver Error: ", err)
	}
	defer conn.Close()
	fmt.Println("UDP server is listening...")

	storePackets(packet_list, &file_name, &max_sequence, &md5_old, conn)

	// new name just to see a file, normally it wouldn't be needed
	new_file_name := "received_" + packet_list[0].(*udp_packets.First_packet).File_Name
	fmt.Printf("\nReceived file: %s\n", new_file_name)

	mergePackets(new_file_name, max_sequence, packet_list)

	// comparing md5
	if compareMD5(new_file_name, md5_old) {
		println("Same MD5!")
	} else {
		println("Different MD5!")
	}
}

func storePackets(packet_list map[uint32]udp_packets.Packet, file_name *string, max_sequence *uint32, md5_old *[]byte, conn *net.UDPConn) {
	var break_loop bool
	buf := make([]byte, 1024)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			log.Fatal("Error: ", err)
		}

		// receive header
		id := binary.BigEndian.Uint16(buf[0:2])
		sequence := binary.BigEndian.Uint32(buf[2:6])
		head := create_header(id, sequence)

		fmt.Println("---------------------------")
		fmt.Println("Sequence_ID: ", id)
		fmt.Println("Sequence_number: ", sequence)

		switch sequence {
		case 0:
			*max_sequence = binary.BigEndian.Uint32(buf[6:10])
			// replace all zero bytes (\x00)
			raw := buf[10:n]
			clean := bytes.ReplaceAll(raw, []byte{0}, []byte{})
			*file_name = string(clean)

			first := create_first_packet(head, *max_sequence, *file_name)
			packet_list[sequence] = &first
			fmt.Println("First packet received!")
		case *max_sequence + 1:
			*md5_old = buf[6:n]

			last := create_last_packet(head, [16]byte(*md5_old))
			packet_list[sequence+1] = &last
			fmt.Println("Last packet received!")
			break_loop = true
		default:
			payload := make([]byte, n-6)
			copy(payload, buf[6:n])

			data := create_data_packet(head, payload)
			packet_list[sequence] = &data
			fmt.Println("Data packet received!")
		}
		if break_loop {
			break
		}
	}
	fmt.Println("---------------------------")
}

func mergePackets(new_file_name string, max_sequence uint32, packet_list map[uint32]udp_packets.Packet) {
	// create and fill the file with all the received data packets
	file, err := os.Create(new_file_name)
	if err != nil {
		log.Fatal("Error: ", err)
	}
	defer file.Close()

	n := uint32(1)
	for n <= max_sequence {
		_, err = file.Write(packet_list[n].(*udp_packets.Data_packet).Data)
		if err != nil {
			log.Fatal("Error: ", err)
		}
		n++
	}
}
