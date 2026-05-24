import socket
import time

firmware_password = "peanutbutter"

def uart_interface(client_socket):
    client_socket.send(b"""
 ____             _     _   _                            _            
|  _ \ ___   ___ | |_  | |_| |__   ___   _ __ ___  _   _| |_ ___ _ __ 
| |_) / _ \ / _ \| __| | __| '_ \ / _ \ | '__/ _ \| | | | __/ _ \ '__|
|  _ < (_) | (_) | |_  | |_| | | |  __/ | | | (_) | |_| | ||  __/ |   
|_| \_\___/ \___/ \__|  \__|_| |_|\___| |_|  \___/ \__,_|\__\___|_|   
           
    \n""")
    client_socket.send(b"[>] Enter 'help' for a list of commands.\n")

    while True:
        client_socket.send(b"\n> ")
        command = client_socket.recv(1024).decode().strip()

        if command == "help":
            client_socket.send(b"Available commands are: help, flag, exit\n>")
        elif command == "flag":
            client_socket.send(b"Congrats! Here's the flag: NBCTF{P34NUT_8UTT3r_J311Y_T1M3}\n>")
        elif command == "exit":
            break
        else:
            client_socket.send(b"Available commands are : help, flag, exit\n>")

def handle_client(client_socket):
    while True:
        try:
            client_socket.send(b"Please enter the password:\n>")
            password = client_socket.recv(1024).decode().strip()

            if not password:
                continue 

            if password == firmware_password:
                uart_interface(client_socket)
                break  
            else:
                client_socket.send(b"Please enter the password:\n>")
                time.sleep(2)
        except (ConnectionResetError, BrokenPipeError):
            print("[!] Client disconnected abruptly.")
            break

    client_socket.close()

def main():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345)) 
    server_socket.listen(1)
    print("[!] Root the router is running on port 12345...")

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"[!] Connection from {addr}")
            handle_client(client_socket)
        except KeyboardInterrupt:
            break

    server_socket.close()

if __name__ == "__main__":
    main()

