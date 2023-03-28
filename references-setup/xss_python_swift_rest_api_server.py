# modified from OpenStack Swift Docs examples for python SwiftService API
# Rodney Beede - 2022-06

import logging

from swiftclient.service import SwiftService, SwiftError
from sys import argv

import socket

logging.basicConfig(level=logging.ERROR)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("swiftclient").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

container = argv[1]
port = int(argv[2])


# Hard-coded is the best coded
_opts = {
    "auth_version": "1.0",
    "auth": "https://localhost:8080/auth/v1.0",
    "user": "system:root",
    "key": "testpass",
    "insecure": True
}


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(("0.0.0.0", port))

s.listen(3)

while True:
    conn_socket, client_addr = s.accept()
    
    print(f"Connection from {client_addr}")
    
    conn_socket.recv(1024)
    
    conn_socket.sendall("HTTP/1.1 200 OK\r\n".encode())
    conn_socket.sendall("Connection: close\r\n".encode())
    conn_socket.sendall("BSides: SATX 2022\r\n".encode())
    conn_socket.sendall("Content-Type: text/html\r\n".encode())
    conn_socket.sendall("Cache-Control: no-cache, no-store, must-revalidate\r\n".encode())
    conn_socket.sendall("Pragma: no-cache\r\n".encode())
    conn_socket.sendall("Expires: 0\r\n".encode())
    conn_socket.sendall("\r\n".encode())
    
    conn_socket.sendall("<html><body>\r\n".encode())
    conn_socket.sendall("<input type='button' value='Upload' onclick=\"alert('This simulation would upload a file but only allow characters a-z and nothing else in the filename. No XSS for you.')\"/>\r\n".encode())
    conn_socket.sendall("<h1>\r\n".encode())
    conn_socket.sendall("List of Uploaded Files\r\n".encode())
    conn_socket.sendall("</h1>\r\n".encode())
    conn_socket.sendall("<pre>\r\n".encode())

    with SwiftService(options=_opts) as swift:
        try:
            list_parts_gen = swift.list(container=container)
            for page in list_parts_gen:
                if page["success"]:
                    for item in page["listing"]:

                        i_size = int(item["bytes"])
                        i_name = item["name"]
                        i_etag = item["hash"]
                        print(
                            "%s [size: %s] [etag: %s]" %
                            (i_name, i_size, i_etag)
                        )
                        conn_socket.sendall( ("%s [size: %s] [etag: %s]\r\n" %
                            (i_name, i_size, i_etag)).encode() )
                else:
                    raise page["error"]

        except SwiftError as e:
            logger.error(e.value)
    
    conn_socket.sendall("</pre>\r\n".encode())
    conn_socket.sendall("</body></html>\r\n".encode())
    conn_socket.close()