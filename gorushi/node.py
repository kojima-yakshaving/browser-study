from dataclasses import dataclass, field


@dataclass
class Node:
    tag: str = ""
    children: list['Node'] = field(default_factory=list)


@dataclass
class Element(Node):
    attributes: dict[str, str] = field(default_factory=dict)
    parent: Node | None = None

    def __repr__(self) -> str:
        return f"<{self.tag} {self.attribute_str}>"

    @property
    def attribute_str(self) -> str:
        attrs: list[str] = []
        for key, value in self.attributes.items():
            attrs.append(f'{key}="{value}"')
        return " ".join(attrs)


@dataclass
class Text(Node):
    text: str = ""
    parent: Node | None = None

    def __repr__(self) -> str:
        return repr(self.text)
