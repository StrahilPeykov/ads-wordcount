#!/usr/bin/env python3
"""
Load Balancer Testing Script
Phase 3: Test different load balancing algorithms
"""

import rpyc
import time
from collections import defaultdict


def test_algorithm(algorithm_name, num_requests=20):
    """
    Test a specific load balancing algorithm.
    
    Args:
        algorithm_name: Name of the algorithm being tested
        num_requests: Number of test requests to send
    """
    print("\n" + "="*70)
    print(f"TESTING: {algorithm_name.upper()}")
    print("="*70 + "\n")
    
    try:
        # Connect to load balancer
        conn = rpyc.connect('load_balancer', 18860, config={'allow_public_attrs': True})
        print("✓ Connected to load balancer\n")
        
        # Get load balancer info
        lb_info = conn.root.get_server_info()
        print(f"Load Balancer Info: {lb_info}\n")
        
        # Test keywords
        keywords = ['shrek', 'donkey', 'dragon', 'ogre', 'fairy', 'castle', 'princess', 'tower']
        
        server_counts = defaultdict(int)
        latencies = []
        cache_hits = 0
        
        print("Sending requests...\n")
        
        for i in range(num_requests):
            keyword = keywords[i % len(keywords)]
            
            start = time.time()
            result = conn.root.count_word(keyword, 'shrek.txt')
            latency = (time.time() - start) * 1000
            
            server = result.get('server', 'unknown')
            cached = result.get('cached', False)
            count = result.get('count', 0)
            
            server_counts[server] += 1
            latencies.append(latency)
            if cached:
                cache_hits += 1
            
            status = "HIT " if cached else "MISS"
            print(f"  Request {i+1:2d}: '{keyword:10s}' → {server:10s} | {status} | {latency:6.2f} ms")
        
        # Print statistics
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        print(f"\nTotal Requests:  {num_requests}")
        print(f"Cache Hits:      {cache_hits}")
        print(f"Cache Misses:    {num_requests - cache_hits}")
        print(f"Avg Latency:     {sum(latencies)/len(latencies):.2f} ms")
        print(f"Min Latency:     {min(latencies):.2f} ms")
        print(f"Max Latency:     {max(latencies):.2f} ms")
        
        print("\nServer Distribution:")
        for server in sorted(server_counts.keys()):
            count = server_counts[server]
            pct = (count / num_requests) * 100
            bar = "█" * int(pct / 2)
            print(f"  {server:10s}: {count:2d} requests ({pct:5.1f}%) {bar}")
        
        # Calculate distribution variance (perfect would be 33.33% each for 3 servers)
        expected = num_requests / len(server_counts)
        variance = sum((count - expected) ** 2 for count in server_counts.values()) / len(server_counts)
        print(f"\nDistribution Variance: {variance:.2f} (lower is better, 0 = perfect)")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("="*70)


def main():
    """Main testing function."""
    print("\n" + "="*70)
    print("LOAD BALANCER ALGORITHM COMPARISON - PHASE 3")
    print("="*70)
    
    print("\nWaiting for services to be ready...")
    time.sleep(3)
    
    # Test with current algorithm (set in docker-compose.yml)
    print("\nTesting current load balancing algorithm...")
    test_algorithm("Current Algorithm", num_requests=20)
    
    print("\n\n" + "="*70)
    print("TO TEST DIFFERENT ALGORITHMS:")
    print("="*70)
    print("\n1. Stop the containers: docker-compose down")
    print("\n2. Edit docker-compose.yml and change:")
    print("     environment:")
    print("       - LB_ALGORITHM=round_robin")
    print("   to:")
    print("     environment:")
    print("       - LB_ALGORITHM=least_connections")
    print("\n3. Restart: docker-compose up")
    print("\n4. Run this test again")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()