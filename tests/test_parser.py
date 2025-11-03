import pytest
from gorushi.node import Element, Text
from gorushi.parser import AttributesExtractor, HTMLParser, print_tree


####
# Attributes Extractor Tests
####
@pytest.mark.ci
def test_attributes_extractor_basic():
    content = 'class="btn btn-primary" id="submit-btn" disabled'
    extractor = AttributesExtractor(text=content)
    attributes = extractor.parse()
    assert attributes.get('class') == 'btn btn-primary'
    assert attributes.get('id') == 'submit-btn'
    assert 'disabled' in attributes
    assert attributes.get('disabled') == ''


####
# HTML Parser Tests
####

@pytest.mark.ci
def test_parser_basic_functionality():
    content = "<html><head><title>Test</title></head><body>Hello World</body></html>"
    parser = HTMLParser(body=content)
    dom_tree = parser.parse()
    assert dom_tree.tag == 'html'
    assert len(dom_tree.children) == 2


@pytest.mark.ci
def test_parser_with_unclosed_tags():
    content = "<html><body><p>Paragraph 1<p>Paragraph 2</body></html>"
    parser = HTMLParser(body=content)
    dom_tree = parser.parse()
    assert dom_tree.tag == 'html'
    body = dom_tree.children[0]
    assert body.tag == 'body'
    assert len(body.children) == 2
    assert body.children[0].tag == 'p'
    assert body.children[1].tag == 'p'


@pytest.mark.ci 
def test_parser_with_comments_and_scripts():
    content = "<html><!-- This is a comment --><body><script>var a = 1;</script></body></html>"
    parser = HTMLParser(body=content)
    dom_tree = parser.parse()
    assert dom_tree.tag == 'html'

    body = dom_tree.children[0]
    assert body.tag == 'body'

    script = body.children[0]
    assert script.tag == 'script'
    assert isinstance(script.children[0], Text)
    assert script.children[0].text == 'var a = 1;'


@pytest.mark.ci 
def test_parser_with_tailwind_classes():
    content = '<div class="bg-blue-500 text-white p-4">Hello Tailwind</div>'
    parser = HTMLParser(body=content)
    dom_tree = parser.parse()
    html = dom_tree
    body = html.children[0]
    div = body.children[0]
    assert isinstance(body, Element)
    assert isinstance(div, Element)
    assert div.attributes.get('class') == 'bg-blue-500 text-white p-4'
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == 'Hello Tailwind'


@pytest.mark.ci 
def test_quote_handling_in_attributes():
    content = '<a href="http://example.com" title=\'Example "Site"\'>Link</a>'
    parser = HTMLParser(body=content)
    dom_tree = parser.parse()
    html = dom_tree
    body = html.children[0]
    a_tag = body.children[0]
    assert isinstance(body, Element)
    assert isinstance(a_tag, Element)
    assert a_tag.attributes.get('href') == 'http://example.com'
    assert a_tag.attributes.get('title') == 'Example "Site"'
    assert isinstance(a_tag.children[0], Text)
    assert a_tag.children[0].text == 'Link'
