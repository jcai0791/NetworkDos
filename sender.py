import argparse
import socket
import struct
from datetime import datetime
import os
import time
import errno
import asyncio
import copy
from collections import defaultdict
MAX_BYTES = 6000
ACKS = defaultdict(lambda : False)
 
def encapsulate(priority, src_ip, src_port, dest_ip, dest_port,payload):
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

def giveUp(seqNum):
    print(f"Error: Retried sending packet {seqNum} five times with no ACK")

#Does a single try of receiving packet in a non-blocking way
#Returns -1 if no packet found, else returns sequence number
async def receiveACK(serversocket, seq_no):
    while True:
        if(ACKS[seq_no]):
             return seq_no
        try:
            lock = asyncio.Lock()
            async with lock:
                packet, address = serversocket.recvfrom(MAX_BYTES)
                outerHeader, payload = decapsulate(packet)
                header = struct.unpack_from("!cII",payload)
                ACKS[header[1]] = True

        except socket.error as e:
            err = e.args[0] 
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                # a "real" error occurred
                print(e)
        await asyncio.sleep(0)


async def timeout(seq_no, serversocket, t):
    try:
       await asyncio.wait_for(receiveACK(serversocket, seq_no), timeout=int(t))
       return 0
    except asyncio.TimeoutError:
        return -1
    return 0

async def main(seq_no, serversocket, t):
    return await asyncio.gather(*[asyncio.create_task(timeout(i, serversocket, t)) for i in seq_no])

# def receiveACK(serversocket, seq_no):
#     try:
#         packet, address = serversocket.recvfrom(MAX_BYTES)
#         outerHeader, payload = decapsulate(packet)
#         header = struct.unpack_from("!cII",payload)
#         assert(header[0]== b'A')
#         ACKS[header[1]] = True
#         if(ACKS[seq_no]):
#             return seq_no
#     except socket.error as e:
#         err = e.args[0] 
#         if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
#             pass
#         else:
#             # a "real" error occurred
#             print(e)
#     await()


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
    serversocket.setblocking(False)

    sequence = 1
    with open(filename,"r+b") as file:
        bytes = bytearray(file.read())
        buffer = [None for i in range(window)]
        times = []
        for i in range(0,len(bytes),int(args.length)):
            section = bytes[i:min(i+int(args.length),len(bytes))]
            sendData(header[1],int(args.requester_port),args.f_hostname,int(args.f_port),section,sequence,int(args.priority),int(args.port))
            buffer[(sequence-1) % window] = section
            
            #print(sequence, i , len(bytes))
            #printData(address,sequence,section)
            if(sequence % window == 0 or i >= len(bytes) - int(args.length)):
                j = 0
                nums = [ k for k in range((((sequence-1)//window) * window) + 1, sequence + 1) ]
                while len(nums) > 0 and j <= 5:
                    res = asyncio.run(main(nums ,  serversocket, args.timeout))
                    nums = [nums[k] for k, j in enumerate(res) if j == -1]
                    print(nums)
                    for s in nums:
                        sendData(header[1],int(args.requester_port),args.f_hostname,int(args.f_port),buffer[(s-1) % window],s,int(args.priority),int(args.port))
                        time.sleep(1.0/int(args.rate))
                    j+=1
                for s in nums:
                    giveUp(s)
            sequence += 1
            time.sleep(1.0/int(args.rate))


                
        sendEnd(header[1],int(args.requester_port),args.f_hostname,int(args.f_port),int(args.priority),int(args.port))
        #printEnd(address,sequence)

    #print("Percent of packets lost: !!!!!Bruh Moment!!!!!")
        

    serversocket.close()
