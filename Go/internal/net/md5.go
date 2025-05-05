package net

import (
	"crypto/md5"
	"fmt"
	"os"
)

func CalcMD5(filename string) [16]byte {
	file_md5, _ := os.ReadFile(filename)
	fmt.Printf("Filesize: %d Bytes \n\n", len(file_md5)) // show how much bytes the file has
	return md5.Sum(file_md5)
}
