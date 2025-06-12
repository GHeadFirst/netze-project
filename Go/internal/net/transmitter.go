package net

import (
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/udp_packets"
)

type TransmissionStats struct {
	Timestamp    string  `json:"timestamp"`
	File         string  `json:"file"`
	FileSize     int64   `json:"file_size"`
	Duration     float64 `json:"duration"`
	Throughput   float64 `json:"throughput"`
	TotalPackets int     `json:"total_packets"`
	AcksReceived int     `json:"acks_received"`
	Retries      int     `json:"retries"`
	SuccessRate  float64 `json:"success_rate"`
}

func Transmitter(filename string) {
	const numTransmissions = 10
	const maxRetries = 3
	const serverAddr = "0.0.0.0:4010" // Match Python receiver's address

	// Create results directory if it doesn't exist
	resultsDir := "results"
	if err := os.MkdirAll(resultsDir, 0755); err != nil {
		log.Fatal("Error creating results directory:", err)
	}

	// Open log file
	logFile, err := os.OpenFile(filepath.Join(resultsDir, "results-go-transmitter.txt"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal("Error opening log file:", err)
	}
	defer logFile.Close()

	fmt.Printf("\nStarting %d transmissions of %s\n", numTransmissions, filename)
	fmt.Println(strings.Repeat("=", 50))

	successfulTransmissions := 0
	for i := 0; i < numTransmissions; i++ {
		fmt.Printf("\nStarting transmission %d/%d\n", i+1, numTransmissions)

		// Get file info
		fileInfo, err := os.Stat(filename)
		if err != nil {
			log.Fatalf("Error getting file info: %v", err)
		}
		fileSize := fileInfo.Size()
		fmt.Printf("File size: %d bytes\n", fileSize)

		// Open file
		file, err := os.Open(filename)
		if err != nil {
			log.Fatalf("Error opening file: %v", err)
		}
		defer file.Close()

		// Create UDP connection
		conn, err := net.Dial("udp", serverAddr)
		if err != nil {
			log.Fatalf("Error creating UDP connection: %v", err)
		}
		defer conn.Close()

		// Set read timeout
		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		// Generate random sequence ID
		sequenceID := uint16(rand.Intn(65536))
		fmt.Printf("Starting transmission with sequence ID: %d\n", sequenceID)

		// Calculate total number of packets
		totalPackets := (fileSize + 1023) / 1024 // Round up division with 1023 because Go rounds down normally
		fmt.Printf("Total packets to send: %d\n", totalPackets)

		// Send first packet
		firstPacket := udp_packets.First_packet{
			Head: udp_packets.Header{
				Transmission_id: sequenceID,
				Sequence_number: 0,
			},
			Max_sequence_number: uint32(totalPackets),
			File_Name:           filename,
		}
		firstPacketBytes := BuildPacket(&firstPacket, [16]byte{})
		_, err = conn.Write(firstPacketBytes)
		if err != nil {
			log.Fatalf("Error sending first packet: %v", err)
		}

		// Send file in chunks
		buffer := make([]byte, 1024)
		sequenceNumber := uint32(1) // Start from 1 since 0 is first packet
		bytesSent := int64(0)
		startTime := time.Now()
		acksReceived := 0
		retries := 0
		success := true

		for {
			n, err := file.Read(buffer)
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Fatalf("Error reading file: %v", err)
			}

			// Create and send data packet
			dataPacket := udp_packets.Data_packet{
				Head: udp_packets.Header{
					Transmission_id: sequenceID,
					Sequence_number: sequenceNumber,
				},
				Data: buffer[:n],
			}

			packetBytes := BuildPacket(&dataPacket, [16]byte{})
			retryCount := 0
			for retryCount < maxRetries {
				_, err = conn.Write(packetBytes)
				if err != nil {
					log.Fatalf("Error sending packet: %v", err)
				}

				// Wait for ACK
				ackBuffer := make([]byte, 3) // ACK is 3 bytes ('ACK')
				_, err = conn.Read(ackBuffer)
				if err != nil {
					if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
						fmt.Printf("\nTimeout waiting for ACK for packet %d, retry %d/%d\n",
							sequenceNumber, retryCount+1, maxRetries)
						retryCount++
						retries++
						continue
					}
					log.Fatalf("Error receiving ACK: %v", err)
				}

				// Check if ACK is valid
				if string(ackBuffer) != "ACK" {
					fmt.Printf("\nUnexpected ACK received: %s, retry %d/%d\n",
						string(ackBuffer), retryCount+1, maxRetries)
					retryCount++
					retries++
					continue
				}

				acksReceived++
				break
			}

			if retryCount >= maxRetries {
				fmt.Printf("\nMax retries reached for packet %d, aborting transmission\n", sequenceNumber)
				success = false
				break
			}

			bytesSent += int64(n)
			progress := float64(bytesSent) / float64(fileSize) * 100
			elapsed := time.Since(startTime)
			speed := float64(bytesSent) / elapsed.Seconds() / 1024 / 1024 // MB/s

			fmt.Printf("\rProgress: %.2f%% (%d/%d packets) - Speed: %.2f MB/s",
				progress, sequenceNumber, totalPackets, speed)

			sequenceNumber++
		}

		if success {
			// Calculate MD5
			md5Sum := CalcMD5(filename)

			// Send last packet
			lastPacket := udp_packets.Last_packet{
				Head: udp_packets.Header{
					Transmission_id: sequenceID,
					Sequence_number: sequenceNumber,
				},
				MD5: md5Sum,
			}
			lastPacketBytes := BuildPacket(&lastPacket, md5Sum)
			_, err = conn.Write(lastPacketBytes)
			if err != nil {
				log.Fatalf("Error sending last packet: %v", err)
			}

			totalTime := time.Since(startTime)
			fmt.Printf("\n\nTransfer completed!\n")
			fmt.Printf("Total time: %.2f seconds\n", totalTime.Seconds())
			fmt.Printf("Average speed: %.2f MB/s\n", float64(fileSize)/totalTime.Seconds()/1024/1024)
			fmt.Printf("Total packets sent: %d\n", sequenceNumber+1)

			// Log statistics
			stats := TransmissionStats{
				Timestamp:    time.Now().Format(time.RFC3339),
				File:         filename,
				FileSize:     fileSize,
				Duration:     totalTime.Seconds(),
				Throughput:   float64(fileSize) / totalTime.Seconds(),
				TotalPackets: int(sequenceNumber + 1),
				AcksReceived: acksReceived,
				Retries:      retries,
				SuccessRate:  float64(acksReceived) / float64(sequenceNumber+1) * 100,
			}

			// Write to log file
			logEntry := fmt.Sprintf("\n%s\n", strings.Repeat("=", 50))
			logEntry += fmt.Sprintf("Transmission %d/%d at %s\n", i+1, numTransmissions, stats.Timestamp)
			logEntry += fmt.Sprintf("File: %s\n", stats.File)
			logEntry += fmt.Sprintf("File Size: %.2f KB\n", float64(stats.FileSize)/1024)
			logEntry += fmt.Sprintf("Duration: %.2f seconds\n", stats.Duration)
			logEntry += fmt.Sprintf("Throughput: %.2f KB/s\n", stats.Throughput/1024)
			logEntry += fmt.Sprintf("Total Packets: %d\n", stats.TotalPackets)
			logEntry += fmt.Sprintf("ACKs Received: %d\n", stats.AcksReceived)
			logEntry += fmt.Sprintf("Retries: %d\n", stats.Retries)
			logEntry += fmt.Sprintf("Success Rate: %.1f%%\n", stats.SuccessRate)
			logEntry += fmt.Sprintf("%s\n", strings.Repeat("=", 50))

			if _, err := logFile.WriteString(logEntry); err != nil {
				log.Fatal("Error writing to log file:", err)
			}

			successfulTransmissions++
		}

		fmt.Printf("\nCompleted transmission %d/%d\n", i+1, numTransmissions)
		fmt.Println(strings.Repeat("-", 50))
	}

	// Print summary
	fmt.Printf("\nTransmission Summary:\n")
	fmt.Printf("Total transmissions: %d\n", numTransmissions)
	fmt.Printf("Successful: %d\n", successfulTransmissions)
	fmt.Printf("Failed: %d\n", numTransmissions-successfulTransmissions)
	fmt.Printf("Success rate: %.1f%%\n", float64(successfulTransmissions)/float64(numTransmissions)*100)
	fmt.Printf("Results have been saved to results/results-go-transmitter.txt\n")
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

func create_header(id uint16, sequence uint32) udp_packets.Header {
	return udp_packets.Header{Transmission_id: id, Sequence_number: sequence}
}

func create_first_packet(head udp_packets.Header, max_sequence_number uint32, filename string) udp_packets.First_packet {
	return udp_packets.First_packet{Head: head, Max_sequence_number: max_sequence_number, File_Name: filename}
}

func create_data_packet(head udp_packets.Header, buf []byte) udp_packets.Data_packet {
	return udp_packets.Data_packet{Head: head, Data: buf}
}

func create_last_packet(head udp_packets.Header, md5_byte [16]byte) udp_packets.Last_packet {
	return udp_packets.Last_packet{Head: head, MD5: md5_byte}
}
