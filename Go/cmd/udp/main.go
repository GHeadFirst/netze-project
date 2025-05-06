package main

import (
	"time"

	"github.com/GHeadFirst/netze-project/Go/internal/net"
)

func main() {

	net.Receiver()

	time.Sleep(10 * time.Millisecond)
	//net.Transmitter("picture.jpg")
}
