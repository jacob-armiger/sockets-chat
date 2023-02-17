import socket
import threading
import sys
import os
# TODO: track number of messages, track clients left, server command to list current users, server command to show stats of messages, make sure client joins viable channel
class Client:
    def __init__(self, conn):
        self.conn = conn
        self.thread = None
        self.name = None
        self.channel = None
    
    # def send(self, string):
    #     self.conn.send(string.encode())
    # def recv(self, size):
    #     self.conn.recv(size).decode()

class Server:
    def __init__(self):
        self.clients = []
        self.msg_recv = 0
        self.msg_sent = 0
        self.bytes_sent = 0
        self.bytes_recv = 0

        self.PORT = 0
        self.max_channels = 0
        self.running = True

    def end_server(self, server_thread):
        self.running = False
        # Server thread may be waiting for connection so make throwaway connection
        os.system(f'nc {socket.gethostname()} {self.PORT}')
        # Wait for server thread to end
        server_thread.join()
        return

# TODO: track number of messages, 
def server_runner(server):
    # Set up server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("\nHost name: ", socket.gethostname())
    server_socket.bind((socket.gethostname(),server.PORT))
    server_socket.listen(25)

    while server.running:
        # Listen for connection
        conn, address = server_socket.accept()

        if not server.running:
            # End server loop without creating new thread
            break


        # Add client to list and start client thread
        current_client = Client(conn)
        server.clients.append(current_client)

        current_client.thread = threading.Thread(target=client_runner, args=(current_client, server,), daemon=True)
        current_client.thread.start()
    
    # Shutdown and close connection to end server
    conn.shutdown(0)
    conn.close()
    return


def client_runner(current_client, server):
    # Get name and desired channel from client
    current_client.conn.send("Enter username: ".encode())
    current_client.name = current_client.conn.recv(1024).decode()

    current_client.conn.send("Enter channel to enter: ".encode())
    current_client.channel = current_client.conn.recv(1024).decode()

    # Tell admin who connected
    print(current_client.name.rstrip(), "connected to channel", current_client.channel)
   
    # Recieve and dessiminate client messages
    while True:
        try:
            msg = current_client.conn.recv(1024).decode()
            #update msg count
            server.msg_recv = server.msg_recv + 1
            server.bytes_recv = server.bytes_recv + len(msg)
            print(f"received: {server.bytes_recv} bytes")
        except:
            #remove client from client list
            server.clients.remove(current_client)
            print(f"Active Clients: {len(server.clients)}")
            break

        # Send message to everyone on same channel except self
        for cl in server.clients:
            if cl.conn is current_client.conn:
                continue
            if cl.channel == current_client.channel:
                #message is sent, update counter
                encoded_msg = msg.encode()
                server.msg_sent = server.msg_sent + 1
                server.bytes_sent = server.bytes_sent + len(encoded_msg)
                print(f"Sent: {server.bytes_sent} bytes")
                cl.conn.sendall(encoded_msg)
                
    return

def main():
    PORT = 0
    CHANNELS = 0
    if(len(sys.argv) == 3):
        PORT = sys.argv[1]
        CHANNELS = sys.argv[2]
    else:
        print("Usage: Python3 main.py [PORT] [Number of channels]\n")
        return 0

    # initialize server object
    server_object = Server()

    server_object.PORT = int(PORT)
    server_object.max_channels = int(CHANNELS)

    server_thread = threading.Thread(target=server_runner, args=(server_object,), daemon=True)  # setting daemon to True makes while loop break even with the accept connection above?

    server_thread.start()

    print("\nType 'exit' to stop chat server")
    while True:
        try:
            command = input()
            if command == "exit":
                server_object.end_server(server_thread)
                return 0
        except KeyboardInterrupt:
                server_object.end_server(server_thread)
                return 0

if __name__ == "__main__":
    main()