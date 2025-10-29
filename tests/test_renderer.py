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
def test_renderer_empty_content():
    content = ""
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert rendered_content == ""

@pytest.mark.ci
def test_combined_entities_and_links():
    content = "Visit &lt;this&gt; link: http://example.com"
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert "Visit <this> link: http://example.com" in rendered_content

@pytest.mark.ci
def test_renderer_with_special_characters():
    content = "Special chars: &amp; &quot; &#39; &lt; &gt;"
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert "Special chars: & \" ' < >" in rendered_content 

@pytest.mark.ci
def test_renderer_with_double_encoded_entities():
    content = "Double encoded: &amp;gt; &amp;lt;"
    renderer = Renderer(content=content)
    rendered_content = renderer.render()
    assert "Double encoded: &gt; &lt;" in rendered_content

