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
