#!/usr/bin/env python3
"""
Load Balancer for Word Count Service
"""

import asyncio
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
        self.lock = asyncio.Lock()
    
    async def increment_connections(self):
        async with self.lock:
            self.active_connections += 1
            self.total_requests += 1
    
    async def decrement_connections(self):
        async with self.lock:
            self.active_connections -= 1
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class LoadBalancer:
    def __init__(self, algorithm: LoadBalancingAlgorithm, listen_port: int = 18860):
        self.algorithm = algorithm
        self.listen_port = listen_port
        self.servers: List[Server] = []
        self.current_server_index = 0
        self.lock = asyncio.Lock()
        self.running = True
        
    def add_server(self, host: str, port: int, name: str):
        server = Server(host, port, name)
        self.servers.append(server)
        print(f"✓ Added server: {server}")
    
    async def get_next_server(self) -> Optional[Server]:
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return await self._round_robin()
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return await self._least_connections()
        else:
            return await self._round_robin()
    
    async def _round_robin(self) -> Optional[Server]:
        """Round-robin load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        
        async with self.lock:
            server = healthy_servers[self.current_server_index % len(healthy_servers)]
            self.current_server_index += 1
            # Increment connection count immediately
            await server.increment_connections()
        return server
    
    async def _least_connections(self) -> Optional[Server]:
        """Least connections load balancing."""
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        
        async with self.lock:
            # Find server with minimum active connections
            server = min(healthy_servers, key=lambda s: s.active_connections)
            # Increment immediately to reserve this server
            await server.increment_connections()
        return server
    
    async def check_server_health(self, server: Server) -> bool:
        """
        Check if a server is healthy by attempting to connect.
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(server.host, server.port),
                timeout=1.0 
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    async def health_check_loop(self):
        print("[Health Monitor] Starting health check loop...")
        
        while self.running:
            health_results = await asyncio.gather(
                *[self.check_server_health(server) for server in self.servers],
                return_exceptions=True
            )
            status_changes = []
            for server, is_healthy in zip(self.servers, health_results):
                was_healthy = server.is_healthy
                server.is_healthy = is_healthy if isinstance(is_healthy, bool) else False
                server.last_health_check = time.time()
                
                if was_healthy and not server.is_healthy:
                    status_changes.append(f"  X {server.name} FAILED")
                elif not was_healthy and server.is_healthy:
                    status_changes.append(f"  + {server.name} RECOVERED")
            
            if status_changes:
                print("\n[Health Check] Status Changes:")
                for change in status_changes:
                    print(change)
            
            print(f"\n[Health Check]| ", end="")
            for server in self.servers:
                status = "alive" if server.is_healthy else "dead"
                print(f"{server.name}: {status} - {server.total_requests} requests | ", end="")
            print()  

            await asyncio.sleep(3)  # Check every 3 seconds

    async def forward_data(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str):
        """
        Forward data from source to destination stream.
        """
        try:
            while self.running:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        """
        Handle a client connection by forwarding to a backend server.
        """
        server = None
        server_reader = None
        server_writer = None
        client_address = client_writer.get_extra_info('peername')
        
        try:
            server = await self.get_next_server()
            if not server:
                print(f"✗ No healthy servers available for {client_address}")
                client_writer.close()
                await client_writer.wait_closed()
                return
            
            print(f"→ Forwarding {client_address} to {server.name}")
            
            # Connect to backend server
            server_reader, server_writer = await asyncio.wait_for(
                asyncio.open_connection(server.host, server.port),
                timeout=30.0
            )
            
            # Forward data bidirectionally 
            await asyncio.gather(
                self.forward_data(client_reader, server_writer, "client→server"),
                self.forward_data(server_reader, client_writer, "server→client"),
                return_exceptions=True
            )
            
        except Exception as e:
            print(f"✗ Error handling client {client_address}: {e}")
            if server:
                server.is_healthy = False
        finally:
            if server:
                await server.decrement_connections()
            if client_writer:
                try:
                    client_writer.close()
                    await client_writer.wait_closed()
                except:
                    pass
            if server_writer:
                try:
                    server_writer.close()
                    await server_writer.wait_closed()
                except:
                    pass
    
    async def start(self):
        """Start the load balancer server."""
        
        # Start health check task
        health_task = asyncio.create_task(self.health_check_loop())
        
        # Create server
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.listen_port
        )
        
        print()
        print("="*60)
        print("Load Balancer Ready!")
        print(f"Listening on port {self.listen_port}")
        print("="*60)
        print()
        
        try:
            async with server:
                await server.serve_forever()
                
        except KeyboardInterrupt:
            print("\n\nShutting down load balancer...")
            self.print_stats()
        finally:
            self.running = False
            health_task.cancel()
            try:
                await health_task
            except asyncio.CancelledError:
                pass
    
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


async def main():
    """Main function to start the load balancer."""
    
    # Get algorithm from environment or use default
    algorithm_str = os.getenv('LB_ALGORITHM', 'round_robin')
    algorithm = LoadBalancingAlgorithm(algorithm_str)
    
    print("="*60)
    print("WORD COUNT LOAD BALANCER - Phase 4")
    print("="*60)
    print(f"Algorithm: {algorithm.value}")
    print()
    
    lb = LoadBalancer(algorithm=algorithm, listen_port=18860)
    
    lb.add_server('server1', 18861, 'server1')
    lb.add_server('server2', 18861, 'server2')
    lb.add_server('server3', 18861, 'server3')
    
    await lb.start()


if __name__ == '__main__':
    asyncio.run(main())