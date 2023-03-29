import argparse 
import socket
import struct
import csv
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
import os 
MAX_BYTES = 6000

def makeRequestPacket(filename,window):
    byteString =bytes(filename,'utf-8')
    return struct.pack(f"!cII{len(byteString)}s",b'R',0,window,byteString)

def sendRequest(hostName,port, filename,window):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(makeRequestPacket(filename,window), (hostName, port))

def receivePackets(sock):
    end = False
    text = ""
    totalPackets = 0
    totalLength = 0
    startTime = datetime.utcnow()
    while not end:
        data, addr = sock.recvfrom(MAX_BYTES)
        header = struct.unpack_from("!cII",data)
        length = header[2]
        totalPackets+=1 if header[0] != b'E' else 0
        totalLength+=length
        if header[0]==b'E':
            end = True
            endTime = datetime.utcnow()
            print("END Packet")
            print("recv time: ",endTime)
            print("sender addr: ",addr)
            print("Sequence num: ",header[1])
            print("length: ",0)
            print("payload: ")
            print("")

            milliseconds = (endTime-startTime)/timedelta(milliseconds=1)
            print("Summary")
            print("sender addr: ",addr)
            print("Total Data packets: ", totalPackets)
            print("Total Data bytes: ", totalLength)
            print("Average packets/second: ", totalPackets*1000/milliseconds)
            print("Duration: ", milliseconds, " ms")
        else:
            payload = struct.unpack_from(f"!{length}s",data,offset=9)[0].decode('utf-8')
            text+=payload
            # print("DATA Packet")
            # print("recv time: ",datetime.utcnow())
            # print("sender addr: ",addr)
            # print("Sequence num: ",header[1])
            # print("length: ",length)
            # print("payload: ",payload[0:min(len(payload),4)])
            # print("")
    return text


def parseTracker():
    with open("tracker.txt", "r") as f:
        d = defaultdict(lambda : [])
        reader = csv.reader(f,delimiter=' ')
        for row in reader:
            d[row[0]].append((int(row[1]), row[2], int(row[3])))
        
    for key in d.keys():
        d[key] = sorted(d[key], key =lambda x: x[0])
    return d



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-o", "--fileoption")
    parser.add_argument("-f", "--f_hostname")
    parser.add_argument("-e", "--f_port")
    parser.add_argument("-w", "--window")
    args = parser.parse_args()
    d = parseTracker()
    window = int(args.window)
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), int(args.port)))

    with open(args.fileoption, "w+") as f:
        pass
    for i in d[args.fileoption]:
        id = i[0]
        #hostname, port, filename
        sendRequest(i[1],i[2],args.fileoption,window)
        text = receivePackets(sock)
        print("<------FULL TEXT------>")
        print(text)
        with open(args.fileoption, "a") as f:
            f.write(text)

