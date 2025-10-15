#!/usr/bin/env python3
"""
Load Balancer for Word Count Service
Phase 3: Load balancing implementation with multiple algorithms
Phase 4: Add fault tolerance and health monitoring
"""

import asyncio
import rpyc
import os
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
        self.total_requests = 0
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class LoadBalancer:
    """
    Load balancer that distributes requests across multiple servers.
    Phase 3: Uses RPyC to forward requests (simpler than socket forwarding).
    """
    
    def __init__(self, algorithm: LoadBalancingAlgorithm):
        self.algorithm = algorithm
        self.servers: List[Server] = []
        self.current_server_index = 0
        self.connections: Dict[str, rpyc.Connection] = {}
        
    def add_server(self, host: str, port: int, name: str):
        """Add a backend server to the pool."""
        server = Server(host, port, name)
        self.servers.append(server)
        print(f"✓ Added server: {server}")
    
    def connect_to_servers(self):
        """Establish connections to all backend servers."""
        print("\nConnecting to backend servers...")
        for server in self.servers:
            try:
                conn = rpyc.connect(
                    server.host,
                    server.port,
                    config={'allow_public_attrs': True, 'sync_request_timeout': 30}
                )
                self.connections[server.name] = conn
                server.is_healthy = True
                print(f"✓ Connected to {server.name}")
            except Exception as e:
                print(f"✗ Failed to connect to {server.name}: {e}")
                server.is_healthy = False
    
    def get_next_server(self) -> Server:
        """
        Select the next server based on the load balancing algorithm.
        
        Returns:
            Server: Selected server for the next request
        """
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
    
    def forward_request(self, method: str, *args, **kwargs):
        """
        Forward a request to a backend server.
        
        Args:
            method: The RPC method name
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            The response from the backend server
        """
        server = self.get_next_server()
        server.active_connections += 1
        server.total_requests += 1
        
        try:
            conn = self.connections[server.name]
            result = getattr(conn.root, method)(*args, **kwargs)
            
            # Add load balancer info to response
            if isinstance(result, dict):
                result['load_balancer'] = 'active'
                result['algorithm'] = self.algorithm.value
            
            return result
        except Exception as e:
            print(f"✗ Error forwarding request to {server.name}: {e}")
            server.is_healthy = False
            raise
        finally:
            server.active_connections -= 1
    
    async def health_check_loop(self):
        """
        Periodically check the health of all servers.
        Phase 4: Will implement proper health monitoring.
        """
        while True:
            await asyncio.sleep(10)
            print("\n[Health Check] Checking server health...")
            for server in self.servers:
                try:
                    if server.name in self.connections:
                        conn = self.connections[server.name]
                        health = conn.root.health_check()
                        server.is_healthy = (health['status'] == 'healthy')
                        status = "✓ HEALTHY" if server.is_healthy else "✗ UNHEALTHY"
                        print(f"  {server.name}: {status} (Requests: {server.total_requests})")
                except Exception as e:
                    server.is_healthy = False
                    print(f"  {server.name}: ✗ UNHEALTHY - {e}")
    
    def print_stats(self):
        """Print load balancer statistics."""
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


class LoadBalancerService(rpyc.Service):
    """RPyC service that acts as a load balancer."""
    
    def __init__(self, load_balancer: LoadBalancer):
        super().__init__()
        self.lb = load_balancer
    
    def exposed_count_word(self, keyword, filename):
        """Forward count_word request to backend server."""
        return self.lb.forward_request('count_word', keyword, filename)
    
    def exposed_get_server_info(self):
        """Return load balancer info."""
        return {
            'type': 'load_balancer',
            'algorithm': self.lb.algorithm.value,
            'healthy_servers': sum(1 for s in self.lb.servers if s.is_healthy),
            'total_servers': len(self.lb.servers)
        }


async def main():
    """Main function to start the load balancer."""
    
    # Get algorithm from environment or use default
    algorithm_str = os.getenv('LB_ALGORITHM', 'round_robin')
    algorithm = LoadBalancingAlgorithm(algorithm_str)
    
    print("="*60)
    print("WORD COUNT LOAD BALANCER - Phase 3")
    print("="*60)
    print(f"Algorithm: {algorithm.value}")
    print()
    
    # Create load balancer
    lb = LoadBalancer(algorithm=algorithm)
    
    # Add backend servers
    lb.add_server('server1', 18861, 'server1')
    lb.add_server('server2', 18861, 'server2')
    lb.add_server('server3', 18861, 'server3')
    
    # Connect to all servers
    lb.connect_to_servers()
    
    print()
    print("="*60)
    print("Load Balancer Ready!")
    print("Listening on port 18860")
    print("="*60)
    print()
    
    # Start health check in background
    asyncio.create_task(lb.health_check_loop())
    
    # Start RPyC server
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(
        LoadBalancerService(lb),
        port=18860,
        protocol_config={'allow_public_attrs': True}
    )
    
    try:
        # Run server in a thread to allow async health checks
        await asyncio.get_event_loop().run_in_executor(None, server.start)
    except KeyboardInterrupt:
        print("\n\nShutting down load balancer...")
        lb.print_stats()


if __name__ == '__main__':
    asyncio.run(main())