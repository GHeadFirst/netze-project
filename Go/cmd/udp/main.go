package main

import (
	"flag"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {
	var (
		send    bool
		receive bool
	)
	flag.BoolVar(&send, "send", false, "Sender file")
	flag.BoolVar(&receive, "receive", false, "Receiver file")
	flag.Parse()

	if send {
		net.Transmitter("picture.jpg")
	}

	if receive {
		net.Receiver()
	}
}
