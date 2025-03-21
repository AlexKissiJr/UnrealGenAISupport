import unreal
import socket
import threading
import json
import traceback
import time
from queue import Queue

# Set up logging
log = unreal.log
display = lambda msg: log(msg)
warning = lambda msg: log(msg, target_name="LogPythonSocket", verbosity=unreal.LogVerbosity.WARNING)
error = lambda msg: log(msg, target_name="LogPythonSocket", verbosity=unreal.LogVerbosity.ERROR)

# Command dispatcher to handle different commands
class CommandDispatcher:
    def __init__(self):
        self.commands = {}
        self.register_default_commands()
    
    def register_command(self, command_name, handler_function):
        self.commands[command_name.lower()] = handler_function
    
    def register_default_commands(self):
        # Register some basic commands
        self.register_command("ping", self.ping_handler)
        self.register_command("exec", self.exec_handler)
        
    def process_command(self, command_data):
        try:
            if not isinstance(command_data, dict):
                return {"error": "Invalid command format, expected JSON object"}
            
            command = command_data.get("command", "").lower()
            
            if not command:
                return {"error": "No command specified"}
            
            if command not in self.commands:
                return {"error": f"Unknown command: {command}"}
            
            return self.commands[command](command_data)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}\n{traceback.format_exc()}"
            error(error_msg)
            return {"error": error_msg}
    
    # Command handlers
    def ping_handler(self, data):
        return {"result": "pong", "timestamp": time.time()}
    
    def exec_handler(self, data):
        code = data.get("code", "")
        if not code:
            return {"error": "No code provided to execute"}
        
        try:
            # Execute the Python code in the Unreal context
            result = {}
            exec(f"global exec_result\nexec_result = {code}", globals())
            result["result"] = globals().get("exec_result", None)
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}\n{traceback.format_exc()}"
            error(error_msg)
            return {"error": error_msg}

# Global state
dispatcher = CommandDispatcher()
main_thread_queue = Queue()
server_thread = None
server_socket = None
running = False

# Function to handle individual client connections
def handle_client(client_socket, client_address):
    display(f"Client connected: {client_address}")
    try:
        while running:
            try:
                # Receive data from client
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Decode and parse JSON
                try:
                    command_data = json.loads(data.decode('utf-8'))
                    display(f"Received command: {command_data}")
                    
                    # Process command on main thread to ensure thread safety
                    result_future = unreal.PythonCallableResult()
                    unreal.PythonCallable.call_on_game_thread(lambda: dispatcher.process_command(command_data), result_future)
                    
                    # Wait for result and send back
                    response = result_future.get()
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    error(f"Invalid JSON received: {data.decode('utf-8')}")
                    client_socket.sendall(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
                
            except socket.timeout:
                # Socket timeout, check if we're still running
                continue
            except Exception as e:
                error(f"Error handling client: {str(e)}")
                break
                
    finally:
        client_socket.close()
        display(f"Client disconnected: {client_address}")

# Function to run the server in a background thread
def run_server():
    global running, server_socket
    
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to port 9877
        server_socket.bind(('0.0.0.0', 9877))
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # 1 second timeout for accepting connections
        
        display("Socket server listening on 0.0.0.0:9877")
        
        while running:
            try:
                client_socket, client_address = server_socket.accept()
                client_socket.settimeout(1.0)  # 1 second timeout for receiving data
                
                # Start a new thread to handle this client
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address),
                    name=f"SocketClient-{client_address[0]}:{client_address[1]}"
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                # Socket timeout, continue and check if we're still running
                continue
            except Exception as e:
                if running:  # Only log if we're still supposed to be running
                    error(f"Error accepting connection: {str(e)}")
                break
                
    except Exception as e:
        error(f"Server error: {str(e)}")
    finally:
        if server_socket:
            server_socket.close()
            server_socket = None
        display("Socket server stopped")

# Start the server
def start_server():
    global running, server_thread
    
    if running:
        warning("Server already running")
        return
    
    running = True
    server_thread = threading.Thread(target=run_server, name="SocketServerThread")
    server_thread.daemon = True
    server_thread.start()
    
    display("Socket server started")

# Stop the server
def stop_server():
    global running, server_thread, server_socket
    
    if not running:
        warning("Server not running")
        return
    
    running = False
    
    # Close the server socket to unblock accept()
    if server_socket:
        try:
            server_socket.close()
        except:
            pass
    
    # Wait for server thread to terminate
    if server_thread and server_thread.is_alive():
        server_thread.join(2.0)  # Wait up to 2 seconds
    
    server_thread = None
    display("Socket server stopped")

# Auto-start the server when the module is imported
start_server()