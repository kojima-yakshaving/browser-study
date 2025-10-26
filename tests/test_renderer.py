import pytest

from gorushi.url import URL
from gorushi.renderer import Renderer, RenderMode


@pytest.mark.ci
def test_renderer():
    content = "<html><body>Link to http://example.com/about</body></html>"
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert "http://example.com/about" in rendered_content


@pytest.mark.ci
def test_renderer_raw_mode():
    content = "<html><body>Hello &lt;World&gt;</body></html>"
    renderer = Renderer(content=content, render_mode=RenderMode.RAW)
    rendered_content = renderer.render()
    assert rendered_content == content


@pytest.mark.ci
def test_renderer_plain_text():
    content = "This is plain text."
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert rendered_content == "This is plain text."


@pytest.mark.ci
def test_renderer_content_with_tags():
    content = "<div>Hello <span>World</span></div>"
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert rendered_content == "Hello World"


@pytest.mark.ci
def test_renderer_empty_content():
    content = ""
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert rendered_content == ""
