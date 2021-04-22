import sys
import socketserver
import hashlib
import base64
import math
import pymongo
import json

message_401 = "HTTP/1.1 401 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 36\r\n\r\nThe requested content does not exist".encode()
message_200 = "HTTP/1.1 200 OK\r\n"
content_length = "\r\nContent-Length: "
content_type = "Content-Type: "
content = "\r\n\r\n" 
message_101 = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ".encode()
myclient = pymongo.MongoClient('mongo')
mydb = myclient["mydatabase"]
mycol = mydb["history"]
#mycol.drop()

message = "image is not available".encode()
message_len = format(len(message), '07b')
respond_message_len = len('100000010' + message_len)/8
respond_message = int('100000010' + message_len,2).to_bytes(length = int(math.ceil(respond_message_len)), byteorder='big')+message
print(respond_message)



def open_file(file): #open file and read it as bytes, then return the [length of bytes,content in byte] 
    f = open(file,'rb')
    count = 0
    utf_content = f.read()
    for i in utf_content:
        count += 1
    #print([count,utf_content])
    return [count,utf_content]

    
    
def handle_websocket_header(bytes_data):
    binary_data = bin(int.from_bytes(bytes_data,byteorder='big'))[2:]
    data = 0
    def read_bytes(x,a,b):
        return int(x[a:b],2)
    extend_payload = 0
    payload_len = read_bytes(binary_data,9,16)
    if payload_len == 126:
        payload_len = read_bytes(binary_data,16,32)
        extend_payload = 16
    elif payload_len == 127:
        print("payload length is 127")
        payload_len = read_bytes(binary_data,16,80)
        extend_payload = 64
    print("payload len in handle websocket " + str(payload_len))
    
    one = read_bytes(binary_data,16+extend_payload,24+extend_payload)
    two = read_bytes(binary_data,24+extend_payload,32+extend_payload)
    three = read_bytes(binary_data,32+extend_payload,40+extend_payload)
    four = read_bytes(binary_data,40+extend_payload,48+extend_payload)
    data = 0
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
        #print("mask key " + str(mask))
        if i == 0:
            data = int(binary_data[48 + i * 8 + extend_payload : 48 + i * 8 + 8 + extend_payload],2)^mask
        else : 
            data = (data << 8) + int(binary_data[48 + i * 8 + extend_payload: 48 + i * 8 + 8 + extend_payload],2)^mask
    #print(bin(data))
    # head_content_length = len(bytes_data) - (2 + payload_len/8 + 32/8)
    # return [payload_len,head_content_length,one,two,three,four]
    
   
    data_escaping = data.to_bytes(length= payload_len, byteorder='big')
    data_escaped = data_escaping.replace('&'.encode(),'&amp'.encode()).replace('<'.encode(),'&lt'.encode()).replace('>'.encode(),'&gt'.encode())
    data_escaped_len = len(data_escaped)
    print("escaped length " + str(data_escaped_len))
    
    if data_escaped_len < 126:
        return [data_escaped, format(data_escaped_len, '07b'), binary_data[16:32]] 
    elif (data_escaped_len >= 126 and data_escaped_len < 2**16):
        return [data_escaped,format(126,'07b'),format(data_escaped_len,'016b')]
    else:
        return [data_escaped,format(127,'07b'),format(data_escaped_len,'064b')]
   
    return [data.to_bytes(length= payload_len, byteorder='big'), binary_data[9:16], binary_data[16:32]]

def create_websocket_format(payload_data, payload_len, extend_payload_len):

    data = '100000010'
    data = data + payload_len
    # print("data and payload length " + str(data))
    length = int(payload_len,2)
    leading_zero = 8 - len(bin(int.from_bytes(payload_data,byteorder='big'))[2:]) % 8
    
    #print("leading zero " + str(leading_zero))
    if payload_len == format(126,'07b'):
        #print("this is 126 ")
        data += extend_payload_len
        length = int(extend_payload_len,2)
    
    elif payload_len == format(127,'07b'):
        print("doing 127 =====================")
        data += extend_payload_len
    for i in range(0,leading_zero):
        #print("add a 0")
        data += '0'
        #print(data)
    data += bin(int.from_bytes(payload_data,byteorder='big'))[2:]
    #print(data)
    return int(data,2).to_bytes(length = int(math.ceil(len(data)/8)), byteorder='big')
class MyTCPHandler(socketserver.BaseRequestHandler):
    clients = []
    client_sockets = []
    
    def handle(self):
        
        #try:
            while(True):
                received_data = self.request.recv(1024)
                client_id = self.client_address[0] + ':' + str(self.client_address[1])
               
                if self in self.client_sockets:


                    header = handle_websocket_header(received_data)
                    template = create_websocket_format(header[0],header[1],header[2])
                    json_data = {}
                    json_data ["payload data"] = header[0]
                    json_data["payload length"] = header[1]
                    json_data["extend payload length"] = header[2]
                    mycol.insert(json_data)
                    #print(json_data)
                    for i in self.client_sockets:
                        i.request.sendall(template)
                    
                    
                else:
                    print(client_id + " is sending data:")
                    print(received_data.decode())
                    print(client_id)
                    print("handling http request")
                  
                    path = received_data.decode().split('\r')[0].split(' ')[1]
                   
                    if path == '/':
                        print("handling http request")                    
                        html = open_file("index.html")
                        html_message = (message_200 + content_type + "text/html" + "\r\nX-Content-Type-Options: nosniff" + content_length + str(html[0]) + content).encode() + html[1]
                        self.request.sendall(html_message)
                    
                        """self.clients.append(client_id)
                        self.client_sockets.append(self.request)
                        print(self.client_sockets)    
                        print("\n\n")"""
                    elif path == "/websocket":
                        print("handling socket")
                        print(received_data.decode())
                        sec_websocket_key_find = received_data[received_data.find("Sec-WebSocket-Key".encode()):]
                        sec_websocket_key_line = sec_websocket_key_find[0:sec_websocket_key_find.find('\r'.encode())]
                        sec_websocket_key = sec_websocket_key_line.split(' '.encode())[1]
                        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode()
                        accept_response = sec_websocket_key + GUID
                        hash_accept_response = hashlib.sha1(accept_response)
                        base64_accept_response = base64.b64encode(hash_accept_response.digest())
                        websocket_response = message_101 + base64_accept_response + content.encode()  
                        self.client_sockets.append(self)
                        self.request.sendall(websocket_response)
                        for x in mycol.find():
                            payload_data = x["payload data"]
                            payload_len = x["payload length"]
                            extend_payload_len = x["extend payload length"]
                            try:
                                payload_data.decode()
                                template = create_websocket_format(payload_data,payload_len,extend_payload_len)
                            except:
                                print("message can not be decode")
                
                            self.request.sendall(template)

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 8000

    with socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()