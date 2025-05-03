package net

import (
	"fmt"
	"log"
	"net"
)

func Receive() {

	addr, err := net.ResolveUDPAddr("udp", ":4010")
	if err != nil {
		log.Fatal("Pennercode ist scheiße")
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal("Session terminated your code is ASS!")
	}
	defer conn.Close()

	buf := make([]byte, 1024)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			log.Fatal("Fehler beim Lesen:", err)
		}
		fmt.Print(string(buf[6:n]))
	}
}
