#kill zqm python: taskkill /F /IM python.exe
import zmq, sys, hashlib

partSize = 1024*1024*10

def downloadIndexFile(socket):
    print("Downloading index file")
    socket.send(b'IndexFile')
    filename, data = socket.recv_multipart()
    with open(filename, "wb") as f:
        while True:
            if data == b'done':
                break
            f.write(data)
            socket.send(b'IndexFile')
            filename, data = socket.recv_multipart()
    return filename

    

def uploadIndexFile(socket, filename):
    with open(filename, "rb") as f:
        while True:
            data = f.read(partSize)
            if not data:
                break
            socket.send_multipart([b'uploadIndexFile', filename, data])
            response = socket.recv()
        socket.send_multipart([b'uploadIndexFile', filename, b'done'])
        response = socket.recv()

def uploadFile(context, filename, servers):
    fileSha1 = bytes(computeHashFile(filename), "ascii")
    indexFile = open(fileSha1.decode("ascii"), "wb")
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
            sha1bt = computeHash(data)
            newPart = (sha1bt+','+servers[0].decode("ascii")+",\n").encode("ascii")
            indexFile.write(newPart)
            servers.append(servers.pop(0))
            sockets[0].send_multipart([b'upload', filename, data, sha1bt.encode("ascii"), fileSha1])
            response = sockets[0].recv()
            print("Reply [%s ]" %(response))
            sockets.append(sockets.pop(0))
            part += 1
    for s in sockets:
        s.close()
    indexFile.close()
    return fileSha1


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
        print("Sample call: python client.py <username> <operation> <filename>")
        exit()

    username = sys.argv[1]
    operation = sys.argv[2]
    filename = sys.argv[3].encode('ascii')

    context = zmq.Context()
    proxySocket = context.socket(zmq.REQ)
    proxySocket.connect("tcp://localhost:6666")

    print("Operation: {}".format(operation))
    #login
    proxySocket.send_multipart([b'login', username.encode("ascii")])
    print(proxySocket.recv().decode("ascii"))

    if operation == "upload":
        proxySocket.send_multipart([b'availableServers'])
        availableServers = proxySocket.recv_multipart()
        indexFile = uploadFile(context, filename, availableServers)
        print("Uploaded {} succesfully.".format(filename))
        print("Sending index file {} to proxy".format(indexFile))
        uploadIndexFile(proxySocket, indexFile)
        proxySocket.send_multipart([b'newFile', indexFile, filename, username.encode("ascii")])
        print(proxySocket.recv().decode("ascii"))
    if operation == 'download':
        proxySocket.send_multipart([b'download', username.encode("ascii"), filename])
        response = proxySocket.recv()
        if response == b'yes':
            indexFile = downloadIndexFile(proxySocket)
            indexFile = open(indexFile, "rb")
            donwloadedFile = open(filename, "ab")
            for line in indexFile:
                line = line.decode("ascii")
                print(line)
                line = line.split(",")
                print(line)
                s = context.socket(zmq.REQ)
                s.connect('tcp://' + line[1])
                s.send_multipart([b'download', line[0].encode("ascii")])
                partOfFile = s.recv()
                donwloadedFile.write(partOfFile)
            print("Download Complete")
        else:
            print("This file doesnt exist")
    if operation == 'share':
        proxySocket.send_multipart([b'share', username.encode("ascii"), filename])
        response = proxySocket.recv()
        if response == b'yes':
            toWho = input("Do you want to share {} with(insert): ".format(filename))
            proxySocket.send(toWho)
            response = proxySocket.recv()
            if response == b'yes':
                print("The file was shared")
            else:
                print("User {} doesnt exist".format(toWho))
        else:
            print("This file doesnt exist")

if __name__=='__main__':
    main()
    