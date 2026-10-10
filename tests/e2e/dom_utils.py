"""
Lightweight DOM and Project Inspection Utilities for Standalone E2E Tests.
Zero non-standard dependencies (Pure Python 3 standard library).
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Dict, Optional, Any


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    # Look for index.html or PROJECT.md
    current = Path(__file__).resolve().parent
    for _ in range(4):
        if (current / "index.html").exists() and (current / "PROJECT.md").exists():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()


PROJECT_ROOT = get_project_root()


class DOMNode:
    """Represents an HTML DOM element in the parsed tree."""

    def __init__(self, tag: str, attrs: Dict[str, str], parent: Optional['DOMNode'] = None):
        self.tag = tag.lower()
        self.attrs = {k.lower(): v for k, v in attrs.items()}
        self.parent = parent
        self.children: List['DOMNode'] = []
        self.text_content: List[str] = []

    @property
    def id(self) -> Optional[str]:
        return self.attrs.get('id')

    @property
    def classes(self) -> List[str]:
        class_str = self.attrs.get('class', '')
        return class_str.split() if class_str else []

    @property
    def text(self) -> str:
        """Returns recursive text content of node and descendants."""
        parts = list(self.text_content)
        for child in self.children:
            child_text = child.text
            if child_text:
                parts.append(child_text)
        return ' '.join(' '.join(parts).split())

    def get_attr(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.attrs.get(name.lower(), default)

    def has_class(self, class_name: str) -> bool:
        return class_name in self.classes

    def find_all(self, tag: Optional[str] = None, **attrs) -> List['DOMNode']:
        """Recursively find all matching elements."""
        results: List['DOMNode'] = []
        match = True
        if tag is not None and self.tag != tag.lower():
            match = False
        for attr_k, attr_v in attrs.items():
            node_v = self.attrs.get(attr_k.lower())
            if node_v is None or (attr_v is not True and node_v != str(attr_v)):
                match = False
                break
        if match and self.tag != 'document_root':
            results.append(self)
        for child in self.children:
            results.extend(child.find_all(tag=tag, **attrs))
        return results

    def find_one(self, tag: Optional[str] = None, **attrs) -> Optional['DOMNode']:
        matches = self.find_all(tag=tag, **attrs)
        return matches[0] if matches else None

    def select(self, selector: str) -> List['DOMNode']:
        """
        Simple CSS selector matching:
        - tag: 'a', 'div'
        - class: '.btn', '.clay-icon-3d'
        - id: '#scroll-world'
        - tag.class: 'a.btn'
        - tag[attr=val]: 'a[data-i18n=nav.tour]'
        """
        selector = selector.strip()
        # ID selector
        if selector.startswith('#'):
            target_id = selector[1:]
            return self.find_all(id=target_id)
        # Class selector
        if selector.startswith('.'):
            target_class = selector[1:]
            results = []
            for node in self.find_all():
                if node.has_class(target_class):
                    results.append(node)
            return results
        # Attribute selector e.g. [attr] or [attr=val]
        attr_match = re.match(r'^(?:([a-zA-Z0-9_-]+))?\[([a-zA-Z0-9_-]+)(?:=[\'"]?([^\'"]+)[\'"]?)?\]$', selector)
        if attr_match:
            tag_name, attr_name, attr_val = attr_match.groups()
            results = []
            for node in self.find_all(tag=tag_name):
                if attr_name in node.attrs:
                    if attr_val is None or node.attrs[attr_name] == attr_val:
                        results.append(node)
            return results
        # Tag with class e.g. 'div.my-class'
        if '.' in selector:
            parts = selector.split('.', 1)
            tag_name, class_name = parts[0], parts[1]
            results = []
            for node in self.find_all(tag=tag_name):
                if node.has_class(class_name):
                    results.append(node)
            return results
        # Plain tag
        return self.find_all(tag=selector)

    def __repr__(self) -> str:
        attrs_str = ' '.join(f'{k}="{v}"' for k, v in list(self.attrs.items())[:3])
        return f"<{self.tag} {attrs_str}>"


class SimpleDOMParser(HTMLParser):
    """Parses HTML into a DOMNode tree."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = DOMNode('document_root', {})
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attrs_dict = {k: (v if v is not None else '') for k, v in attrs}
        node = DOMNode(tag, attrs_dict, parent=self.current)
        self.current.children.append(node)
        # Void elements in HTML
        if tag.lower() not in ('img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'):
            self.current = node

    def handle_endtag(self, tag: str):
        if self.current.parent is not None and self.current.tag == tag.lower():
            self.current = self.current.parent

    def handle_data(self, data: str):
        cleaned = data.strip()
        if cleaned:
            self.current.text_content.append(cleaned)


def parse_html_file(relative_or_abs_path: str) -> DOMNode:
    """Parse an HTML file into a DOMNode tree."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    parser = SimpleDOMParser()
    parser.feed(content)
    return parser.root


def parse_html_content(html_str: str) -> DOMNode:
    """Parse raw HTML string into a DOMNode tree."""
    parser = SimpleDOMParser()
    parser.feed(html_str)
    return parser.root


def read_file_text(relative_or_abs_path: str) -> str:
    """Read full text of a file in the project."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def file_exists(relative_or_abs_path: str) -> bool:
    """Check if a file exists relative to project root."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.exists() and path.is_file()


def dir_exists(relative_or_abs_path: str) -> bool:
    """Check if a directory exists relative to project root."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.exists() and path.is_dir()


def parse_xml_file(relative_or_abs_path: str) -> ET.Element:
    """Parse an XML file into an ElementTree Element."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    tree = ET.parse(path)
    return tree.getroot()


def parse_json_file(relative_or_abs_path: str) -> Any:
    """Parse a JSON file from project."""
    path = Path(relative_or_abs_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return json.load(f)


def get_all_html_files() -> List[Path]:
    """Return all HTML files in project root and pages/."""
    files = []
    index = PROJECT_ROOT / 'index.html'
    if index.exists():
        files.append(index)
    pages_dir = PROJECT_ROOT / 'pages'
    if pages_dir.exists():
        for p in pages_dir.glob('*.html'):
            files.append(p)
    return sorted(files)
