import zmq, sys, hashlib

partSize = 1024*1024*10

def uploadFile(context, filename, servers):
    fileSha1 = bytes(computeHashFile(filename), "ascii")
    sockets = []
    for address in servers:
        s = context.socket(zmq.REQ)
        s.connect("tcp://" + address.decode("ascii"))
        sockets.append(s)

    with open(filename, "rb") as f:
        part = 0
        while True:
            data = f.read(partSize)
            if not data:
                break
            print("Uploading part {}".format(part))
            sha1bt = bytes(computeHash(data), "ascii")
            sockets[0].send_multipart([b'upload', filename, data, sha1bt, fileSha1])
            response = sockets[0].recv()
            print("Reply [%s ]" %(response))
            #sockets.append(sockets.pop(0))
            part += 1
            

def computeHashFile(filename):
    BUFFER = 65536
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUFFER)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def computeHash(bt):
    sha1 = hashlib.sha1()
    sha1.update(bt)
    return sha1.hexdigest()

def main():
    if len(sys.argv) != 4:
        print("Sample call: python <client.py> <username> <operation> <filename>")
        exit()

    username = sys.argv[1]
    operation = sys.argv[2]
    filename = sys.argv[3].encode('ascii')

    context = zmq.Context()
    proxySocket = context.socket(zmq.REQ)
    proxySocket.connect("tcp://localhost:6666")

    print("Operation: {}".format(operation))

    if operation == "upload":
        proxySocket.send_multipart([b'availableServers'])
        availableServers = proxySocket.recv_multipart()
        uploadFile(context, filename, availableServers)
        print("Uploaded {} succesfully.".format(filename))

if __name__=='__main__':
    main()
    