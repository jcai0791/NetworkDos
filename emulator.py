import argparse 
import socket
import struct
import csv
import random
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
import os 
import asyncio
import errno

MAX_BYTES = 6000
PRIOQ = [[],[],[]]
DELAYING = False
def encapsulate(priority, src_ip, src_port, dest_ip, dest_port,payload):
    packet = struct.pack(f"!B4sH4sHI{len(payload)}s",priority,src_ip,src_port,dest_ip,dest_port,len(payload),payload)
    return packet


def decapsulate(packet):
    header = struct.unpack_from("!B4sH4sHI",packet)
    length = header[5]
    payload = struct.unpack_from(f"!{length}s",packet,offset=17)[0]
    return header,payload

def getType(data):
    h = struct.unpack_from("!cII",data)
    return h[0]

def parseTable(fileName, selfHostname, selfPort):
    with open(fileName, "r") as f:
        d = defaultdict(lambda : ("",0,0,0))
        reader = csv.reader(f,delimiter=' ')
        for row in reader:
            if(row[0]==selfHostname and int(row[1])==selfPort):
                destHost = socket.inet_aton(socket.gethostbyname(row[2]))
                destPort = int(row[3])
                nextHost = socket.gethostbyname(row[4])
                nextPort = int(row[5])
                delay = int(row[6])
                lossProb = int(row[7])
                d[(destHost, destPort)] = (nextHost,nextPort, delay, lossProb) 
        return d

#Each log event must include:
# source hostname and port
# intended destination host name and port
# time of loss (to millisecond resolution)
# priority level of the packet
# size of the payload.
def log(packet, logFile, reason):
    outerHeader,payload = decapsulate(packet)
    with open(logFile, "a") as f:
        f.write(reason,"\n")
        f.write("Source Address: ",socket.inet_ntoa(outerHeader[1])," Port: ",outerHeader[2],"\n")
        f.write("Destination Address: ",socket.inet_ntoa(outerHeader[3])," Port: ",outerHeader[4],"\n")
        f.write("Time of Loss: ",datetime.utcnow(),"\n")
        f.write("Priority level: ",outerHeader[0],"\n")
        f.write("Payload Size: ",outerHeader[5]," Bytes\n")
        f.write("-"*50)
        
def forwardPacket(packet, nextHopIp, nextHopPort):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(packet,(nextHopIp,nextHopPort))

async def sendPacket(next,packet,file,type):
    DELAYING = True
    await asyncio.sleep(next[2])
    if(type!='E' and random.randint(1,100)<=next[3]):
        #drop packet
        log(packet,file,"Random Loss Occurred")
        DELAYING = False
        return

    forwardPacket(packet, next[0], next[1])
    DELAYING = False
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-q", "--queue_size")
    parser.add_argument("-f", "--filename")
    parser.add_argument("-l", "--log")
    args = parser.parse_args()
    queue_size = int(args.queue_size)
    table = parseTable(args.filename,socket.gethostname(),int(args.port))

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
            priority = header[0]
            if(not table[(destAdd,destPort)]):
                log(packet,args.log,"No forwarding entry found")
                continue

            if(len(PRIOQ[priority-1]) < queue_size):
                PRIOQ[priority-1].append(packet)
            else:
                log(packet,args.log, f"Queue {priority} full")

            #send
            if(not DELAYING):
                for prio in range(0,3):
                    if(PRIOQ[prio]):
                        sentPacket = PRIOQ[prio].pop()
                        asyncio.run(sendPacket(table[(destAdd,destPort)],sentPacket,args.log,type))
                        break




            


    
