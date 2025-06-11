package main

import (
	"fmt"
	"os"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage:")
		fmt.Println("  For receiver: go run cmd/udp/main.go receiver")
		fmt.Println("  For transmitter: go run cmd/udp/main.go transmitter <filename>")
		os.Exit(1)
	}

	command := os.Args[1]

	switch command {
	case "receiver":
		fmt.Println("Starting receiver...")
		net.Receiver()
	case "transmitter":
		if len(os.Args) < 3 {
			fmt.Println("Error: transmitter requires a filename")
			fmt.Println("Usage: go run cmd/udp/main.go transmitter <filename>")
			os.Exit(1)
		}
		filename := os.Args[2]
		fmt.Println("Starting transmitter...")
		net.Transmitter(filename)
	default:
		fmt.Printf("Unknown command: %s\n", command)
		fmt.Println("Usage:")
		fmt.Println("  For receiver: go run cmd/udp/main.go receiver")
		fmt.Println("  For transmitter: go run cmd/udp/main.go transmitter <filename>")
		os.Exit(1)
	}
}
