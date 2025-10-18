#!/usr/bin/env python3
"""
Load Balancer for Word Count Service
"""

import socket
import threading
import os
import time
from typing import List, Optional
from enum import Enum


class LoadBalancingAlgorithm(Enum):
    """Supported load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"


class Server:
    def __init__(self, host: str, port: int, name: str):
        self.host = host
        self.port = port
        self.name = name
        self.is_healthy = True
        self.active_connections = 0
        self.total_requests = 0
        self.last_health_check = time.time()
        self.lock = threading.Lock()
    
    def increment_connections(self):
        with self.lock:
            self.active_connections += 1
            self.total_requests += 1
    
    def decrement_connections(self):
        with self.lock:
            self.active_connections -= 1
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class LoadBalancer:
    def __init__(self, algorithm: LoadBalancingAlgorithm, listen_port: int = 18860):
        self.algorithm = algorithm
        self.listen_port = listen_port
        self.servers: List[Server] = []
        self.current_server_index = 0
        self.lock = threading.Lock()
        self.running = True
        
    def add_server(self, host: str, port: int, name: str):
        server = Server(host, port, name)
        self.servers.append(server)
        print(f"✓ Added server: {server}")
    
    def get_next_server(self) -> Optional[Server]:
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin()
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections()
        else:
            return self._round_robin()
    
    def _round_robin(self) -> Optional[Server]:
        """Round-robin load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        
        with self.lock:
            server = healthy_servers[self.current_server_index % len(healthy_servers)]
            self.current_server_index += 1
        return server
    
    def _least_connections(self) -> Optional[Server]:
        """Least connections load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        return min(healthy_servers, key=lambda s: s.active_connections)
    
    def check_server_health(self, server: Server) -> bool:
        """
        Check if a server is healthy by attempting to connect.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((server.host, server.port))
            sock.close()
            return True
        except Exception:
            return False
    
    def health_check_loop(self):
        print("[Health Monitor] Starting health check loop...")
        
        while self.running:
            time.sleep(3)  # Check every 3 seconds
            print("\n[Health Check] Checking server health...")
            
            for server in self.servers:
                was_healthy = server.is_healthy
                is_healthy = self.check_server_health(server)
                server.is_healthy = is_healthy
                server.last_health_check = time.time()
                
                if was_healthy and not is_healthy:
                    print(f"  {server.name}: ✗ FAILED")
                elif not was_healthy and is_healthy:
                    print(f"  {server.name}: ✓ RECOVERED")
                else:
                    status = "✓ HEALTHY" if is_healthy else "✗ UNHEALTHY"
                    print(f"  {server.name}: {status} (Requests: {server.total_requests})")
    
    def forward_data(self, source: socket.socket, destination: socket.socket, direction: str):
        """
        Forward data from source socket to destination socket.
        """
        try:
            while self.running:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)
        except Exception:
            pass
        finally:
            try:
                source.shutdown(socket.SHUT_RD)
            except:
                pass
            try:
                destination.shutdown(socket.SHUT_WR)
            except:
                pass
    
    def handle_client(self, client_socket: socket.socket, client_address):
        """
        Handle a client connection by forwarding to a backend server.
        """
        server = None
        server_socket = None
        
        try:
            server = self.get_next_server()
            if not server:
                print(f"✗ No healthy servers available for {client_address}")
                client_socket.close()
                return
            
            server.increment_connections()
            print(f"→ Forwarding {client_address} to {server.name}")
            
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(30)
            server_socket.connect((server.host, server.port))
            
            # Forward data bidirectionally
            client_to_server = threading.Thread(
                target=self.forward_data,
                args=(client_socket, server_socket, "client→server"),
                daemon=True
            )
            server_to_client = threading.Thread(
                target=self.forward_data,
                args=(server_socket, client_socket, "server→client"),
                daemon=True
            )
            
            client_to_server.start()
            server_to_client.start()
            client_to_server.join()
            server_to_client.join()
            
        except Exception as e:
            print(f"✗ Error handling client {client_address}: {e}")
            if server:
                server.is_healthy = False
        finally:
            if server:
                server.decrement_connections()
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass
    
    def start(self):
        """Start the load balancer server."""
        
        # Start health check thread
        health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        health_thread.start()
        
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(('0.0.0.0', self.listen_port))
        listen_socket.listen(10)
        
        print()
        print("="*60)
        print("Load Balancer Ready!")
        print(f"Listening on port {self.listen_port}")
        print("="*60)
        print()
        
        try:
            while self.running:
                client_socket, client_address = listen_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n\nShutting down load balancer...")
            self.print_stats()
        finally:
            self.running = False
            listen_socket.close()
    
    def print_stats(self):
        print("\n" + "="*60)
        print("LOAD BALANCER STATISTICS")
        print("="*60)
        print(f"Algorithm: {self.algorithm.value}")
        print(f"Total Servers: {len(self.servers)}")
        print(f"Healthy Servers: {sum(1 for s in self.servers if s.is_healthy)}")
        print("\nPer-Server Stats:")
        for server in self.servers:
            status = "✓" if server.is_healthy else "✗"
            print(f"  {status} {server.name:10} | Requests: {server.total_requests:3} | Active: {server.active_connections}")
        print("="*60 + "\n")


def main():
    """Main function to start the load balancer."""
    
    # Get algorithm from environment or use default
    algorithm_str = os.getenv('LB_ALGORITHM', 'round_robin')
    algorithm = LoadBalancingAlgorithm(algorithm_str)
    
    print("="*60)
    print("WORD COUNT LOAD BALANCER - Phase 3")
    print("="*60)
    print(f"Algorithm: {algorithm.value}")
    print()
    
    lb = LoadBalancer(algorithm=algorithm, listen_port=18860)
    
    lb.add_server('server1', 18861, 'server1')
    lb.add_server('server2', 18861, 'server2')
    lb.add_server('server3', 18861, 'server3')
    
    lb.start()


if __name__ == '__main__':
    main()