import socket

class ChatServer:
    def __init__(self, host="0.0.0.0", port=5001):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.address = None
        
    def start_server(self):
        """Initialize and start the server."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print("Server waiting for connection...")
        self.connection, self.address = self.server_socket.accept()
        print(f"Client connected from {self.address}")
        self.handle_client()

    def handle_client(self):
        """Handle communication with the connected client."""
        try:
            while True:
                data = self.receive_data()
                if not data:
                    print("Client disconnected.")
                    break
                
                print(f"Client: {data}")
                
                # Simple Hello World response
                reply = "Hello World!"
                self.send_data(reply)
                
                if data.lower() == "bye":
                    break

        except Exception as e:
            print("An error occurred:", str(e))

        finally:
            self.close_connection()

    def receive_data(self):
        """Receive data from the client."""
        data = self.connection.recv(1024).decode('utf-8')
        if not data or data.lower() == "bye":
            return None
        return data

    def send_data(self, message):
        """Send data to the client."""
        self.connection.send(message.encode('utf-8'))

    def close_connection(self):
        """Close the client connection and the server socket."""
        if self.connection:
            self.connection.close()
        self.server_socket.close()
        print("Connection closed.")

if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.start_server()