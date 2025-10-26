
import pytest
from gorushi.connection import Connection
from gorushi.url import URL
import time

@pytest.mark.cache
def test_caching_with_live_server():
    """Tests that the connection caches responses from a live server."""
    conn = Connection(http_options={'http_version': '1.1'})

    # Test max-age
    url_max_age = URL("http://localhost:8000/cache?mode=max-age")
    # First request, should fetch from server
    content1 = conn.request(url=url_max_age)
    # Second request, should be served from cache
    content2 = conn.request(url=url_max_age)
    assert content1 == content2

    # Test expiration
    time.sleep(10)
    # Third request, should fetch from server again
    content3 = conn.request(url=url_max_age)
    assert content1 != content3

    # Test no-store
    url_no_store = URL("http://localhost:8000/cache?mode=no-store")
    # First request, should fetch from server
    content4 = conn.request(url=url_no_store)
    # Second request, should also fetch from server
    content5 = conn.request(url=url_no_store)
    assert content4 != content5
