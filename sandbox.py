data  = b"Hallo Welt"
data2 = "Hallo Welt"
a = 200

penner = a.to_bytes() + data
print(data.decode())         # b'Hallo Welt'
print(data2.encode())         # b'Hallo Welt'

print(a)
print(a.to_bytes())

print(penner)
print(penner.decode("utf-8", errors="replace"))