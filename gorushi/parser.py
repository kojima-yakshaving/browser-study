from dataclasses import dataclass, field
from typing import Literal

from gorushi.constants import SELF_CLOSING_TAGS
from gorushi.node import Element, Node, Text
from gorushi.renderer import aho_corasick_matcher
from gorushi.state_machine import HTMLTokenizerState, HTMLTokenizerStateMachine


def print_tree(node: Node, indent: int = 0) -> None:
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

@dataclass 
class AttributesExtractor:
    text: str = ""

    state: Literal['idle', 'name', 'equal_sign', 'value', 'whitespace'] \
        = 'idle'

    def parse(self) -> dict[str, str]:
        attributes: dict[str, str] = {}
        
        attibute_name = ""
        attibute_value = ""
        current_quote_char: str | None = None

        for i in range(len(self.text)):
            c = self.text[i]
            if self.state == 'idle':
                if c.isspace():
                    continue
                else:
                    if c.isalnum() or c in ['-', '_']:
                        attibute_name += c
                        self.state = 'name'
            elif self.state == 'name':
                if c == '=':
                    self.state = 'equal_sign'
                elif c.isspace():
                    attributes[attibute_name.casefold()] = ""
                    attibute_name = ""
                    self.state = 'idle'
                else:
                    attibute_name += c
            elif self.state == 'equal_sign':
                if c in ['"', "'"]:
                    current_quote_char = c
                    self.state = 'value'
            elif self.state == 'value':
                if c == current_quote_char:
                    if self.text[i - 1] == '\\':
                        attibute_value = attibute_value[:-1] + c
                        continue
                    attributes[attibute_name.casefold()] = attibute_value
                    attibute_name = ""
                    attibute_value = ""
                    current_quote_char = None
                    self.state = 'idle'
                else:
                    attibute_value += c
            
        if attibute_name:
            attributes[attibute_name.casefold()] = attibute_value

        return attributes



@dataclass
class HTMLParser:
    HEAD_TAGS = [
        'base', 'basefont', 'bgsound', 'noscript',
        'link', 'meta', 'script', 'style', 'title'
    ]

    body: str = ""
    unfinished: list[Element] = field(default_factory=list)


    def parse(self) -> Element:
        state_machine = HTMLTokenizerStateMachine()
        for c in self.body:
            output = state_machine.feed(c)
            if output:
                kind, value = output
                if kind == "text":
                    if value:
                        self.add_text(value)
                elif kind == "tag":
                    self.add_tag(value)
                elif kind == "script":
                    self.add_text(value)
                elif kind == "comment":
                    _comment = state_machine.flush_buffer()

        if state_machine.state == HTMLTokenizerState.TEXT:
            text = state_machine.flush_buffer()
            if text:
                self.add_text(text)

        return self.finish()

    def implicit_tags(self, tag: str | None) -> None:
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != 'html':
                self.add_tag('html')
            elif open_tags == ['html'] \
                    and tag not in ['head', 'body', '/html']:
                if tag in self.HEAD_TAGS:
                    self.add_tag('head')
                else:
                    self.add_tag('body')
            elif open_tags == ['html', 'head'] \
                    and tag not in ['/head'] + self.HEAD_TAGS:
                self.add_tag('/head')
            elif len(open_tags) > 0 and open_tags[-1] == 'p' and tag == 'p':
                self.add_tag('/p')
            elif len(open_tags) > 0 and open_tags[-1] == 'li' and tag == 'li':
                self.add_tag('/li')
            else:
                break           

    def get_attributes(self, text: str) -> tuple[str, dict[str, str]]:
        parts = text.split()
        tag = parts[0].casefold()
        attributes_part = " ".join(parts[1:])

        extractor = AttributesExtractor(text=attributes_part)
        attributes = extractor.parse()

        return (tag, attributes)

    def add_text(self, text: str) -> None:
        if text.isspace():
            return

        unescaped_text = aho_corasick_matcher.replace_all(text)
        parent = self.unfinished[-1] 
        node = Text(text=unescaped_text, parent=parent)
        parent.children.append(node)

    def add_tag(self, tag: str) -> None:
        tag, attributes = self.get_attributes(tag)
        if tag.startswith('!'):
            return

        if tag.startswith('/'):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag=tag, parent=parent, attributes=attributes)
            if parent:
                parent.children.append(node)
        else:
            self.implicit_tags(tag)
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag=tag, parent=parent, attributes=attributes)
            self.unfinished.append(node)
        pass

    def finish(self) -> Element:
        if not self.unfinished:
            self.implicit_tags(None)

        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

