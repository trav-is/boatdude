#!/usr/bin/env python3
"""
the boat dude - local dev server
simple python http server for local hacking
"""

import http.server
import socketserver
import os
import sys
import signal
import threading
import time
from pathlib import Path

class BoatDudeServer:
    def __init__(self, port=8000, directory="."):
        self.port = port
        self.directory = Path(directory).resolve()
        self.server = None
        self.httpd = None
        self.running = False
        
    def start(self):
        """start the server"""
        if self.running:
            print(f"server already running on port {self.port}")
            return
            
        try:
            os.chdir(self.directory)
            
            # custom handler that serves index.html for root requests
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                def end_headers(self):
                    # add cors headers for dev
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    super().end_headers()
                
                def do_GET(self):
                    # serve index.html for root path
                    if self.path == '/':
                        self.path = '/index.html'
                    return super().do_GET()
            
            self.httpd = socketserver.TCPServer(("", self.port), CustomHandler)
            self.server = threading.Thread(target=self.httpd.serve_forever)
            self.server.daemon = True
            self.server.start()
            
            self.running = True
            print(f"🚤 the boat dude server started!")
            print(f"📍 serving: {self.directory}")
            print(f"🌐 url: http://localhost:{self.port}")
            print(f"⏹️  press ctrl+c to stop")
            
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"❌ port {self.port} is already in use. try a different port.")
                print(f"💡 usage: python server.py [port]")
            else:
                print(f"❌ error starting server: {e}")
            sys.exit(1)
    
    def stop(self):
        """stop the server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.running = False
            print("🛑 server stopped")

def signal_handler(sig, frame):
    """handle ctrl+c nicely"""
    print("\n🛑 shutting down server...")
    if 'server' in globals():
        server.stop()
    sys.exit(0)

def main():
    # set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # get port from command line or use default
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ invalid port number. using default port 8000.")
    
    # create and start server
    global server
    server = BoatDudeServer(port=port)
    
    try:
        server.start()
        
        # keep the main thread alive
        while server.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()


