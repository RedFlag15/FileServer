import zmq, sys

def recvIndexFile(socket, filename, data):
    socket.send(b'got')
    with open(filename, "wb") as f:
        while True:
            if data == b'done':
                break
            f.write(data)
            op, filename, data = socket.recv_multipart()
            socket.send(b'got')

def main():
    if len(sys.argv) != 2:
        print("Sample call: python server.py <address: <ip>:<port>>")
        exit()

    filesFolder = "files/"

    clientAddress = sys.argv[1]
    print(clientAddress)
    context = zmq.Context()
    proxySocket = context.socket(zmq.REQ)
    proxySocket.connect("tcp://127.0.0.1:5555")

    clientSocket = context.socket(zmq.REP)
    clientSocket.bind("tcp://{}".format(clientAddress))

    proxySocket.send_multipart([b'newServer', bytes(clientAddress, "ascii")])
    response = proxySocket.recv()
    print(response)

    while True:
        operation, *data = clientSocket.recv_multipart()
        if operation == b'upload':
            filename, bt, sha1bt, sha1File = data
            storeAs = filesFolder + sha1bt.decode("ascii")
            with open(storeAs, "wb") as f:
                f.write(bt)
            clientSocket.send(b"Done")
        elif operation == b'download':
            f = open(filesFolder+data[0].decode("ascii"), "rb")
            partOfFile = f.read()
            clientSocket.send(partOfFile)
        elif operation == b'uploadIndexFile':
            recvIndexFile(clientSocket, data[0].decode("ascii"), data[1])
        else:
            clientSocket.send(b'Unsupported operation')
        

if __name__ == '__main__':
    main()