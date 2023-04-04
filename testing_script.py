import os
import socket
import subprocess
import time
import sys
def getPort():
    for i in range(2049, 65536):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((socket.gethostname(), i))   
        except socket.error as e:
            continue
        sock.close()
        yield str(i)
    yield -1

gen = getPort()
def test1():

    r1,s1,g1 = next(gen), next(gen), next(gen)
    os.chdir("test1")
    if not os.path.exists("requester"):
        os.mkdir("requester")
    with open("requester/tracker.txt", "w+") as f:
        f.write(f"file.txt 1 {socket.gethostname()} {s1}\n")
    with open("table1.txt", "w+") as f:
        f.write(f"{socket.gethostname()} {g1} {socket.gethostname()} {r1} {socket.gethostname()} {r1} 0 0\n")
        f.write(f"{socket.gethostname()} {g1} {socket.gethostname()} {s1} {socket.gethostname()} {s1} 0 0\n")

    output = sys.stdout
    os.chdir("sender")
    subprocess.Popen(['python3', '../../sender.py',"-p", s1, "-g" , r1, "-r", "100", "-q", "1", "-l" , "10", "-f" , socket.gethostname(), "-e" , g1, "-i", "3" , "-t", "1000"], stdout=output, stderr=subprocess.STDOUT)
    os.chdir('..')

    time.sleep(.5)
    subprocess.Popen(['python3', '../emulator.py', "-p", g1, "-q", "100" , "-f", "table1.txt", "-l", "log"], stdout=output, stderr=subprocess.STDOUT)
    time.sleep(.5)
    os.chdir("requester")
    subprocess.Popen(['python3', "../../requester.py", "-p", r1, "-f",socket.gethostname(), "-e", g1, "-o" , "file.txt", "-w", "10"], stdout=output, stderr=subprocess.STDOUT)

    time.sleep(2)
    sys.stdout.flush()
    p = subprocess.Popen(["diff", "file.txt", "../sender/file.txt"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if out == None or len(out) == 0:
        subprocess.Popen(["echo", "-e" , "\e[92mtest 1 passed\e[0m"])
    else:
        subprocess.Popen(["echo", "-e" , "\e[31mtest 1 failed\e[0m"])
def test2():
    r1,s1 = next(gen), next(gen)
    os.chdir("tests/test2")
    if not os.path.exists("requester"):
        os.mkdir("requester")
    with open("requester/tracker.txt", "w+") as f:
        f.write(f"hello.txt 1 {socket.gethostname()} {s1}\n")
    with open("hello.txt", "w+") as f:
        for i in range(100):
            f.write("1")
    length = os.stat("hello.txt").st_size
    output = subprocess.DEVNULL
    subprocess.Popen(['python3', '../../sender.py',"-p", s1, "-g" , r1, "-r", "2", "-q", "0", "-l" , str(length//2)], stdout=output)
    os.chdir("requester")
    subprocess.Popen(['python3', "../../../requester.py", "-p", r1, "-o" , "hello.txt"], stdout=output)
    time.sleep(2)
    p = subprocess.Popen(["diff", "hello.txt", "../hello.txt"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if out == None or len(out) == 0:
        subprocess.Popen(["echo", "-e" , "\e[92mtest 2 passed\e[0m"])
    else:
        subprocess.Popen(["echo", "-e" , "\e[31mtest 2 failed\e[0m"])
def test3():
    r1,s1,s2 = next(gen), next(gen), next(gen)
    os.chdir("tests/test3")
    if not os.path.exists("requester"):
        os.mkdir("requester")
    if not os.path.exists("sender1"):
        os.mkdir("sender1")
    if not os.path.exists("sender2"):
        os.mkdir("sender2")
    with open("requester/tracker.txt", "w+") as f:
        f.write(f"hello.txt 1 {socket.gethostname()} {s1}\nhello.txt 2 {socket.gethostname()} {s2}")
    with open("sender1/hello.txt", "w+") as f:
        for i in range(50):
            f.write("1")
    with open("sender2/hello.txt", "w+") as f:
        for i in range(100):
            f.write("2")
    length = os.stat("sender1/hello.txt").st_size
    length2 = os.stat("sender2/hello.txt").st_size
    with open("hello.txt" , "w+") as f:
        for i in range(50):
            f.write("1")
        for i in range(100):
            f.write("2")
    output = subprocess.DEVNULL
    subprocess.Popen(['python3', '../../../sender.py',"-p", s1, "-g" , r1, "-r", "2", "-q", "0", "-l" , str(length//2)], stdout=output, cwd="sender1")
    subprocess.Popen(['python3', '../../../sender.py',"-p", s2, "-g" ,  r1, "-r", "2", "-q", "0", "-l" , str(length2//2)], stdout=output, cwd="sender2")

    os.chdir("requester")
    subprocess.Popen(['python3', "../../../requester.py", "-p", r1, "-o" , "hello.txt"], stdout=output)
    time.sleep(3)
    p = subprocess.Popen(["diff", "hello.txt", "../hello.txt"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if out == None or len(out) == 0:
        subprocess.Popen(["echo", "-e" , "\e[92mtest 3 passed\e[0m"])
    else:
        subprocess.Popen(["echo", "-e" , "\e[31mtest 3 failed\e[0m"])

def test4():
    r1,s1 = next(gen), next(gen)
    os.chdir("tests/test4")
    if not os.path.exists("requester"):
        os.mkdir("requester")
    with open("requester/tracker.txt", "w+") as f:
        f.write(f"hello.txt 1 {socket.gethostname()} {s1}\n")
    with open("hello.txt", "w+") as f:
        for i in range(500):
            f.write("1")
    length = os.stat("hello.txt").st_size

    output = subprocess.DEVNULL
    subprocess.Popen(['python3', '../../sender.py',"-p", s1, "-g" , r1, "-r", "3", "-q", "0", "-l" , str(length//3)], stdout=output)

    os.chdir("requester")
    subprocess.Popen(['python3', "../../../requester.py", "-p", r1, "-o" , "hello.txt"], stdout=output)
    time.sleep(3)
    p = subprocess.Popen(["diff", "hello.txt", "../hello.txt"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if out == None or len(out) == 0:
        subprocess.Popen(["echo", "-e" , "\e[92mtest 4 passed\e[0m"])
    else:
        subprocess.Popen(["echo", "-e" , "\e[31mtest 4 failed\e[0m"])

def test5():
    r1,s1,s2 = next(gen), next(gen), next(gen)
    os.chdir("tests/test5")
    if not os.path.exists("requester"):
        os.mkdir("requester")
    if not os.path.exists("sender1"):
        os.mkdir("sender1")
    if not os.path.exists("sender2"):
        os.mkdir("sender2")
    with open("requester/tracker.txt", "w+") as f:
        f.write(f"hello.txt 1 {socket.gethostname()} {s1}\nhello.txt 2 {socket.gethostname()} {s2}")
    with open("sender1/hello.txt", "w+") as f:
        for i in range(400):
            f.write("1")
    with open("sender2/hello.txt", "w+") as f:
        for i in range(500):
            f.write("2")
    length = os.stat("sender1/hello.txt").st_size
    length2 = os.stat("sender2/hello.txt").st_size
    with open("hello.txt" , "w+") as f:
        for i in range(400):
            f.write("1")
        for i in range(500):
            f.write("2")
    output = subprocess.DEVNULL
    subprocess.Popen(['python3', '../../../sender.py',"-p", s1, "-g" , r1, "-r", "10", "-q", "0", "-l" , str(length//10)], stdout=output, cwd="sender1")
    subprocess.Popen(['python3', '../../../sender.py',"-p", s2, "-g" ,  r1, "-r", "10", "-q", "0", "-l" , str(length2//10)], stdout=output, cwd="sender2")

    os.chdir("requester")
    subprocess.Popen(['python3', "../../../requester.py", "-p", r1, "-o" , "hello.txt"], stdout=output)
    time.sleep(3)
    p = subprocess.Popen(["diff", "hello.txt", "../hello.txt"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if out == None or len(out) == 0:
        subprocess.Popen(["echo", "-e" , "\e[92mtest 5 passed\e[0m"])
    else:
        subprocess.Popen(["echo", "-e" , "\e[31mtest 5 failed\e[0m"])

if __name__ == "__main__":
    for i in ["test" + str(i) for i in range(1,2)]:
        globals()[i]()
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        