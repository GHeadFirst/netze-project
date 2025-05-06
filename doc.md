# UDP - Packetstruktur

```go
type Packet interface {
    isPacket()
}

type Header struct {
    Transmission_id uint16
    Sequence_number uint32
}

type First_packet struct {
    Head                Header
    Max_sequence_number uint32
    File_Name           string
}

type Data_packet struct {
    Head Header
    Data []byte
}

type Last_packet struct {
    Head Header
    MD5  [16]byte
}

// "marker interface" just to group
func (p First_packet) isPacket() {}
func (p Data_packet) isPacket()  {}
func (p Last_packet) isPacket()  {}
```

Damit die vorgegebene Struktur eingehalten werden kann wurden hier 3 type structs mit den entsprechenden Feldern (First_packet, Data_Packet, Last_Packet) erstellt. Dabei hat jedes Packet ein weiteres type struct Header in sich enthalten (Composition). Um die Packets in einer Datenstruktur (z.B.: einem slice) speichern zu können, wird ein Interface benötigt. Damit das in Go funktioniert muss dann jedes type struct alle Methoden des Interfaces Implementieren. In diesem Programm wird das Interface jedoch nur zum Gruppieren verwendet. Das nennt man auch Marker Interface. Das Interface hat nur eine Methode und die type structs implementieren diese. Die Methode hat keinen Inhalt und daher nur keine Funktion. 

```Go
func Transmitter(filename string) {
    const headerSize = 6
    const packetSize = 1024
    var (
        ip   string = "127.0.0.1"
        port string = "4010"
    )
    fmt.Println("File: ", filename)
    md5_byte := CalcMD5(filename)
    // udp connection
    conn, err := net.Dial("udp", ip+":"+port)
    if err != nil {
        log.Fatal("Error: ", err)
    }
    defer conn.Close()

    packet_list, sequence := storePacketsIntoArray(filename, packetSize-
												   headerSize, md5_byte)

    // fixup the max_sequence value in the first packet
    packet_list[0].(*udp_packets.First_packet).Max_sequence_number = sequence - 1
    
    // sending part
    fmt.Println("Sending file...")
    for _, pkt := range packet_list {
        packet := BuildPacket(pkt, md5_byte)
        _, err := conn.Write(packet)
        if err != nil {
            log.Fatal("Error: ", err)
        }
        time.Sleep(5 * time.Millisecond) // timer to avoid that some packet are
								         // not being send due to packetqueue
    }
}
```

Die Transmitterfunktion dient dazu um die Datei zu schicken. Der Ablauf der Funktion wie folgt ab: 
1. MD5 von der Datei berechnen
2. UDP-Verbindung herstellen
3. Packets in einem slice speichern
4. Senden der einzelnen Packets 

Der MD5-Wert wird aus den aus den Bytes der zu sendenden Datei berechnet und so erhält man einen 16 Byte langen Hashwert. Damit dieser berechnet wird, wird folgende Funktion aufgerufen:

```Go
func CalcMD5(filename string) [16]byte {
    file_md5, _ := os.ReadFile(filename)
    fmt.Printf("Filesize: %d Bytes \n\n", len(file_md5)) // show how much bytes
														 //the file has
	return md5.Sum(file_md5)
}
```

Diese Funktion berechnet mithilfe der Library `crypto/md5` den MD5 und gibt diesen als 16 Byte array zurück.

Danach wird mithilfe von der Dial Funktion aus der `net` Library eine UDP-Verbindung hergestellt. In diesem Fall werden die IP-Adresse vom localhost und der port 4010 verwendet, um das Programm direkt auf dem Laptop testen zu können. Mit `defer conn.Close()` wird sichergestellt das die Verbindung geschlossen wird sobald das Programm endet.

Sobald die Verbindung da ist werden die Packets in einem Slice gespeichert. Damit das funktioniert wird die Funktion `storePacketsIntoArray` aufgerufen die, die fertige Packet Sammlung und die Sequenz zurückgibt.

