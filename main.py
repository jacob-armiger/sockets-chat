import socket
import threading
import sys
import os

class Client:
    def __init__(self, conn):
        self.conn = conn
        self.thread = None
        self.name = None
        self.channel = None

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
        # Server thread may be waiting for connection, so make throwaway connection
        os.system(f'nc {socket.gethostname()} {self.PORT}')
        # Wait for server thread to end
        server_thread.join()
        return


def server_runner(server):
    # Set up server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("\nHost name: ", socket.gethostname())
    print("---------------------------------\n")
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

    tmp_str = "Channels available\n"
    for i in range(1, server.max_channels+1):
        tmp_str += f'{i} '
    tmp_str += "\nSelect one of the above channels: "

    current_client.conn.send(tmp_str.encode())

    # Have client choose channel
    while True:
        selected_channel = current_client.conn.recv(1024).decode().rstrip()

        # Set channel
        if(selected_channel.isdigit() and int(selected_channel) <= server.max_channels and int(selected_channel) > 0):
            current_client.channel = selected_channel
            break
        current_client.conn.send("That channel isn't available...\n".encode())

    # Tell client they've connected
    current_client.conn.send(f"You've connected to channel {current_client.channel}\n".encode())

    # Tell admin who connected
    print(current_client.name.rstrip(), "connected to channel", current_client.channel, "\n")

    # Recieve and dessiminate client messages
    while True:
        try:
            msg = current_client.conn.recv(1024).decode()

            if not msg:
                # Remove client from list
                server.clients.remove(current_client)
                break

            #update msg count
            server.msg_recv = server.msg_recv + 1
            server.bytes_recv = server.bytes_recv + len(msg)
        except:
            break

        # Show username in message
        msg = f'{current_client.name.rstrip()}: {msg}'
        # Send message to everyone on same channel except self
        for cl in server.clients:
            if cl.conn is current_client.conn:
                continue
            if cl.channel == current_client.channel:
                # send msg, update counter
                encoded_msg = msg.encode()
                server.msg_sent = server.msg_sent + 1
                server.bytes_sent = server.bytes_sent + len(encoded_msg)
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

    print("Commands:\n'exit' - ends chat server\n'list' - show list of connected users\n'stats' - show messaging statistics")
    while True:
        # Server Admin input
        try:
            command = input()

            if command == "exit":
                server_object.end_server(server_thread)
                return 0
            elif command == "list":
                client_list = server_object.clients

                if(len(client_list) == 0):
                    print("There are no users connected...")
                else:
                    for i in range(1, len(client_list)+1):
                        print(f'{i} {client_list[i-1].name.rstrip()}')
            elif command == "stats":
                print("Messages forwarded: ", server_object.msg_sent)
                print("Messages recieved: ", server_object.msg_recv)
            print(" ")

        except KeyboardInterrupt:
                server_object.end_server(server_thread)
                return 0

if __name__ == "__main__":
    main()