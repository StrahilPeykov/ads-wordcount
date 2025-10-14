#!/usr/bin/env python3
"""
Word Count Server
Phase 2: Basic RPyC server implementation with Redis caching
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
        
    def exposed_count_word(self, keyword, filename):
        """
        Count occurrences of a keyword in the specified text file.
        
        Args:
            keyword (str): The word to count
            filename (str): Name of the text file
            
        Returns:
            int: Number of occurrences of the keyword
        """
        # TODO: Implement caching logic with Redis
        # TODO: Implement word counting logic
        # TODO: Measure and return execution time
        
        cache_key = f"{filename}:{keyword}"
        
        # Check cache first
        cached_result = self.redis_client.get(cache_key)
        if cached_result is not None:
            print(f"Cache hit for {cache_key}")
            return int(cached_result)
        
        print(f"Cache miss for {cache_key}, computing...")
        
        # Read file and count occurrences
        file_path = self.text_directory / filename
        if not file_path.exists():
            return -1  # File not found
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().lower()
            count = text.count(keyword.lower())
        
        # Cache the result
        self.redis_client.set(cache_key, count)
        
        return count
    
    def exposed_get_server_info(self):
        """
        Return server information (useful for load balancing demonstration).
        
        Returns:
            dict: Server information
        """
        return {
            'hostname': os.getenv('HOSTNAME', 'unknown'),
            'container_name': 'word_count_server'
        }


if __name__ == '__main__':
    # Start the RPyC server
    port = 18861
    print(f"Starting Word Count Server on port {port}...")
    
    server = ThreadedServer(
        WordCountService,
        port=port,
        protocol_config={'allow_public_attrs': True}
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")