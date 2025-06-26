package net

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

// Receiver listens for UDP packets, reconstructs the file, verifies MD5, and reports duration & throughput
func Receiver() {
	var (
		port string = "4010"

		fileName    string
		maxSequence uint32
		md5Old      []byte
		packetList  = make(map[uint32]udp_packets.Packet)
	)

	addr, err := net.ResolveUDPAddr("udp", ":"+port)
	if err != nil {
		log.Fatal("Error resolving address: ", err)
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal("Receiver Error: ", err)
	}
	defer conn.Close()

	fmt.Println("UDP server is listening...")

	// start timing
	start := time.Now()

	// receive packets
	storePackets(packetList, &fileName, &maxSequence, &md5Old, conn)

	// reconstruct filename
	newFileName := "received_" + packetList[0].(*udp_packets.First_packet).File_Name
	fmt.Printf("\nReceived file: %s\n", newFileName)

	// write out data packets
	mergePackets(newFileName, maxSequence, packetList)

	// compare MD5 using md5.go's function
	if compareMD5(newFileName, md5Old) {
		fmt.Println("Same MD5!")
	} else {
		fmt.Println("Different MD5!")
	}

	// stop timing and report
	elapsed := time.Since(start).Seconds()
	info, err := os.Stat(newFileName)
	if err != nil {
		log.Printf("Could not stat file: %v", err)
		return
	}

	size := info.Size() // bytes
	kb := float64(size) / elapsed / 1024
	mbit := float64(size)*8.0 / elapsed / 1e6

	fmt.Printf("\n→ Duration: %.3f s\n", elapsed)
	fmt.Printf("→ Throughput: %.1f KB/s (%.2f Mbit/s)\n", kb, mbit)
}

func storePackets(packetList map[uint32]udp_packets.Packet, fileName *string, maxSequence *uint32, md5Old *[]byte, conn *net.UDPConn) {
	var breakLoop bool
	buf := make([]byte, 5000)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			log.Fatal("Error reading packet: ", err)
		}

		// parse header
		id := binary.BigEndian.Uint16(buf[0:2])
		sequence := binary.BigEndian.Uint32(buf[2:6])
		head := create_header(id, sequence)

		switch sequence {
		case 0:
			*maxSequence = binary.BigEndian.Uint32(buf[6:10])

			raw := buf[10:n]
			clean := bytes.ReplaceAll(raw, []byte{0}, []byte{})
			*fileName = string(clean)

			first := create_first_packet(head, *maxSequence, *fileName)
			packetList[sequence] = &first
			fmt.Println("First packet received!")

		case *maxSequence + 1:
			*md5Old = buf[6:n]

			last := create_last_packet(head, [16]byte(*md5Old))
			packetList[sequence+1] = &last
			fmt.Println("Last packet received!")
			breakLoop = true

		default:
			payload := make([]byte, n-6)
			copy(payload, buf[6:n])

			data := create_data_packet(head, payload)
			packetList[sequence] = &data
			fmt.Println("Data packet received!")
		}

		if breakLoop {
			break
		}
	}
	fmt.Println("---------------------------")
}

func mergePackets(newFileName string, maxSequence uint32, packetList map[uint32]udp_packets.Packet) {
	file, err := os.Create(newFileName)
	if err != nil {
		log.Fatal("Error creating file: ", err)
	}
	defer file.Close()

	for n := uint32(1); n <= maxSequence; n++ {
		_, err = file.Write(packetList[n].(*udp_packets.Data_packet).Data)
		if err != nil {
			log.Fatal("Error writing packet: ", err)
		}
	}
}
