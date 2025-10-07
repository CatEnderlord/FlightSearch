import subprocess
import sys
import time
import os
import signal
import atexit

def run_server_client():
    """Run both server and client processes simultaneously."""
    # Start the server process
    print("Starting server...")
    server_process = subprocess.Popen([sys.executable, "server.py"], 
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
    
    # Give the server a moment to initialize
    time.sleep(1)
    
    # Check if server started successfully
    if server_process.poll() is not None:
        print("Server failed to start. Error:")
        print(server_process.stderr.read())
        return
    
    print("Server started successfully!")
    
    # Start the client process
    print("Starting client...")
    client_process = subprocess.Popen([sys.executable, "client.py"])
    
    # Function to clean up processes on exit
    def cleanup():
        print("\nShutting down...")
        if server_process and server_process.poll() is None:
            print("Terminating server...")
            if os.name == 'nt':  # Windows
                server_process.terminate()
            else:  # Unix/Linux/Mac
                os.kill(server_process.pid, signal.SIGTERM)
        
        if client_process and client_process.poll() is None:
            print("Client terminated.")
    
    # Register the cleanup function to be called on normal program termination
    atexit.register(cleanup)
    
    try:
        # Wait for the client to finish (when user closes the GUI)
        client_process.wait()
        print("Client closed.")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    finally:
        cleanup()
        
if __name__ == "__main__":
    print("Starting Hello World Chat Application")
    print("-------------------------------------")
    print("Press Ctrl+C to terminate both applications")
    run_server_client()
    print("Both applications terminated.")