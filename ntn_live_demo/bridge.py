"""Run-owned loopback TCP forwarding from Windows/WSL to the UE display relay."""
import select
import signal
import socket
import socketserver
import threading
import time

class Forward(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection(('10.202.0.2',self.server.destination),timeout=5) as other:
            self.request.settimeout(None);other.settimeout(None)
            while True:
                ready,_,_=select.select([self.request,other],[],[],1)
                for source in ready:
                    data=source.recv(65536)
                    if not data:return
                    (other if source is self.request else self.request).sendall(data)

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True

running=True
def stop(*_):
    global running
    running=False
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
servers=[]
try:
    for port,destination in [(8889,8890),(8190,8190)]:
        server=Server(('127.0.0.1',port),Forward);server.destination=destination;servers.append(server)
        threading.Thread(target=server.serve_forever,daemon=True).start()
    while running:time.sleep(.2)
finally:
    for server in servers:server.shutdown();server.server_close()
