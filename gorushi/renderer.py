from collections import deque
from dataclasses import dataclass, field
from enum import Enum


ENTITIES = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&#39;": "'",
}

class RenderMode(Enum):
    RAW = 1 
    RENDERED = 2


@dataclass
class TrieNode:
    """Node in the Aho-Corasick automaton."""
    children: dict[str, 'TrieNode'] = field(default_factory=dict)
    is_terminal: bool = False  # Marks end of a pattern
    replacement: str | None = None  # Value to replace matched pattern with
    failure_link: 'TrieNode | None' = None  # Fallback node on mismatch


@dataclass 
class AhoCorasickMatcher:
    """
    Aho-Corasick algorithm implementation for efficient multi-pattern matching.
    
    Uses a trie with failure links to handle overlapping patterns and partial
    match failures. Useful for entity recognition, text replacement, etc.
    """
    root: TrieNode = field(default_factory=TrieNode)
    _compiled: bool = False  # Track if failure links are built
    
    def add_pattern(self, pattern: str, replacement: str) -> None:
        """
        Insert a pattern and its replacement value into the trie.
        
        Args:
            pattern: The text pattern to match
            replacement: The value to replace the pattern with
        """
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_terminal = True
        node.replacement = replacement
        self._compiled = False  # Need to rebuild failure links

    def compile(self) -> None:
        """
        Build failure links using BFS traversal.
        Must be called after adding all patterns and before matching.
        """
        queue: deque[TrieNode] = deque()
        
        # Level 1 nodes fail back to root
        for child in self.root.children.values():
            child.failure_link = self.root
            queue.append(child)
        
        # BFS to build failure links for remaining nodes
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find the deepest node that matches the suffix
                fail_node = current.failure_link
                while fail_node and char not in fail_node.children:
                    fail_node = fail_node.failure_link
                
                child.failure_link = fail_node.children[char] if fail_node else self.root
                
                # Inherit terminal status from failure link if needed
                if child.failure_link.is_terminal and not child.is_terminal:
                    child.is_terminal = True
                    child.replacement = child.failure_link.replacement
        
        self._compiled = True

    def replace_all(self, text: str) -> str:
        """
        Scan text and replace all pattern matches with their replacements.
        
        Args:
            text: Input text to scan
            
        Returns:
            Text with all patterns replaced
            
        Raises:
            RuntimeError: If compile() hasn't been called
        """
        if not self._compiled:
            raise RuntimeError("Must call compile() before matching")
        
        result: list[str] = []
        node = self.root
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Follow failure links until we find a match or reach root
            while node != self.root and char not in node.children:
                node = node.failure_link
            
            if char in node.children:
                node = node.children[char]
            else:
                # No match from root - keep original character
                result.append(char)
                i += 1
                continue
            
            # Check if we've completed a pattern match
            if node.is_terminal:
                result.append(node.replacement or '')
                node = self.root  # Reset to root after match
            
            i += 1
        
        return ''.join(result)

aho_corasick_matcher = AhoCorasickMatcher()

for entity, replacement in ENTITIES.items():
    aho_corasick_matcher.add_pattern(entity, replacement)
aho_corasick_matcher.compile()


@dataclass
class Renderer:
    content: str
    render_mode: RenderMode = RenderMode.RENDERED

    def render_text_only(self) -> str:
        if self.render_mode == RenderMode.RAW:
            return self.content

        text = ""
        in_tag = False
        for c in self.content:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                text += c

        return text


    def render(self) -> str:
        if self.render_mode == RenderMode.RAW:
            return self.content
        elif self.render_mode == RenderMode.RENDERED:
            return aho_corasick_matcher.replace_all(self.content)
        else:
            raise ValueError("Unsupported render mode")
