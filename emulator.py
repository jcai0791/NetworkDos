import argparse 
import socket
import struct
import csv
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
import os 
import errno
MAX_BYTES = 6000

def encapsulate(priority, src_ip, src_port, dest_ip, dest_port,payload):
    packet = struct.pack(f"!BIHIHI{len(payload)}s",priority,src_ip,src_port,dest_ip,dest_port,len(payload),payload)
    return packet

def decapsulate(packet):
    header = struct.unpack_from("!BIHIHI",packet)
    length = header[5]
    payload = struct.unpack_from(f"!{length}s",packet,offset=17)[0]
    return header,payload

def getType(data):
    h = struct.unpack_from("!cII",data)
    return h[0]

def parseTable(fileName, selfHostname, selfPort):
    with open(fileName, "r") as f:
        d = defaultdict(lambda : [])
        reader = csv.reader(f,delimiter=' ')
        for row in reader:
            if(row[0]==selfHostname and int(row[1])==selfPort):
                destHost = row[2]
                destPort = int(row[3])
                nextHost = row[4]
                nextPort = int(row[5])
                delay = int(row[6])
                lossProb = int(row[7])
                #TODO

def forwardPacket(packet, nextHopIp, nextHopPort):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(packet,(nextHopIp,nextHopPort))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-q", "--queue_size")
    parser.add_argument("-f", "--filename")
    parser.add_argument("-l", "--log")
    args = parser.parse_args()

    table = parseTable(args.filename)

    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), int(args.port)))
    sock.setblocking(0)


    while(True):
        try:
            packet, address = sock.recvfrom(MAX_BYTES)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                #No packet received yet. Do step 4
                continue
            else:
                # a "real" error occurred
                print(e)
                break
        else:
            header, payload = decapsulate(packet)
            destAdd = header[3]
            destPort = header[4]
            type = getType(payload)
            


            


    
