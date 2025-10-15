#!/usr/bin/env python3
"""
Word Count Client
Phase 2: Basic RPyC client implementation
Phase 3: Updated to connect to load balancer and show server distribution
"""

import rpyc
import time


class WordCountClient:
    """
    Client for the Word Count Service.
    """
    
    def __init__(self, host='load_balancer', port=18860):
        """
        Initialize connection to the word count server/load balancer.
        
        Args:
            host (str): Server/Load Balancer hostname
            port (int): Server/Load Balancer port
        """
        self.host = host
        self.port = port
        self.connection = None
        
    def connect(self):
        """Establish connection to the server."""
        try:
            print(f"Connecting to load balancer at {self.host}:{self.port}...")
            self.connection = rpyc.connect(
                self.host,
                self.port,
                config={'allow_public_attrs': True}
            )
            print("✓ Connected successfully!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def count_word(self, keyword, filename):
        """
        Request word count from the server and measure latency.
        
        Args:
            keyword (str): The word to count
            filename (str): Name of the text file
            
        Returns:
            tuple: (result_dict, latency_ms)
        """
        if not self.connection:
            print("Not connected to server!")
            return None, None
        
        try:
            # Measure execution latency
            start_time = time.time()
            
            result = self.connection.root.count_word(keyword, filename)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            return result, latency_ms
            
        except Exception as e:
            print(f"Error during request: {e}")
            return None, None
    
    def get_server_info(self):
        """Get information about the connected server/load balancer."""
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
            print("\nConnection closed.")


def run_demo():
    """
    Demo function to test the word count service with load balancing.
    """
    client = WordCountClient()
    
    if not client.connect():
        return
    
    # Get load balancer info
    lb_info = client.get_server_info()
    if lb_info:
        print(f"Connected to: {lb_info}")
    
    # Phase 3: Test queries to demonstrate load balancing
    test_queries = [
        ('shrek', 'shrek.txt'),
        ('donkey', 'shrek.txt'),
        ('dragon', 'shrek.txt'),
        ('ogre', 'shrek.txt'),
        ('princess', 'shrek.txt'),
        ('castle', 'shrek.txt'),
        ('the', 'shrek.txt'),
        ('shrek', 'shrek.txt'),  # Cache hit test
        ('fairy', 'shrek.txt'),
        ('tower', 'shrek.txt'),
    ]
    
    print("\n" + "="*70)
    print("PHASE 3 - LOAD BALANCING TEST")
    print("="*70)
    print("Running test queries to demonstrate load distribution...\n")
    
    results = []
    server_distribution = {}
    
    for i, (keyword, filename) in enumerate(test_queries, 1):
        print(f"Request {i:2d}: Counting '{keyword:10s}' in '{filename}'")
        result, latency = client.count_word(keyword, filename)
        
        if result is not None:
            count = result.get('count', 'N/A')
            server = result.get('server', 'unknown')
            cached = result.get('cached', False)
            cache_status = "CACHE HIT" if cached else "CACHE MISS"
            
            # Track server distribution
            server_distribution[server] = server_distribution.get(server, 0) + 1
            
            print(f"  → Server: {server:10s} | Count: {count:3d} | {cache_status:11s} | Latency: {latency:6.2f} ms")
            
            results.append({
                'request': i,
                'keyword': keyword,
                'count': count,
                'server': server,
                'cached': cached,
                'latency': latency
            })
        else:
            print("  → Request failed!")
        print()
    
    # Print summary statistics
    print("="*70)
    print("LOAD DISTRIBUTION SUMMARY")
    print("="*70)
    
    total_requests = len(results)
    cache_hits = sum(1 for r in results if r['cached'])
    cache_misses = total_requests - cache_hits
    avg_latency = sum(r['latency'] for r in results) / total_requests if results else 0
    
    print(f"\nTotal Requests: {total_requests}")
    print(f"Cache Hits:     {cache_hits}")
    print(f"Cache Misses:   {cache_misses}")
    print(f"Avg Latency:    {avg_latency:.2f} ms")
    
    print("\nRequests per Server:")
    for server, count in sorted(server_distribution.items()):
        percentage = (count / total_requests * 100) if total_requests > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"  {server:10s}: {count:2d} requests ({percentage:5.1f}%) {bar}")
    
    print("="*70)
    
    client.close()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("WORD COUNT CLIENT - PHASE 3")
    print("Testing Load Balancing with Multiple Servers")
    print("="*70 + "\n")
    
    # Wait a bit for servers to be ready
    time.sleep(3)
    
    run_demo()
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