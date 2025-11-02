from dataclasses import dataclass, field

from gorushi.constants import SELF_CLOSING_TAGS
from gorushi.node import Element, Node, Text
from gorushi.renderer import aho_corasick_matcher


def print_tree(node: Node, indent: int = 0) -> None:
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


@dataclass
class HTMLParser:
    HEAD_TAGS = [
        'base', 'basefont', 'bgsound', 'noscript',
        'link', 'meta', 'script', 'style', 'title'
    ]


    body: str = ""
    unfinished: list[Element] = field(default_factory=list)

    def parse(self) -> Node:
        text = ""
        in_tag = False

        for c in self.body:
            if c == '<': 
                in_tag = True 
                if text:
                    self.add_text(text)
                text = ""
            elif c == '>':
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c

        if not in_tag and text:
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
            else:
                break

    def get_attributes(self, text: str) -> tuple[str, dict[str, str]]:
        parts = text.split()
        tag = parts[0].casefold()
        attributes: dict[str, str] = {}
        for attrpair in parts[1:]:
            if '=' in attrpair:
                key, value = attrpair.split('=', 1)
                if len(value) >= 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]

                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
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
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag=tag, parent=parent, attributes=attributes)
            self.unfinished.append(node)
        pass

    def finish(self) -> Node:
        if not self.unfinished:
            self.implicit_tags(None)

        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

