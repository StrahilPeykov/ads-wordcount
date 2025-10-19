#!/usr/bin/env python3
"""
Load Balancer Testing Script
Phase 4: Added fault tolerance
"""

import rpyc
import time
import os
import sys
import redis
from collections import defaultdict


def test_algorithm(algorithm_name, num_requests=10):
    """
    Test a specific load balancing algorithm.
    Returns buffered output to prevent interleaving.
    """
    client_id = os.getenv('CLIENT_ID', 'unknown')
    client_name = f"client{client_id}"
    
    # Buffer all output
    output = []
    
    output.append("\n" + "="*70)
    output.append(f"[{client_name}] TESTING: {algorithm_name.upper()}")
    output.append("="*70 + "\n")
    
    try:
        keyword_sets = {
            '1': ['shrek', 'donkey', 'dragon', 'far', 'swamp', 'lord', 'once', 'upon', 'time', 'away'],
            '2': ['donkey', 'dragon', 'fiona', 'fairy', 'ogre', 'shrek', 'tale', 'castle', 'king', 'princess'],
            '3': ['dragon', 'fiona', 'castle', 'princess', 'tower', 'shrek', 'rescue', 'knight', 'quest', 'sword'],
            '4': ['fiona', 'castle', 'lord', 'farquaad', 'duloc', 'donkey', 'mirror', 'gingerbread', 'man', 'song'],
            '5': ['castle', 'lord', 'mirror', 'guards', 'torture', 'dragon', 'eggs', 'babies', 'parfait', 'onions']
        }
        keywords = keyword_sets.get(client_id, keyword_sets['1'])
        
        server_counts = defaultdict(int)
        latencies = []
        cache_hits = 0
        
        output.append(f"[{client_name}] Sending requests...\n")
        
        total_start_time = time.time()
        
        for i in range(num_requests):
            keyword = keywords[i % len(keywords)]
            
            # New connection per request for proper load balancing
            conn = rpyc.connect('load_balancer', 18860, config={'allow_public_attrs': True})
            
            try:
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
                output.append(f"[{client_name}] Request {i+1:2d}: '{keyword:10s}' → {server:10s} | {status} | {latency:6.2f} ms | count={count:3d}")
            finally:
                conn.close()
        
        # Calculate total elapsed time
        total_elapsed_time = (time.time() - total_start_time) * 1000  # in milliseconds
        
        # Statistics
        output.append("\n" + "="*70)
        output.append(f"[{client_name}] RESULTS")
        output.append("="*70)
        
        output.append(f"\n[{client_name}] Total Requests:  {num_requests}")
        output.append(f"[{client_name}] Cache Hits:      {cache_hits}")
        output.append(f"[{client_name}] Cache Misses:    {num_requests - cache_hits}")
        output.append(f"[{client_name}] Total Time:      {total_elapsed_time:.2f} ms")
        output.append(f"[{client_name}] Avg Latency:     {sum(latencies)/len(latencies):.2f} ms")
        output.append(f"[{client_name}] Min Latency:     {min(latencies):.2f} ms")
        output.append(f"[{client_name}] Max Latency:     {max(latencies):.2f} ms")
        
        output.append(f"\n[{client_name}] Server Distribution:")
        for server in sorted(server_counts.keys()):
            count = server_counts[server]
            pct = (count / num_requests) * 100
            bar = "█" * int(pct / 2)
            output.append(f"[{client_name}]   {server:10s}: {count:2d} requests ({pct:5.1f}%) {bar}")
        
        expected = num_requests / len(server_counts)
        variance = sum((count - expected) ** 2 for count in server_counts.values()) / len(server_counts)
        output.append(f"\n[{client_name}] Distribution Variance: {variance:.2f} (lower is better, 0 = perfect)")
        
    except Exception as e:
        output.append(f"✗ Error: {e}")
    
    output.append("="*70)
    
    return output


def main():
    client_id = os.getenv('CLIENT_ID', 'unknown')
    client_name = f"client{client_id}"
    
    # Buffer all output to prevent interleaving with other clients
    output = []
    
    output.append("\n" + "="*70)
    output.append(f"[{client_name}] LOAD BALANCER TEST - PHASE 4")
    output.append("="*70)
    
    output.append(f"\n[{client_name}] Waiting for services to be ready...")
    time.sleep(2)
    
    # Test with current algorithm
    output.append(f"\n[{client_name}] Testing current load balancing algorithm...")
    
    # Measure this client's total time
    client_start = time.time()
    test_output = test_algorithm("Current Algorithm", num_requests=10)
    client_elapsed = (time.time() - client_start) * 1000
    
    output.extend(test_output)
    
    # Store this client's time in Redis for comparison
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.rpush('test:client_times', f"{client_id}:{client_elapsed:.2f}")
        r.expire('test:client_times', 60)  # Expire after 60 seconds
        
        # If this is client5 (last one), calculate and display max time
        if client_id == '5':
            time.sleep(2)  # Give other clients time to finish
            client_times = r.lrange('test:client_times', 0, -1)
            times = {}
            for entry in client_times:
                cid, ctime = entry.split(':')
                times[cid] = float(ctime)
            
            if times:
                max_client = max(times, key=times.get)
                max_time = times[max_client]
                
                output.append("\n" + "="*70)
                output.append("OVERALL TEST SUMMARY")
                output.append("="*70)
                output.append(f"\nTotal clients: {len(times)}")
                output.append(f"Slowest client: client{max_client} ({max_time:.2f} ms)")
                output.append(f"Fastest client: client{min(times, key=times.get)} ({min(times.values()):.2f} ms)")
                output.append(f"Average time: {sum(times.values())/len(times):.2f} ms")
                output.append("="*70)
            
            # Clear the times for next run
            r.delete('test:client_times')
    except Exception as e:
        pass  # Silently ignore Redis errors
    
    # Print everything at once atomically
    print("\n".join(output), flush=True)


if __name__ == '__main__':
    main()