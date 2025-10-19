#!/usr/bin/env python3
"""
Word Count Client
Phase 4: Added fault tolerance
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
            print("[Client] Connected successfully!")
            return True
        except Exception as e:
            print(f"[Client] Connection failed: {e}")
            return False
    
    def count_word(self, keyword, filename):
        """
        Request word count from the server and measure latency.
        """
        if not self.connection:
            print("Not connected to server!")
            return None, None
        
        try:
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
        if self.connection:
            self.connection.close()
            print("\nConnection closed.")


def run_count():
    """
    Run function to test the word count service with load balancing.
    """
    client = WordCountClient()
    
    if not client.connect():
        return
    
    lb_info = client.get_server_info()
    if lb_info:
        print(f"Connected to: {lb_info}")
    
    test_queries = [
        ('shrek', 'shrek.txt'),
        ('donkey', 'shrek.txt'),
        ('dragon', 'shrek.txt'),
        ('ogre', 'shrek.txt'),
        ('princess', 'shrek.txt'),
        ('castle', 'shrek.txt'),
        ('the', 'shrek.txt'),
        ('shrek', 'shrek.txt'),
        ('fairy', 'shrek.txt'),
        ('tower', 'shrek.txt'),
    ]
    
    print("\n" + "="*70)
    print("PHASE 4- FAULT TOLERANCE TEST")
    print("="*70)
    print("Running test queries...\n")
    
    results = []
    server_distribution = {}
    
    for i, (keyword, filename) in enumerate(test_queries, 1):
        print(f"Request {i:2d}: '{keyword:10s}' in '{filename}'")
        result, latency = client.count_word(keyword, filename)
        
        if result is not None:
            count = result.get('count', 'N/A')
            server = result.get('server', 'unknown')
            cached = result.get('cached', False)
            cache_status = "HIT " if cached else "MISS"
            
            server_distribution[server] = server_distribution.get(server, 0) + 1
            
            print(f"  → {server:10s} | Count: {count:3d} | {cache_status:4s} | {latency:6.2f} ms")
            
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
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    
    total_requests = len(results)
    cache_hits = sum(1 for r in results if r['cached'])
    avg_latency = sum(r['latency'] for r in results) / total_requests if results else 0
    
    print(f"\nTotal Requests: {total_requests}")
    print(f"Cache Hits:     {cache_hits}")
    print(f"Cache Misses:   {total_requests - cache_hits}")
    print(f"Avg Latency:    {avg_latency:.2f} ms")
    
    print("\nServer Distribution:")
    for server, count in sorted(server_distribution.items()):
        percentage = (count / total_requests * 100) if total_requests > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"  {server:10s}: {count:2d} requests ({percentage:5.1f}%) {bar}")
    
    print("="*70)
    
    client.close()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("WORD COUNT CLIENT - PHASE 4")
    print("="*70 + "\n")
    
    time.sleep(3)
    run_count()
