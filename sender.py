import argparse
import socket
import struct
from datetime import datetime
import os
import time

MAX_BYTES = 6000

def receiveRequest(serversocket):
    data, addr = serversocket.recvfrom(MAX_BYTES)
    request = struct.unpack_from("!cII",data)
    length = request[2]
    fileName = struct.unpack_from(f"!{length}s",data,offset=9)[0].decode('utf-8')
    print("file name recieved : "+fileName)
    return fileName, addr



def readFile(filename, b):
    bytearr = []
    with open(filename, "rb") as f:
        while (byte := f.read(b)):
            bytearr.append(byte)
    return bytearr


def makeDataPacket(bytes, sequence_num):
    return struct.pack(f"!cII{len(bytes)}s",b'D',sequence_num,len(bytes),bytes)

def makeEndPacket():
    return struct.pack(f"!cII",b'E',0,0)

def sendData(address,port, bytes, sequence_num):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(makeDataPacket(bytes,sequence_num), (address, port))

def sendEnd(address, port):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(makeEndPacket(), (address, port))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-g", "--requester_port")
    parser.add_argument("-r", "--rate")
    parser.add_argument("-q", "--seq_no")
    parser.add_argument("-l", "--length")
    args = parser.parse_args()
    
    serversocket = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    serversocket.bind((socket.gethostname(), int(args.port)))
    
    filename, address = receiveRequest(serversocket)
    sequence = int(args.seq_no)
    with open(filename,"r+b") as file:
        bytes = bytearray(file.read())
        for i in range(0,len(bytes),int(args.length)):
            section = bytes[i:min(i+int(args.length),len(bytes))]
            sendData(address[0],int(args.requester_port),section,sequence)
            print("DATA Packet")
            print("send time: ",datetime.utcnow())
            print("requester addr: ",address)
            print("Sequence num: ",sequence)
            print("length: ",len(section))
            print("payload: ",section.decode('utf-8')[0:min(len(section),4)])
            print("")
            sequence += len(section)
            time.sleep(1.0/int(args.rate))
        sendEnd(address[0],int(args.requester_port))
        print("END Packet")
        print("send time: ",datetime.utcnow())
        print("requester addr: ",address)
        print("Sequence num: ",sequence)
        print("length: ",0)
        print("payload: ")
        print("")
        

    serversocket.close()
