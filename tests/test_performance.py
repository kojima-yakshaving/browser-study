import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from gorushi.url import URL
from gorushi.connection import Connection, ConnectionPoolCacheKey

# --- Benchmark Function ---

def run_benchmark(num_requests, keep_alive):
    base_url = "http://example.org"
    Connection.connection_pool.clear()
    times = []
    connections = {'new': 0, 'reused': 0}
    http_version = "1.1" if keep_alive else "1.0"

    for i in range(num_requests):
        url = URL(base_url)
        key = ConnectionPoolCacheKey(host=url.host, port=url.port)
        
        # For HTTP/1.1, we check the pool before the request to see if it will be reused.
        if keep_alive:
            if key not in Connection.connection_pool:
                connections['new'] += 1
            # In the first request, the connection is new but not yet in the pool.
            # After the first request, it's reused.
            elif i > 0:
                connections['reused'] += 1
        else:
            # For HTTP/1.0, a new connection is always made.
            connections['new'] += 1

        start_time = time.perf_counter()
        
        conn = Connection(http_options={"http_version": http_version})
        conn.request(url=url)
        
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    # Close any sockets left in the pool
    for sock in Connection.connection_pool.values():
        sock.close()
    Connection.connection_pool.clear()
    
    # The first connection in a keep-alive scenario is also "new"
    if keep_alive and num_requests > 0:
        connections['reused'] = num_requests - 1

    return {
        'total_time': sum(times),
        'avg_time': sum(times) / num_requests if num_requests > 0 else 0,
        'connections': connections,
    }

# --- Tests ---

def test_performance_with_keep_alive():
    """Tests performance with HTTP/1.1 keep-alive enabled."""
    num_requests = 20
    results = run_benchmark(num_requests, keep_alive=True)

    print(f"\n--- Keep-Alive Enabled (HTTP/1.1) ---")
    print(f"Total time for {num_requests} requests: {results['total_time']:.4f}s")
    print(f"Average time per request: {results['avg_time']:.4f}s")
    print(f"New connections: {results['connections']['new']}")
    print(f"Reused connections: {results['connections']['reused']}")

    # With keep-alive, there should be only one new connection
    assert results['connections']['new'] == 1
    assert results['connections']['reused'] == num_requests - 1

def test_performance_without_keep_alive():
    """Tests performance with HTTP/1.0 (no keep-alive)."""
    num_requests = 20
    results = run_benchmark(num_requests, keep_alive=False)

    print(f"\n--- Keep-Alive Disabled (HTTP/1.0) ---")
    print(f"Total time for {num_requests} requests: {results['total_time']:.4f}s")
    print(f"Average time per request: {results['avg_time']:.4f}s")
    print(f"New connections: {results['connections']['new']}")
    print(f"Reused connections: {results['connections']['reused']}")

    # Without keep-alive, a new connection is made for each request
    assert results['connections']['new'] == num_requests
    assert results['connections']['reused'] == 0

def test_connection_reuse_across_urls():
    """Tests that connections are reused for different paths on the same host/port."""
    Connection.connection_pool.clear()
    num_requests = 10
    base_url = "http://example.org"
    conn = Connection(http_options={"http_version": "1.1"})

    # First request to establish a connection
    conn.request(url=URL(f"{base_url}/page1"))
    assert len(Connection.connection_pool) == 1

    # Subsequent requests to different paths but the same host
    for i in range(num_requests - 1):
        conn.request(url=URL(f"{base_url}/page{i+2}"))

    # The same connection should be reused
    assert len(Connection.connection_pool) == 1

    # Cleanup
    for sock in Connection.connection_pool.values():
        sock.close()
    Connection.connection_pool.clear()
