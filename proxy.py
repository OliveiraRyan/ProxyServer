import sys
import os
import time
import socket
import select
from datetime import datetime

# python proxy.py 120

# http://localhost:8888/the.web.page/to/visit/

# Host Name: localhost
# PORT: 8888

# Only handle GET requests

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

def handle_message(sock, sockets):
    '''Process the message sent on socket sock and then return a list of client 
    sockets that have been terminated.'''

    to_remove = []
    msg = sock.recv(_max_msg_size).decode("UTF-8")
    if len(msg.strip()) == 0:
        return [sock]

    firstfield = msg.strip().split()[0]
    if len(firstfield) == 0 or \
       (sockets[sock][1] == None and firstfield != "/user"):
        to_remove.append(sock)

    return to_remove

def parse_header(request):
    headers = request.split('\n')
    top_header = headers[0].split()
    method = top_header[0]
    filename = top_header[1]
    return top_header, method, filename

def fetch_from_cache(filename):
    filename = filename[0] + filename[1:].replace("/", "-")
    
    time_until_expire = None
    if len(sys.argv) == 2:
        time_until_expire = int(sys.argv[1])

    try:
        if os.path.exists("cache"):
            if time_until_expire:
                print("filename to fetch from cache: " + 'cache' + filename)
                last_mod = os.path.getmtime('cache' + filename)
                expiration_time = last_mod + time_until_expire
                if (expiration_time <= time.time()):
                    return None
            file_input = open('cache' + filename, 'rb')
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
    print("filename to save in cache: " + 'cache' + filename)
    file_to_save = open('cache' + filename, 'wb')
    file_to_save.write(content)
    file_to_save.close()

def fetch_from_server(filename):
    try:
##        if filename[-4:] == ".ico":
##            return None
        if filename[-1] == '/':
            filename = filename + "index.html"
        filename_split = filename.split('/')
        if len(filename_split) == 2:
            filename_split.append("index.html")
        host = filename_split[1]
        file_path = ""
        for subfile in filename_split[2:]:
            if subfile == "":
                break
            else:
                file_path = file_path + "/" + subfile

        # Create socket to webbrowser
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Host before connect: " + host)
        print(filename_split)
        sock.connect((host, 80))
        print("Connecting to webbrowser...")
        print("File: " + file_path)
        print("Host: " + host)
        get_request = "GET {0} HTTP/1.1\r\nHost: {1}\r\n\r\n".format(file_path, host)
        sock.sendall(get_request.encode("UTF-8"))

        content = b""
        cc=0
        while True:
            # print("reading.. " + str(cc))
            cc+=1
            data = sock.recv(_max_msg_size)
            if filename.endswith("/index.html"):
                print("reading.. " + str(cc))
                print(data)
            # print(data)
            if not data:
                print("break")
                break
            content = content + data
        #content = total_data
        print("before close")
        sock.close()
        print("after close")
        if filename.endswith(".html"):
            # print(content)
            return html_injection(content)
        return content
    except:
        print(sys.exc_info()[0])
        print("Something broke")
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

def html_injection(content):
    now = datetime.now() # Current date and time
    dt = '<body><p style="z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; \
        background-color:yellow; padding:10px; font-weight:bold;">Last cached:<br/>{}</p>'.format(now.strftime('%Y-%m-%d %H:%M:%S'))
    return content.replace(b'<body>', bytes(dt, 'ASCII'))

if __name__ == "__main__":
    connection = setup_server(_hostname, _port)

    inputs = [connection]
    clients = {}
    while 1:
        inps, outs, errors = select.select(inputs, [], [])

        for inp in inps:
            if inp == connection: # New connection
                (client, address) = connection.accept()
                clients[client] = (address, None)
                inputs.append(client)
                print("Accepted new client", address)
                msg = b''
                while True:
                    client_msg = client.recv(_max_msg_size)
                    msg = msg + client_msg
                    if not client_msg or b'\r\n\r\n' in client_msg:
                        break
                msg = msg.decode("UTF-8")
                if msg == '':
                    break
                print("msg:")
                print(msg)
                top_header, method, filename = parse_header(msg)
                print("top_header:")
                print(top_header)
                print("method:")
                print(method)
                print("filename after parse:")
                print(filename)
                if filename == '/':
                    filename = filename + 'index.html'
                content = fetch_file(filename)
                print("FILE FETCHED!")
                if not content:
                    content = b'HTTP/1.1 404 NOT FOUND\r\n File Not Found'
                client.sendall(content)
            else:
                try:
                    to_remove = handle_message(inp, clients)
                except socket.error:
                    to_remove = [inp]
                for client in to_remove:
                    print("Dropping client", clients[client])
                    del clients[client]
                    inputs.remove(client) 
                    client.close()

    print("Terminating")
    connection.close()

