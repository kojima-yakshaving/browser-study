import pytest
from gorushi.node import Text
from gorushi.parser import HTMLParser, print_tree


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
