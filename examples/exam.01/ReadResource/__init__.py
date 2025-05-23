import sys, io, os

def read() :
    path = os.path.dirname(os.path.abspath(__file__))
    #print(path)
    f = open(os.path.join(path, "config.ini"), 'r')
    while True:
        line = f.readline()
        if not line: break
        print(line.strip())
    f.close()
    