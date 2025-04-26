# 🇩🇪 German
# PS Netze und Verteilte Systeme (NVS) SS 2025

## **Programmierprojekt, bis Do 8.5.2025**

**EINE Präsentation der 4-er Gruppe als PDF mit passendem Dateinamen bitte bis zum Vorabend 18 Uhr per e-mail _von Ihrem Uni-Mail-Account_ senden an [bernhard.collini-nocker@plus.ac.at](mailto:bernhard.collini-nocker@plus.ac.at) mit Betreff: [NVS25] PP1**

---

## **Programmierprojekt in 4-er Teams: Präsentation v1**

Programmieren Sie ein Transmit-(TX) und Receive-(RX) Programm in jeweils zwei verschiedenen Programmiersprachen, das mittels UDP eine Datei zwischen den vier Kombinationen schnellstens und fehlerfrei übertragen kann.  
Verwenden Sie dafür folgende Paketstruktur:

```
Packet SeqNr = 1 bis MaxSeqNr {
    Transmission ID (16),
    Sequence Number (32),
    Data (..)
}

first Packet SeqNr = 0 {
    Transmission ID (16),
    Sequence Number (32),
    Max Sequence Number (32),
    File Name (8..2048)
}

last Packet {
    Transmission ID (16),
    Sequence Number (32),
    MD5 (128)
}
```

> In der ersten Version sollen **KEINE** Kontrollnachrichten von RX zu TX verwendet werden!  
> Die Fehlerfreiheit soll nur mittels **MD5** sichergestellt werden.

---

**Präsentieren Sie die Implementierung TX/RX in zwei Programmiersprachen, und die Messergebnisse (je 10 zwischen den Kombinationen) im Hinblick auf Optimierung Durchsatz.**

# 🇬🇧 English

# PS Networks and Distributed Systems (NVS) SS 2025

## **Programming Project, due Thu 8 May 2025**

**ONE presentation from the group of four, as a PDF with an appropriate filename, must be sent by email _from your university email account_ to [bernhard.collini-nocker@plus.ac.at](mailto:bernhard.collini-nocker@plus.ac.at) by 6 PM the evening before, with the subject: [NVS25] PP1**

---

## **Programming Project in Teams of Four: Presentation v1**

Program a Transmit (TX) and a Receive (RX) program, each in two different programming languages, that can transfer a file between the four possible combinations as quickly and error-free as possible using UDP.  
Use the following packet structure:

```
Packet SeqNr = 1 to MaxSeqNr {
    Transmission ID (16),
    Sequence Number (32),
    Data (..)
}

First Packet SeqNr = 0 {
    Transmission ID (16),
    Sequence Number (32),
    Max Sequence Number (32),
    File Name (8..2048)
}

Last Packet {
    Transmission ID (16),
    Sequence Number (32),
    MD5 (128)
}
```

> In the first version, **NO** control messages from RX to TX should be used!  
> Error-free transmission must be ensured **only** using **MD5**.

---

**Present the TX/RX implementation in two different programming languages, along with the measurement results (10 per combination) focusing on throughput optimization.**

