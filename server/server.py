#!/usr/bin/env python3
"""
Word Count Server
Phase 3: Added load balancing
"""

import rpyc
from rpyc.utils.server import ThreadedServer
import redis
import os
from pathlib import Path


class WordCountService(rpyc.Service):
    """
    RPyC service for counting word occurrences in text files.
    """
    
    def __init__(self):
        super().__init__()
        # Connect to Redis
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        self.text_directory = Path('/app/texts')
        self.server_name = os.getenv('SERVER_NAME', 'unknown_server')
        self.request_count = 0
        
    def exposed_count_word(self, keyword, filename):
        """
        Count occurrences of a keyword in the specified text file.
        """
        self.request_count += 1
        cache_key = f"{filename}:{keyword}"
        
        # Check cache first
        cached_result = self.redis_client.get(cache_key)
        if cached_result is not None:
            print(f"[{self.server_name}] Cache HIT for '{keyword}' (Request #{self.request_count})")
            return {
                'count': int(cached_result),
                'server': self.server_name,
                'cached': True,
                'request_number': self.request_count
            }
        
        print(f"[{self.server_name}] Cache MISS for '{keyword}', computing... (Request #{self.request_count})")
        
        # Read file and count occurrences
        file_path = self.text_directory / filename
        if not file_path.exists():
            return {
                'count': -1,
                'server': self.server_name,
                'cached': False,
                'error': 'File not found',
                'request_number': self.request_count
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().lower()
            count = text.count(keyword.lower())
        
        # Cache the result
        self.redis_client.set(cache_key, count)
        
        return {
            'count': count,
            'server': self.server_name,
            'cached': False,
            'request_number': self.request_count
        }
    
    def exposed_get_server_info(self):
        """
        Return server information (useful for load balancing demonstration).
        """
        return {
            'server_name': self.server_name,
            'hostname': os.getenv('HOSTNAME', 'unknown'),
            'request_count': self.request_count
        }
    
    def exposed_health_check(self):
        """
        Health check endpoint for load balancer.
        """
        try:
            # Check Redis connection
            self.redis_client.ping()
            return {
                'status': 'healthy',
                'server': self.server_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'server': self.server_name,
                'error': str(e)
            }


if __name__ == '__main__':
    # Start the RPyC server
    port = int(os.getenv('SERVER_PORT', 18861))
    server_name = os.getenv('SERVER_NAME', 'unknown_server')
    
    print(f"Starting Word Count Server '{server_name}' on port {port}...")
    
    server = ThreadedServer(
        WordCountService,
        port=port,
        protocol_config={'allow_public_attrs': True}
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print(f"\nShutting down server '{server_name}'...")