```Go
func storePacketsIntoArray(filename string, dataSize int, md5_byte [16]byte)([]udp_packets.Packet, uint32) {

    var (
        id          uint16 = uint16(rand.Intn(65536)) // random 16 bit integer
        sequence    uint32 = 0
        packet_list []udp_packets.Packet
    )
    //open
    file, err := os.Open(filename)
    if err != nil {
        log.Fatal("Error: ", err)
    }
    // store first packet
    firsthead := create_header(id, sequence)
    first := create_first_packet(firsthead, 0, filename) // zero at first because
									 // the max is not known yet --> fixup needed
    packet_list = append(packet_list, &first)

    // storing all data_packets into an array called packet_list

    for {
        sequence++
        buf := make([]byte, dataSize)
        // read
        count, err := file.Read(buf)
        if err != nil && err != io.EOF {
            log.Fatal("Error: ", err)
        }
        // if nothing was read, break
        if count == 0 {
            break
        }
        // everytime a new header with a new sequencenumber but same id
        head := create_header(id, sequence)
        data_packet := create_data_packet(head, buf[:count])
        packet_list = append(packet_list, &data_packet)
    }

    // store last packet
    lasthead := create_header(id, sequence)
    last := create_last_packet(lasthead, md5_byte)
    packet_list = append(packet_list, &last)
  
    return packet_list, sequence
}
```

Es wird eine randomisierte ID vergeben die für alle Packets gleich sind. Die Sequenznummer wird mit 0 initialisiert und dann hochgezählt mit jedem Schleifendurchlauf. Mit der Funktion create_header wird gleich der erste header für das First_Packet erstellt. Dieser Header wird gleich der nächsten Funktion `create_first_packet` übergeben. Das erste Packet ist somit erstellt und gleich an erster Stelle vom Slice eingefügt. 

```Go
func create_header(id uint16, sequence uint32) udp_packets.Header {
    return udp_packets.Header{Transmission_id: id, Sequence_number: sequence}
}

func create_first_packet(head udp_packets.Header, max_sequence_number uint32,
						filename string) udp_packets.First_packet {

    return udp_packets.First_packet{Head: head, Max_sequence_number:
								    max_sequence_number, File_Name: filename}
}
```

Wichtig ist hier das der Funktion `create_first_packet` die `max_sequence_number` mit der Zahl 0 übergeben wird, denn am Anfang ist die maximale Sequenz noch nicht bekannt und muss nach dem letzten Packet nachträglich mit der richtigen Zahl überschrieben werden. Das Data_Packet wird auf gleicher Weise wie das First_Packet in das Slice gespeichert mit jedoch einen paar kleinen Unterschieden. In jedem Schleifendurchlauf werden weitere bytes der Datei gelesen und in einen buffer gespeichert. Diese bytes werden dann als payload im Data_packet gespeichert und anschließend in das Packet slice eingefügt. 

```Go
func create_data_packet(head udp_packets.Header, buf []byte)
						udp_packets.Data_packet {
    return udp_packets.Data_packet{Head: head, Data: buf}
}
```

`count` ist die Variable die sagt wie viel Bytes in der Datei gelesen wurde. Wenn diese irgendwann den Wert 0 erreicht dann heißt es das keine weiteren Daten mehr in der Datei zu lesen sind. `buf[:count]` wird hier als ein Parameter übergeben in der Funktion `create_data_packet` und dient dazu das die Packets nicht mit unnötigen null-bytes aufgefüllt werden. Das verfälscht sonst den MD5 Wert der von receiver berechnet wird. Anschließend wenn alle Data_Packets befüllt wurden muss die max_sequence_number mit der richtigen Nummer überschrieben werden. Dazu nimmt man das erste Element vom Slice und nimmt den konkreten Typ mittels Type-Assertion. Die Maximal Sequenz ist hier `sequence - 1` da das Last_Packet nicht dazu gezählt wird. Die Sequenznummer wäre bei Last_Packet `sequence + 1`.

Jetzt kommt der eigentliche Teil des Transmitters. Das ist das versenden der Packets. Mit einer Schleife und der Funktion `conn.Write` werden die einzelnen Packets bei jedem Schleifendurchlauf an den receiver versendet. Bevor aber `conn.Write` die Daten versenden kann müssen die Daten aus den Packets in Byte umgeformt werden und das geschieht mit der Funktion. 

```Go
func BuildPacket(x udp_packets.Packet, md5_byte [16]byte) []byte {
    var packet []byte

    switch pkt := x.(type) {

    case *udp_packets.First_packet:
        var transmission_byte [2]byte
        var sequence_byte [4]byte
        var max_sequence_byte [4]byte
        var file_name_byte [256]byte

        binary.BigEndian.PutUint16(transmission_byte[:],
							       uint16(pkt.Head.Transmission_id))
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

        binary.BigEndian.PutUint16(transmission_byte[:],
							       uint16(pkt.Head.Transmission_id))
        binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

        packet = append(packet, transmission_byte[:]...)
        packet = append(packet, sequence_byte[:]...)
        packet = append(packet, pkt.Data...)

    case *udp_packets.Last_packet:
        var transmission_byte [2]byte
        var sequence_byte [4]byte
        //md5 is already in [16]byte
        
        binary.BigEndian.PutUint16(transmission_byte[:],
							        uint16(pkt.Head.Transmission_id))
        binary.BigEndian.PutUint32(sequence_byte[:], pkt.Head.Sequence_number)

        packet = append(packet, transmission_byte[:]...)
        packet = append(packet, sequence_byte[:]...)
        packet = append(packet, md5_byte[:]...)
    }
    return packet
}
```

