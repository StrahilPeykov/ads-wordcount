#!/usr/bin/env python3
"""
Load Balancer for Word Count Service
Phase 3: Load balancing implementation with multiple algorithms
Phase 4: Add fault tolerance and health monitoring
"""

import asyncio
import socket
from typing import List, Dict
from enum import Enum


class LoadBalancingAlgorithm(Enum):
    """Supported load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"


class Server:
    """Represents a backend server."""
    
    def __init__(self, host: str, port: int, name: str):
        self.host = host
        self.port = port
        self.name = name
        self.is_healthy = True
        self.active_connections = 0
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class LoadBalancer:
    """
    Load balancer that distributes requests across multiple servers.
    Uses network sockets for efficient byte-stream forwarding.
    """
    
    def __init__(self, listen_port: int, algorithm: LoadBalancingAlgorithm):
        self.listen_port = listen_port
        self.algorithm = algorithm
        self.servers: List[Server] = []
        self.current_server_index = 0
        
    def add_server(self, host: str, port: int, name: str):
        """Add a backend server to the pool."""
        server = Server(host, port, name)
        self.servers.append(server)
        print(f"Added server: {server}")
    
    def get_next_server(self) -> Server:
        """
        Select the next server based on the load balancing algorithm.
        
        Returns:
            Server: Selected server for the next request
        """
        # TODO: Implement load balancing algorithms
        # TODO: Implement health checking
        
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin()
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections()
        else:
            return self._round_robin()
    
    def _round_robin(self) -> Server:
        """Round-robin load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            raise Exception("No healthy servers available")
        
        server = healthy_servers[self.current_server_index % len(healthy_servers)]
        self.current_server_index += 1
        return server
    
    def _least_connections(self) -> Server:
        """Least connections load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            raise Exception("No healthy servers available")
        
        return min(healthy_servers, key=lambda s: s.active_connections)
    
    async def health_check(self):
        """
        Periodically check the health of all servers.
        Phase 4: Implement health monitoring.
        """
        while True:
            # TODO: Implement health checking logic
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def handle_client(self, client_reader, client_writer):
        """
        Handle incoming client connection and forward to backend server.
        
        Args:
            client_reader: AsyncIO stream reader for client
            client_writer: AsyncIO stream writer for client
        """
        # TODO: Implement request forwarding
        # TODO: Handle connection errors and failover
        pass
    
    async def start(self):
        """Start the load balancer server."""
        # TODO: Implement async server using asyncio
        print(f"Load Balancer starting on port {self.listen_port}")
        print(f"Algorithm: {self.algorithm.value}")
        print(f"Backend servers: {len(self.servers)}")
        
        # Start health checking in background
        asyncio.create_task(self.health_check())
        
        # TODO: Start accepting connections
        print("Load Balancer ready!")


if __name__ == '__main__':
    # Example configuration for Phase 3
    lb = LoadBalancer(
        listen_port=18860,
        algorithm=LoadBalancingAlgorithm.ROUND_ROBIN
    )
    
    # Add backend servers
    lb.add_server('server', 18861, 'server1')
    lb.add_server('server2', 18861, 'server2')
    lb.add_server('server3', 18861, 'server3')
    
    # Start the load balancer
    try:
        asyncio.run(lb.start())
    except KeyboardInterrupt:
        print("\nShutting down load balancer...")