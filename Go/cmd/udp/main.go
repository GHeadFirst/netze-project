package main

import (
	"flag"
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {
	var (
		send    string
		receive string
	)
	flag.StringVar(&send, "send", "", "Sender file")
	flag.StringVar(&receive, "receive", "", "Receiver file")

	if send == "send" {
		net.Transmitter("picture.jpg")

	}

	if receive == "receive" {
		net.Receiver()
	}

	time.Sleep(10 * time.Millisecond)
	//net.Transmitter("picture.jpg")
}
