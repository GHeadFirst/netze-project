package main

import (
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {
	// go routine to run the receiver simultanously with the transmitter
	go net.Receive()
	// enough time so the receiver can start
	time.Sleep(100 * time.Millisecond)
	// send data
	net.Transmission("./test_data_go.txt")
}
