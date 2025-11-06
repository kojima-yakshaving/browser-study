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

####
# Mismatched Tags Tests 
####

@pytest.mark.ci
def test_misnested_simple_b_i():
    # <b>Bold <i>both</b> italic</i>
    content = "<b>Bold <i>both</b> italic</i>"
    parser = HTMLParser(body=content)
    dom = parser.parse()

    body = dom.children[0]
    assert body.tag == "body"

    # <b> should contain: "Bold ", <i>both</i>
    b = body.children[0]
    assert b.tag == "b"
    assert isinstance(b.children[0], Text)
    assert b.children[0].text == "Bold "

    # implicit <i> opened after </b>
    i1 = b.children[1]
    assert isinstance(i1, Element)
    assert i1.tag == "i"
    assert isinstance(i1.children[0], Text)
    assert i1.children[0].text == "both"

    # after </b>, parser must reopen <i>
    i2 = body.children[1]
    assert i2.tag == "i"
    assert isinstance(i2.children[0], Text)
    assert i2.children[0].text == " italic"


@pytest.mark.ci
def test_misnested_three_levels_b_i_u():
    content = "<b>A <i>B <u>C</b> D</i> E</u>"
    parser = HTMLParser(body=content)
    dom = parser.parse()

    body = dom.children[0]
    assert body.tag == "body"

    # <b> should wrap the initial segment
    b = body.children[0]
    assert b.tag == "b"
    assert isinstance(b.children[0], Text)
    assert b.children[0].text.strip() == "A"

    # Inside <b> → <i>
    i = b.children[1]
    assert i.tag == "i"

    # Inside <i> → <u>
    u = i.children[1]
    assert u.tag == "u"

    # <u> contains "C"
    assert isinstance(u.children[0], Text)
    assert u.children[0].text == "C"

@pytest.mark.ci
def test_misnested_with_br_void_element():
    content = "<b>bold <i>mid <br> brtag</b> tail</i>"
    parser = HTMLParser(body=content)
    dom = parser.parse()

    body = dom.children[0]
    assert body.tag == "body"

    b = body.children[0]
    assert b.tag == "b"

    # b → children: "bold ", <i>..., implicit </i>, etc.
    assert isinstance(b.children[0], Text)
    assert "bold" in b.children[0].text

    # <i> inside <b>
    i = b.children[1]
    assert i.tag == "i"

    # Ensure <br> stays inside <i>
    br = i.children[1]
    assert br.tag == "br"

    # The text after br should be inside the same <i>
    assert isinstance(i.children[2], Text)
    assert "brtag" in i.children[2].text

    # After </b> → implicit <i> wraps "tail"
    reopened_i = body.children[1]
    assert reopened_i.tag == "i"
    assert isinstance(reopened_i.children[0], Text)
    assert reopened_i.children[0].text == " tail"



