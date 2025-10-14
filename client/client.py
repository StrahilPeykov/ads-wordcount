#!/usr/bin/env python3
"""
Word Count Client
Phase 2: Basic RPyC client implementation
"""

import rpyc
import time


class WordCountClient:
    """
    Client for the Word Count Service.
    """
    
    def __init__(self, host='server', port=18861):
        """
        Initialize connection to the word count server.
        
        Args:
            host (str): Server hostname
            port (int): Server port
        """
        self.host = host
        self.port = port
        self.connection = None
        
    def connect(self):
        """Establish connection to the server."""
        try:
            print(f"Connecting to server at {self.host}:{self.port}...")
            self.connection = rpyc.connect(
                self.host,
                self.port,
                config={'allow_public_attrs': True}
            )
            print("Connected successfully!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def count_word(self, keyword, filename):
        """
        Request word count from the server and measure latency.
        
        Args:
            keyword (str): The word to count
            filename (str): Name of the text file
            
        Returns:
            tuple: (count, latency_ms)
        """
        if not self.connection:
            print("Not connected to server!")
            return None, None
        
        try:
            # Measure execution latency
            start_time = time.time()
            
            count = self.connection.root.count_word(keyword, filename)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            return count, latency_ms
            
        except Exception as e:
            print(f"Error during request: {e}")
            return None, None
    
    def get_server_info(self):
        """Get information about the connected server."""
        if not self.connection:
            return None
        
        try:
            return self.connection.root.get_server_info()
        except Exception as e:
            print(f"Error getting server info: {e}")
            return None
    
    def close(self):
        """Close the connection to the server."""
        if self.connection:
            self.connection.close()
            print("Connection closed.")


def run_demo():
    """
    Demo function to test the word count service.
    """
    client = WordCountClient()
    
    if not client.connect():
        return
    
    # Get server info
    server_info = client.get_server_info()
    if server_info:
        print(f"Connected to server: {server_info}")
    
    # Example queries using Shrek movie script
    test_queries = [
        ('shrek', 'shrek.txt'),
        ('donkey', 'shrek.txt'),
        ('dragon', 'shrek.txt'),
        ('shrek', 'shrek.txt'),  # Should hit cache
        ('ogre', 'shrek.txt'),
    ]
    
    print("\n" + "="*60)
    print("Running test queries...")
    print("="*60 + "\n")
    
    for i, (keyword, filename) in enumerate(test_queries, 1):
        print(f"Request {i}: Counting '{keyword}' in '{filename}'")
        count, latency = client.count_word(keyword, filename)
        
        if count is not None:
            print(f"  Result: {count} occurrences")
            print(f"  Latency: {latency:.2f} ms")
        else:
            print("  Request failed!")
        print()
    
    client.close()


if __name__ == '__main__':
    print("Word Count Client - Phase 2")
    print("="*60)
    
    # Wait a bit for server to be ready
    time.sleep(2)
    
    run_demo()