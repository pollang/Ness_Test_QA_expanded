import datetime
from socket import socket, AF_INET, SOCK_STREAM


def request_current_from_ammeter(port: int, command: bytes):
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(('localhost', port))
        s.sendall(command)
        data = s.recv(1024)
        if data:
            print(f"{datetime.datetime.now()} - Received current measurement from port {port}: {data.decode('utf-8')} A")
        else:
            print(f"{datetime.datetime.now()} - No data received.")

