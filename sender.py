import argparse
import socket
import struct
from datetime import datetime
import os
import time

MAX_BYTES = 6000


def encapsulate(priority, src_ip, src_port, dest_ip, dest_port,payload):
    print(src_ip)
    print(dest_ip)
    packet = struct.pack(f"!B4sH4sHI{len(payload)}s",priority,src_ip,src_port,dest_ip,dest_port,len(payload),payload)
    return packet


def decapsulate(packet):
    header = struct.unpack_from("!B4sH4sHI",packet)
    length = header[5]
    payload = struct.unpack_from(f"!{length}s",packet,offset=17)[0]
    return header,payload

def readFile(filename, b):
    bytearr = []
    with open(filename, "rb") as f:
        while (byte := f.read(b)):
            bytearr.append(byte)
    return bytearr


def receiveRequest(serversocket):
    data, addr = serversocket.recvfrom(MAX_BYTES)
    outHeader,payload = decapsulate(data)
    request = struct.unpack_from("!cII",payload)
    window = request[2]
    # fileName = struct.unpack_from(f"!{length}s",data,offset=9)[0].decode('utf-8')
    fileName = payload[9:].decode('utf-8')
    print("file name recieved : "+fileName)
    return fileName, addr, window, outHeader


def makeDataPacket(bytes, sequence_num):
    return struct.pack(f"!cII{len(bytes)}s",b'D',sequence_num,len(bytes),bytes)

def makeEndPacket():
    return struct.pack(f"!cII",b'E',0,0)

def sendData(requesterIP,requesterPort,emulatorHostname,emulatorPort, bytes, sequence_num,priority,ownPort):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    payload = makeDataPacket(bytes,sequence_num)
    ownIP = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
    packet = encapsulate(priority,ownIP,ownPort,requesterIP,requesterPort,payload)
    sock.sendto(packet, (emulatorHostname, emulatorPort))

def sendEnd(requesterIP,requesterPort,emulatorHostname,emulatorPort,priority,ownPort):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    ownIP = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
    packet = encapsulate(priority,ownIP,ownPort,requesterIP,requesterPort,makeEndPacket())
    sock.sendto(packet, (emulatorHostname, emulatorPort))

    
def printData(address,sequence,section):
    print("DATA Packet")
    print("send time: ",datetime.utcnow())
    print("requester addr: ",address)
    print("Sequence num: ",sequence)
    print("length: ",len(section))
    print("payload: ",section.decode('utf-8')[0:min(len(section),4)])
    print("")

def printEnd(address, sequence):
    print("END Packet")
    print("send time: ",datetime.utcnow())
    print("requester addr: ",address)
    print("Sequence num: ",sequence)
    print("length: ",0)
    print("payload: ")
    print("")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-g", "--requester_port")
    parser.add_argument("-r", "--rate")
    parser.add_argument("-q", "--seq_no") #deprecated
    parser.add_argument("-l", "--length")
    parser.add_argument("-f", "--f_hostname")
    parser.add_argument("-e", "--f_port")
    parser.add_argument("-i", "--priority")
    parser.add_argument("-t", "--timeout")
    args = parser.parse_args()
    
    serversocket = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    serversocket.bind((socket.gethostname(), int(args.port)))
    filename, address, window, header = receiveRequest(serversocket)
    sequence = 1
    with open(filename,"r+b") as file:
        bytes = bytearray(file.read())
        for i in range(0,len(bytes),int(args.length)):
            section = bytes[i:min(i+int(args.length),len(bytes))]
            sendData(header[1],int(args.requester_port),args.f_hostname,int(args.f_port),section,sequence,int(args.priority),int(args.port))
            printData(address,sequence,section)
            sequence += 1
            time.sleep(1.0/int(args.rate))
        sendEnd(header[1],int(args.requester_port),args.f_hostname,int(args.f_port),int(args.priority),int(args.port))
        printEnd(address,sequence)

    print("Percent of packets lost: !!!!!Bruh Moment!!!!!")
        

    serversocket.close()
