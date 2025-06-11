package net

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

type ReceptionStats struct {
	Timestamp    string  `json:"timestamp"`
	File         string  `json:"file"`
	FileSize     int64   `json:"file_size"`
	Duration     float64 `json:"duration"`
	Throughput   float64 `json:"throughput"`
	TotalPackets int     `json:"total_packets"`
	AcksSent     int     `json:"acks_sent"`
	MD5Match     bool    `json:"md5_match"`
}

func Receiver() {
	const numTransmissions = 10
	var (
		port string = "4010"
		transmissionCount = 0
	)

	// Create results directory if it doesn't exist
	resultsDir := "results"
	if err := os.MkdirAll(resultsDir, 0755); err != nil {
		log.Fatal("Error creating results directory:", err)
	}

	// Open log file
	logFile, err := os.OpenFile(filepath.Join(resultsDir, "results-go-receiver.txt"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal("Error opening log file:", err)
	}
	defer logFile.Close()

	addr, err := net.ResolveUDPAddr("udp", ":"+port)
	if err != nil {
		log.Fatal("Error:", err)
	}
	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal("Receiver Error:", err)
	}
	defer conn.Close()
	fmt.Println("UDP server is listening...")
	fmt.Printf("Waiting for %d transmissions...\n", numTransmissions)
	fmt.Println(strings.Repeat("=", 50))

	for transmissionCount < numTransmissions {
		var (
			file_name    string
			max_sequence uint32
			md5_old      []byte
			packet_list  = make(map[uint32]udp_packets.Packet)
			startTime    = time.Now()
			acksSent     = 0
		)

		storePackets(packet_list, &file_name, &max_sequence, &md5_old, conn, &acksSent)

		// New name just to see a file
		new_file_name := "received_" + packet_list[0].(*udp_packets.First_packet).File_Name
		fmt.Printf("\nReceived file: %s\n", new_file_name)

		mergePackets(new_file_name, max_sequence, packet_list)

		// Get file info
		fileInfo, err := os.Stat(new_file_name)
		if err != nil {
			log.Fatal("Error getting file info:", err)
		}

		// Calculate duration and throughput
		duration := time.Since(startTime).Seconds()
		throughput := float64(fileInfo.Size()) / duration

		// Compare MD5
		md5Match := compareMD5(new_file_name, md5_old)

		// Log statistics
		stats := ReceptionStats{
			Timestamp:    time.Now().Format(time.RFC3339),
			File:         file_name,
			FileSize:     fileInfo.Size(),
			Duration:     duration,
			Throughput:   throughput,
			TotalPackets: len(packet_list),
			AcksSent:     acksSent,
			MD5Match:     md5Match,
		}

		// Write to log file
		logEntry := fmt.Sprintf("\n%s\n", strings.Repeat("=", 50))
		logEntry += fmt.Sprintf("Transmission %d/%d at %s\n", transmissionCount+1, numTransmissions, stats.Timestamp)
		logEntry += fmt.Sprintf("File: %s\n", stats.File)
		logEntry += fmt.Sprintf("File Size: %.2f KB\n", float64(stats.FileSize)/1024)
		logEntry += fmt.Sprintf("Duration: %.2f seconds\n", stats.Duration)
		logEntry += fmt.Sprintf("Throughput: %.2f KB/s\n", stats.Throughput/1024)
		logEntry += fmt.Sprintf("Total Packets: %d\n", stats.TotalPackets)
		logEntry += fmt.Sprintf("ACKs Sent: %d\n", stats.AcksSent)
		logEntry += fmt.Sprintf("MD5 Match: %v\n", stats.MD5Match)
		logEntry += fmt.Sprintf("%s\n", strings.Repeat("=", 50))

		if _, err := logFile.WriteString(logEntry); err != nil {
			log.Fatal("Error writing to log file:", err)
		}

		// Print statistics
		fmt.Printf("\nTransmission Statistics:\n")
		fmt.Printf("File: %s\n", stats.File)
		fmt.Printf("File Size: %.2f KB\n", float64(stats.FileSize)/1024)
		fmt.Printf("Duration: %.2f seconds\n", stats.Duration)
		fmt.Printf("Throughput: %.2f KB/s\n", stats.Throughput/1024)
		fmt.Printf("Total packets received: %d\n", stats.TotalPackets)
		fmt.Printf("Total ACKs sent: %d\n", stats.AcksSent)
		fmt.Printf("MD5 Match: %v\n", stats.MD5Match)

		transmissionCount++
		fmt.Printf("\nCompleted transmission %d/%d\n", transmissionCount, numTransmissions)
		fmt.Println(strings.Repeat("-", 50))
	}

	fmt.Printf("\nReceived all %d transmissions\n", numTransmissions)
	fmt.Printf("Results have been saved to results/results-go-receiver.txt\n")
}

func storePackets(packet_list map[uint32]udp_packets.Packet, file_name *string, max_sequence *uint32, md5_old *[]byte, conn *net.UDPConn, acksSent *int) {
	var break_loop bool
	buf := make([]byte, 5000)
	receivedPackets := make(map[uint32]bool) // Track received packets to avoid duplicates
	expectedPackets := 0
	lastPacketReceived := false

	for {
		n, addr, err := conn.ReadFromUDP(buf)
		if err != nil {
			log.Fatal("Error:", err)
		}

		// receive header
		id := binary.BigEndian.Uint16(buf[0:2])
		sequence := binary.BigEndian.Uint32(buf[2:6])
		head := create_header(id, sequence)

		// Send ACK for every packet
		_, err = conn.WriteToUDP([]byte("ACK"), addr)
		if err != nil {
			log.Fatal("Error sending ACK:", err)
		}
		*acksSent++

		// Skip if we've already received this packet
		if receivedPackets[sequence] {
			continue
		}

		fmt.Println("---------------------------")
		fmt.Println("Sequence_ID:", id)
		fmt.Println("Sequence_number:", sequence)

		// Mark packet as received
		receivedPackets[sequence] = true

		switch sequence {
		case 0:
			*max_sequence = binary.BigEndian.Uint32(buf[6:10])
			expectedPackets = int(*max_sequence) + 2 // +2 for first and last packets
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
			packet_list[sequence] = &last
			fmt.Println("Last packet received!")
			lastPacketReceived = true
		default:
			if sequence > *max_sequence {
				fmt.Printf("Warning: Received packet with sequence %d > max_sequence %d\n", sequence, *max_sequence)
				continue
			}
			payload := make([]byte, n-6)
			copy(payload, buf[6:n])

			data := create_data_packet(head, payload)
			packet_list[sequence] = &data
			fmt.Println("Data packet received!")
		}

		// Check if we have received all expected packets
		if lastPacketReceived && len(packet_list) == expectedPackets {
			fmt.Printf("\nReceived all %d expected packets\n", expectedPackets)
			break_loop = true
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
		log.Fatal("Error creating file:", err)
	}
	defer file.Close()

	// Write packets in order
	for n := uint32(1); n <= max_sequence; n++ {
		if packet, ok := packet_list[n]; ok {
			if dataPacket, ok := packet.(*udp_packets.Data_packet); ok {
				_, err = file.Write(dataPacket.Data)
				if err != nil {
					log.Fatal("Error writing to file:", err)
				}
			} else {
				log.Fatalf("Expected data packet at sequence %d, got %T", n, packet)
			}
		} else {
			log.Fatalf("Missing packet at sequence %d", n)
		}
	}
}
