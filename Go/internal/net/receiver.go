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

func Receive() {
	var (
		file_name    string
		max_sequence uint32
		md5_old      []byte
		packet_list  = make(map[uint32]udp_packets.Packet) // map because received packets could be unsorted
		break_loop   bool
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
			// replace all zero bytes (\x00)
			raw := buf[10:n]
			clean := bytes.ReplaceAll(raw, []byte{0}, []byte{})
			file_name = string(clean)
			first := udp_packets.First_packet{
				Head:                head,
				Max_sequence_number: max_sequence,
				File_Name:           file_name,
			}
			packet_list[sequence] = &first
			fmt.Println("First packet received!")
		case max_sequence + 1:
			md5_old = buf[6:n]
			last := udp_packets.Last_packet{
				Head: head,
				MD5:  [16]byte(md5_old),
			}
			packet_list[sequence+1] = &last
			fmt.Println("Last packet received!")
			break_loop = true
		default:
			payload := make([]byte, n-6)
			copy(payload, buf[6:n])
			data := udp_packets.Data_packet{
				Head: head,
				Data: payload,
			}
			packet_list[sequence] = &data
			fmt.Println("Data packet received!")
		}
		fmt.Println("---------------------------")
		if break_loop {
			break
		}
	}
	new_file_name := "received_" + packet_list[0].(*udp_packets.First_packet).File_Name
	fmt.Printf("\nReceived file: %s\n", new_file_name)

	// create and fill the file with all the received data packets
	file, err := os.Create(new_file_name)
	if err != nil {
		log.Fatal("Pennercode kann die erhaltene Datei nicht erstellen!", err)
	}
	defer file.Close()

	n := uint32(1)
	for n <= max_sequence {
		_, err = file.Write(packet_list[n].(*udp_packets.Data_packet).Data)
		if err != nil {
			log.Fatal("Pennercode konnte nicht in die datei schreiben", err)
		}
		n++
	}

	md5_new := CalcMD5(new_file_name)
	if bytes.Equal(md5_old, md5_new[:]) {
		println("Same MD5!")
	} else {
		println("Different MD5")
	}
}
