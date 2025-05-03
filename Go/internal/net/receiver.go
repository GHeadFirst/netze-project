package net

import (
	"log"
	"net"
)

func receive() (int, string, int, float32) {

	conn, err := net.Dial("udp", "127.0.0.1:4010")
	if err != nil {
		log.Fatal("Pennercode endet hier!")
	}

	defer conn.Close()

}
