import pytest

from gorushi.url import URL


@pytest.mark.ci
def test_file_url():
    url = URL.parse("file:///path/to/file")
    assert url.scheme == "file"
    assert url.path == "/path/to/file"


@pytest.mark.ci
def test_data_scheme():
    url = URL.parse("data:text/html,Hello World")
    assert url.scheme == "data"
    assert url.content == "Hello World"


@pytest.mark.ci
def test_view_source_scheme():
    url = URL.parse("view-source:http://example.com")
    assert url.view_source
    assert url.scheme == "http"
    assert url.host == "example.com"
