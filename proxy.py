import sys
import os
import time
import socket
import select

_port = 8888
_hostname = "localhost"
_max_msg_size = 256

def setup_server(hostname, port):
    '''Return a server socket bound to the specified port.'''
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.setblocking(0)
    connection.bind((hostname, port))
    connection.listen(5)
    return connection

def send_messages(sockets, msg):
    '''Send bytes msg to each socket in the dict sockets and return a list of sockets
    which have died.'''

    msg = bytes(msg, encoding="UTF-8")
    to_remove = []
    for sock in sockets:
        total_sent = 0
        try:
            while total_sent < len(msg):
                sent = sock.send(msg[total_sent: total_sent + _max_msg_size])
                total_sent += sent
        except socket.error:
            to_remove.append(sock)
    return to_remove

def handle_message(sock, sockets):
    '''Process the message sent on socket sock and then return a list of client 
    sockets that have been terminated.'''

    to_remove = []
    msg = sock.recv(_max_msg_size).decode("UTF-8")
    if len(msg.strip()) == 0:
        return [sock]

    firstfield = msg.strip().split()[0]
    if firstfield.startswith("<") or len(firstfield) == 0 or \
       (sockets[sock][1] == None and firstfield != "/user"):
        to_remove.append(sock)

    elif firstfield.startswith("/"):
        remainder = msg.strip()[len(firstfield):].strip()
        if firstfield == "/user" and sockets[sock][1] == None:
            if len(remainder) > 0:
                sockets[sock] = (sockets[sock][0], remainder)
                to_remove = send_messages(sockets, "%s has connected." % remainder)
            else:
                to_remove.append(sock)
        elif firstfield == "/users":
            to_remove = send_messages([sock], "%d users are online." % (len(sockets)))
        elif firstfield == "/bye":
            to_remove = send_messages([sock], "Simonsays ...")
            to_remove += send_messages(sockets, "%s has left the room." % sockets[sock][1])
            to_remove.append(sock)
        else:
            to_remove = send_messages([sock], "Server says: Nice try!")

    else:
        to_remove = send_messages(sockets, "%s says: %s" % (sockets[sock][1], msg.strip()))

    return to_remove

# python proxy.py 120

# http://localhost:8888/the.web.page/to/visit/

# Host Name: localhost
# PORT: 8888

# Only handle GET requests


# Here is how you can get time string given the timestamp in Python:
# time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))



# Step 1: Forward HTTP requests and responses without caching

# Step 2: Enable the TCP server to handle simultaneous connections

# Step 3: Enable caching

# Step 4: Make cache items expire

# Step 5: Modify the HTTP response

def parse_header(request):
    headers = request.split('\n')
    top_header = headers[0].split()
    method = top_header[0]
    filename = top_header[1]
    return top_header, method, filename

def fetch_from_cache(filename):
    # Convert to match to cache-saving naming convention.
    if filename[-1] == '/':
        filename = filename + "index.html"
    filename = filename[0] + filename[1:].replace("/", "-")
    try:
        if os.path.exists("cache"):
            file_input = open('cache' + filename, 'r')
            content = file_input.read()
            file_input.close()
            return content
    except:
        return None
    
def save_in_cache(filename, content):
    if not os.path.exists("cache"):
        os.mkdir('cache')
        os.chmod('cache', 0o711)
    # Cache-saving naming convention.
    filename = filename[0] + filename[1:].replace("/", "-")
    file_to_save = open('cache' + filename, 'w')
    file_to_save.write(content)
    file_to_save.close()

def fetch_from_server(filename):
    try:
        filename_split = filename.split('/')
        host = filename_split[1]
        file = "/"
        for subfile in filename_split[2:]:
            if subfile == "":
                break
            else:
                file = file + subfile + "/"
        # Create socket to webbrowser
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, 80))
        connection.setblocking(0)
        get_request = "GET {0} HTTP/1.1\r\nHost: {1}\r\n\r\n".format(file, host)
        sock.sendall(get_request.encode("UTF-8"))
        total_data = ""
        while True:
            data = sock.recv(_max_msg_size).decode("UTF-8")
            if data == "":
                break
            total_data = total_data + data
        content = total_data
        print("content:")
        print(content)
        sock.close()
        return content
    except:
        return None
    
def fetch_file(filename):
    file_from_cache = fetch_from_cache(filename)

    if file_from_cache:
        print('Retrieved from cache')
        return file_from_cache
    else:
        file_from_server = fetch_from_server(filename)
        if file_from_server:
            print('Retrieved from server')
            save_in_cache(filename, file_from_server)
            return file_from_server
        else:
            return None

if __name__ == "__main__":
    connection = setup_server(_hostname, _port)

    inputs = [connection, sys.stdin]
    clients = {}
    while 1:
        inps, outs, errors = select.select(inputs, [], [])

        for inp in inps:
            if inp == sys.stdin: # Terminal input
                send_messages(clients, "<SERVER MESSAGE> " + sys.stdin.readline().rstrip())
            elif inp == connection: # New connection
                (client, address) = connection.accept()
                clients[client] = (address, None)
                inputs.append(client)
                print("Accepted new client", address)
                msg = client.recv(_max_msg_size).decode("UTF-8")
                print("msg:")
                print(msg)
                top_header, method, filename = parse_header(msg)
                print("top_header:")
                print(top_header)
                print("method:")
                print(method)
                print("filename:")
                print(filename)
                if filename == '/':
                    filename = filename + 'index.html'
                content = fetch_file(filename)
                if content:
                    response = 'HTTP/1.1 200 OK\r\n' + content
                else:
                    response = 'HTTP/1.1 404 NOT FOUND\r\n File Not Found'
                client.sendall(response.encode("UTF-8"))
            else:
                try:
                    to_remove = handle_message(inp, clients)
                except socket.error:
                    to_remove = [inp]
                for client in to_remove:
                    print("Dropping client", clients[client])
                    try:
                        send_messages([client], "/bye")
                    except socket.error:
                        pass
                    del clients[client]
                    inputs.remove(client) 
                    client.close()

    print("Terminating")
    connection.close()

