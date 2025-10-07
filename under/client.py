import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5001):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Hello World Chat")
        self.chat_frame = None
        self.chat_area = None
        self.message_text = None
        self.setup_gui()
        
    def setup_gui(self):
        """Set up the GUI for chat interface."""
        # Create main chat frame
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(padx=10, pady=10)
        
        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, state=tk.DISABLED, 
            height=15, width=40, font=("Arial", 12)
        )
        self.chat_area.pack(padx=5, pady=5)
        
        # Message input field
        self.message_text = tk.Entry(self.chat_frame, font=("Arial", 12), width=30)
        self.message_text.pack(side=tk.LEFT, padx=5, pady=5)
        self.message_text.bind("<Return>", lambda event: self.send_message())
        
        # Send button
        send_button = tk.Button(self.chat_frame, text="Send", command=self.send_message, font=("Arial", 12))
        send_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Connect to server when GUI is ready
        self.root.after(100, self.connect_server)
        
    def update_chat(self, message, is_self=False):
        """Update the chat display with a new message."""
        self.chat_area.config(state=tk.NORMAL)
        sender = "You" if is_self else "Server"
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
        
    def connect_server(self):
        """Connect to the chat server."""
        try:
            self.client_socket.connect((self.host, self.port))
            threading.Thread(target=self.receive_message, daemon=True).start()
            self.update_chat("Connected to server", is_self=False)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Unable to connect to server: {e}")
            self.root.destroy()
            
    def receive_message(self):
        """Receive messages from the server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.update_chat(message)
                else:
                    # Connection closed by server
                    self.update_chat("Server disconnected")
                    break
            except:
                # Connection error
                messagebox.showerror("Connection Error", "Lost connection to server")
                break
                
    def send_message(self):
        """Send user message to the server."""
        message = self.message_text.get().strip()
        if message:
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.update_chat(message, is_self=True)
                self.message_text.delete(0, tk.END)
                
                if message.lower() == "bye":
                    self.client_socket.close()
                    self.root.destroy()
            except:
                messagebox.showerror("Send Error", "Failed to send message")
                
    def run(self):
        """Run the client application."""
        self.root.mainloop()
        
if __name__ == "__main__":
    client = ChatClient()
    client.run()