## Project Approach 🇬🇧

### Overview

We implement a file transfer system over UDP in two different programming languages. The system must transmit a file quickly and reliably without control messages from the receiver. File integrity is validated solely through MD5 checksum comparison after transfer.

### Packet Structure

Following the specification:

- **First Packet (SeqNr = 0):**
    
    - Transmission ID (16 bits)
        
    - Sequence Number (32 bits)
        
    - Max Sequence Number (32 bits)
        
    - File Name (8..2048 bytes)
        
- **Data Packets (SeqNr = 1 to MaxSeqNr-1):**
    
    - Transmission ID (16 bits)
        
    - Sequence Number (32 bits)
        
    - Data Payload (..)
        
- **Last Packet (SeqNr = MaxSeqNr):**
    
    - Transmission ID (16 bits)
        
    - Sequence Number (32 bits)
        
    - MD5 Hash (128 bits)
        

### Sender (TX) Flow

1. Read the file from disk.
    
2. Calculate MD5 checksum.
    
3. Split the file into packets according to the structure.
    
4. Assign:
    
    - A new **Transmission ID** for the entire file transfer.
        
    - **Sequence Numbers** strictly during file splitting.
        
5. Send packets via UDP **without guarantee of order**.
    

### Receiver (RX) Flow

1. Listen for incoming UDP packets.
    
2. For each packet:
    
    - Extract sequence number.
        
    - Store payload in a structured collection (Map: SeqNr → Payload).
        
    - If first packet (SeqNr = 0) is received, store metadata (File Name, MaxSeqNr).
        
3. After all packets are received:
    
    - Sort payloads by sequence number.
        
    - Reconstruct the file.
        
    - Verify file integrity by comparing the computed MD5 checksum with the received one.
        

### Important Considerations

- **Transmission ID must remain constant** across all packets of a single file.
    
- **UDP does not guarantee ordering** – our system must handle out-of-order arrivals.
    
- **Rounding up** is necessary when calculating the number of packets based on file size.
    
- **No control messages** are allowed between receiver and sender.

## Projektansatz 🇩🇪

### Übersicht

Wir implementieren ein Dateitransfersystem über UDP in zwei verschiedenen Programmiersprachen. Das System soll eine Datei schnell und zuverlässig übertragen, ohne Kontrollnachrichten vom Empfänger. Die Integrität der übertragenen Datei wird ausschließlich durch den Vergleich des MD5-Checksummenwerts nach der Übertragung sichergestellt.

### Paketstruktur

Gemäß der Spezifikation:

- **Erstes Paket (SeqNr = 0):**
    
    - Transmission ID (16 Bit)
        
    - Sequenznummer (32 Bit)
        
    - Maximale Sequenznummer (32 Bit)
        
    - Dateiname (8..2048 Bytes)
        
- **Datenpakete (SeqNr = 1 bis MaxSeqNr-1):**
    
    - Transmission ID (16 Bit)
        
    - Sequenznummer (32 Bit)
        
    - Nutzdaten (..)
        
- **Letztes Paket (SeqNr = MaxSeqNr):**
    
    - Transmission ID (16 Bit)
        
    - Sequenznummer (32 Bit)
        
    - MD5-Hash (128 Bit)
        

### Sender (TX) Ablauf

1. Datei vom Datenträger lesen.
    
2. MD5-Checksumme berechnen.
    
3. Datei gemäß der Paketstruktur aufteilen.
    
4. Zuweisung:
    
    - Eine neue **Transmission ID** für die gesamte Dateiübertragung.
        
    - **Sequenznummern** strikt während der Aufteilung vergeben.
        
5. Pakete per UDP senden, **ohne garantierte Reihenfolge**.
    

### Empfänger (RX) Ablauf

1. Auf eingehende UDP-Pakete lauschen.
    
2. Für jedes empfangene Paket:
    
    - Sequenznummer extrahieren.
        
    - Nutzdaten in einer strukturierten Sammlung speichern (Map: SeqNr → Payload).
        
    - Falls erstes Paket (SeqNr = 0) empfangen wird, Metadaten (Dateiname, MaxSeqNr) speichern.
        
3. Nach Empfang aller Pakete:
    
    - Nutzdaten nach Sequenznummer sortieren.
        
    - Datei rekonstruieren.
        
    - Datei-Integrität überprüfen, indem die berechnete MD5-Checksumme mit der empfangenen verglichen wird.
        

### Wichtige Überlegungen

- **Transmission ID muss über alle Pakete einer Datei hinweg konstant bleiben.**
    
- **UDP garantiert keine Reihenfolge** – unser System muss mit beliebiger Ankunftsreihenfolge umgehen können.
    
- **Aufrunden** ist notwendig, wenn die Anzahl der Pakete basierend auf der Dateigröße berechnet wird.
    
- **Keine Kontrollnachrichten** dürfen zwischen Sender und Empfänger verwendet werden.