Da in dem Slice `packet_list` unterschiedliche Typen sind muss man die mithilfe einer switch-case unterscheiden. Das Prinzip ist in allen drei cases das Gleiche. Zuerst werden die Variablen Deklariert als Byte-Arrays mit den jeweiligen Byte-größen. Danach werden alle Felder von jedem Packet in Byte-Arrays umgewandelt. Anschließend werden alle dabei entstanden Byte-Arrays von den Feldern in das Slice packet gespeichert. Das Zeichen `[:]` bedeutet das aus einem Array temporär ein Slice gemacht wird, um dann das Array an das Slice packet anhängen zu können. Am Ende wird das packet als Byte-Array zurückgegeben. Damit auch alle Packets ankommen können und keine unnötige Warteschlangen entstehen, wird `time.Sleep` verwendet um eine kleine Pause zwischen dem verschicken einzulegen.


# UDP - Receiver

```Go
func Receiver() {
    var (
        port string = "4010"
        file_name    string
        max_sequence uint32
        md5_old      []byte
        packet_list  = make(map[uint32]udp_packets.Packet) // map because received
												        //packets could be unsorted
		)

    addr, err := net.ResolveUDPAddr("udp", ":"+port)
    if err != nil {
        log.Fatal("Error: ", err)
    }
    conn, err := net.ListenUDP("udp", addr)
    if err != nil {
        log.Fatal("Receiver Error: ", err)
    }
    defer conn.Close()
    fmt.Println("UDP server is listening...")
    
    storePackets(packet_list, &file_name, &max_sequence, &md5_old, conn)

    // new name just to see a file, normally it wouldn't be needed
    new_file_name := "received_" + packet_list[0]
					(*udp_packets.First_packet).File_Name

    fmt.Printf("\nReceived file: %s\n", new_file_name)

    mergePackets(new_file_name, max_sequence, packet_list)

    // comparing md5
    if compareMD5(new_file_name, md5_old) {
        println("Same MD5!")
    } else {
        println("Different MD5!")
    }
}
```

Der Receiver besteht aus folgenden Schritten:
1. Eine Verbindung mit UDP herstellen 
2. Angekommene Packets in einer Hashmap speichern
3. Packets wieder zu einer Datei zusammenfügen
4. Neuen MD5-Wert ermitteln und mit dem erhaltenen vergleichen

Mit `net.ResolveUDPAddr("udp", ":"+port)` wird auf alle Interfaces auf port 4010 gehört. `net.ListenUDP("udp", addr)` öffnet ein UDP-Socket das auf der angegebenen Adresse auf eingehende Packets lauscht.

Die Funktion `storePackets` speichert die packets dann wieder in die vorherige Struktur zurück mit Ausnahme das hier eine Map verwendet wird statt einem Array. Es kann nämlich sein das die Packets durcheinander sein können in der Datenstruktur beim Ankommen. conn.ReadFromUDP liest das Packet und speichert das packet in einem buffer mit der Größe 1024 Byte. Dann wird der Header vom Packet zurück in ursprünglichen Typen gebracht.
```Go
func storePackets(packet_list map[uint32]udp_packets.Packet, file_name *string,
				  max_sequence *uint32, md5_old *[]byte, conn *net.UDPConn) {
    var break_loop bool
    buf := make([]byte, 1024)

    for {
        n, _, err := conn.ReadFromUDP(buf)
        if err != nil {
            log.Fatal("Error: ", err)
        }

        // receive header
        id := binary.BigEndian.Uint16(buf[0:2])
        sequence := binary.BigEndian.Uint32(buf[2:6])
        head := create_header(id, sequence)

        fmt.Println("---------------------------")
        fmt.Println("Sequence_ID: ", id)
        fmt.Println("Sequence_number: ", sequence)

        switch sequence {

        case 0:
            *max_sequence = binary.BigEndian.Uint32(buf[6:10])
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
            packet_list[sequence+1] = &last
            fmt.Println("Last packet received!")
            break_loop = true

        default:
            payload := make([]byte, n-6)
            copy(payload, buf[6:n])

            data := create_data_packet(head, payload)
            packet_list[sequence] = &data
            fmt.Println("Data packet received!")
        }

        if break_loop {
            break
        }
    }
    fmt.Println("---------------------------")
}
```