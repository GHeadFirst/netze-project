package main

import (
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {

	go net.Receiver()

	time.Sleep(10 * time.Millisecond)
	net.Transmitter("picture.jpg")
}
