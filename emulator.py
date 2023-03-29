import argparse
import socket
import struct
from datetime import datetime
import os
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-q", "--queue_size")
    parser.add_argument("-f", "--filename")
    parser.add_argument("-l", "--log")
    args = parser.parse_args()
    
