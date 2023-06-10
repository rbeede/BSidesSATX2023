# Uses Python3 http.server for serving requests
# Rodney Beede - 2023-03

import http.server
import logging
import sys
import urllib3

from swiftclient.service import SwiftService, SwiftError


def main(argv):

    # Quiet down the default logging
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger("requests").setLevel(logging.CRITICAL)
    logging.getLogger("swiftclient").setLevel(logging.CRITICAL)
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    

    port = int(argv[1])  # port to listen on (http, no TLS)
    
    container = "fileuploads"

    # Assumes lab OpenStack Swift has been setup and running from same box
    swift_opts = {
        "auth_version": "1.0",
        "auth": "https://localhost:8080/auth/v1.0",
        "user": "system:root",
        "key": "testpass",
        "insecure": True
    }

    custom_handler = HandlerFactory(container, swift_opts)
    http_daemon = http.server.ThreadingHTTPServer(
        ("", port),  # All IPv6 or IPv4 interfaces
        custom_handler
    )
    
    http_daemon.serve_forever()
    

def HandlerFactory(container, swift_opts):
    class VulnerableObjectStorageHTTPRequestHandler(http.server.BaseHTTPRequestHandler, object):
        protocol_version = "HTTP/1.1"
        
        def __init__(self, *args, **kwargs):
            self.container = container
            self.swift_opts = swift_opts
            super(VulnerableObjectStorageHTTPRequestHandler, self).__init__(*args, **kwargs)


        def do_GET(self):
            print(f"Connection from f{self.client_address}")
            
            if(self.path == "/favicon.ico"):
                self.send_response(404)
                self.send_header("Content-Length", 0)
                self.end_headers()
                return

        
            response_content = "<html><body>\r\n"
            response_content += "<input type='button' value='Upload' onclick=\"alert('This simulation would upload a file but only allow characters a-z and nothing else in the filename. No XSS for you.')\"/>\r\n"
            response_content += "<h1>\r\n"
            response_content += "List of Uploaded Files\r\n"
            response_content += "</h1>\r\n"
            response_content += "<pre>\r\n"
            
            with SwiftService(options = self.swift_opts) as swift:
                try:
                    list_parts_gen = swift.list(container = self.container)
                    for page in list_parts_gen:
                        if page["success"]:
                            for item in page["listing"]:

                                i_size = int(item["bytes"])
                                i_name = item["name"]
                                i_etag = item["hash"]

                                response_content += f"{i_name} [size: {i_size}] [etag: {i_etag}]\r\n"
                        else:
                            raise page["error"]

                except SwiftError as e:
                    print(e.value)
            
            response_content += "</pre>\r\n"
            response_content += "</body></html>\r\n"


            encoded_response_content = response_content.encode("utf-8")

            self.send_response(200)
            self.send_header("BSidesSATX", "2023")
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", len(encoded_response_content))
            self.end_headers()

            self.wfile.write(encoded_response_content)
    return VulnerableObjectStorageHTTPRequestHandler  # factory return


if __name__ == "__main__":
    main(sys.argv)
