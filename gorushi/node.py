from dataclasses import dataclass, field


@dataclass
class Node:
    children: list['Node'] = field(default_factory=list)


@dataclass
class Element(Node):
    tag: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    parent: Node | None = None

    def __repr__(self) -> str:
        return f"<{self.tag}>"


@dataclass
class Text(Node):
    text: str = ""
    parent: Node | None = None

    def __repr__(self) -> str:
        return repr(self.text)
