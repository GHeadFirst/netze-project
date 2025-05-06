package net

import (
	"bytes"
	"crypto/md5"
	"fmt"
	"os"
)

func CalcMD5(filename string) [16]byte {
	file_md5, _ := os.ReadFile(filename)
	fmt.Printf("Filesize: %d Bytes \n\n", len(file_md5)) // show how much bytes the file has
	return md5.Sum(file_md5)
}

func compareMD5(new_file_name string, md5_old []byte) bool {
	md5_new := CalcMD5(new_file_name)
	md5_old_string := fmt.Sprintf("%x", md5_old)
	md5_new_string := fmt.Sprintf("%x", md5_new)

	fmt.Println("MD5 before: ", md5_new_string)
	fmt.Println("MD5 after:  ", md5_old_string)
	fmt.Println("---------------------------------------------")

	return bytes.Equal(md5_old, md5_new[:])
}
