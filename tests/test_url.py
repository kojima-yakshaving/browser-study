from url import URL


def test_file_url():
    url = URL("file:///path/to/file")
    assert url.scheme == "file"
    assert url.path == "/path/to/file"

def test_data_scheme():
    url = URL("data:text/html,Hello World")
    assert url.scheme == "data"
    assert url.content == "Hello World"

def test_view_source_scheme():
    url = URL("view-source:http://example.com")
    assert url.show_raw
    assert url.scheme == "http"
    assert url.host == "example.com"
