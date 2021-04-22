
def handle_TCP_header(bytes_data):
    binary_data = bin(int.from_bytes(bytes_data,byteorder='big'))[2:]
    
    def read_bytes(x,a,b):
        return int(x[a:b],2)
    extend_payload_len = 0
    payload_len = read_bytes(binary_data,9,16)
    if payload_len == 126:
        payload_len = read_bytes(binary_data,16,32)
        extend_payload_len = 16
    print("payload len " + str(payload_len))

    one = read_bytes(binary_data,16+extend_payload_len,24+extend_payload_len)
    two = read_bytes(binary_data,24+extend_payload_len,32+extend_payload_len)
    three = read_bytes(binary_data,32+extend_payload_len,40+extend_payload_len)
    four = read_bytes(binary_data,40+extend_payload_len,48+extend_payload_len)

    for i in range(0,int(payload_len)):
        mask = 9999
        # print("mask bit is " + str(i%8))
        if i == 0:
            mask = one
        elif int(i % 4) == 0:
            mask = one
        elif int(i % 4) == 1:
            mask = two
        elif int(i % 4) == 2:
            mask = three
        elif int(i % 4) == 3:
            mask = four
        print("mask key " + str(mask))
        if i == 0:
            data = int(binary_data[48 + i * 8 + extend_payload_len : 48 + i * 8 + 8 + extend_payload_len],2)^mask
        else : 
            data = (data << 8) + int(binary_data[48 + i * 8 + extend_payload_len: 48 + i * 8 + 8 + extend_payload_len],2)^mask
    print("bin data " + bin(data))
    print(data.to_bytes(length=34, byteorder='big').decode())
    # head_content_length = len(bytes_data) - (2 + payload_len/8 + 32/8)
    # return [payload_len,head_content_length,one,two,three,four]
    return data.to_bytes(length=34, byteorder='big')

length = "00000000000000000000000000000000000000000000000"
a = b'\x81\x16'
print(bin(int.from_bytes(a,byteorder='big'))[2:])
# pay load is 9:16
# if it is 126, read 16:32
# mask key is 32 bit after payload len
#