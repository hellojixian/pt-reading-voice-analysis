"""
Markdown parsing utilities for server-side rendering of markdown content
"""

import markdown
import re

def render_markdown_to_html(text):
    """
    Convert markdown text to HTML for client-side rendering

    Args:
        text (str): Markdown formatted text

    Returns:
        str: HTML formatted content
    """
    if not text:
        return ""

    # Pre-process the markdown to handle specific elements that need custom handling
    processed_text = text

    # Pre-process headings to ensure proper conversion (fix for the original issue)
    # Handle all heading levels from 1 to 6
    for level in range(1, 7):
        heading_pattern = rf'^{"#" * level}\s+(.*?)$'
        replacement = f'<h{level}>\\1</h{level}>'
        processed_text = re.sub(heading_pattern, replacement, processed_text, flags=re.MULTILINE)

    # Configure markdown extensions
    extensions = [
        'tables',          # Support for tables
        'nl2br',           # Convert newlines to line breaks
        'fenced_code',     # Support for fenced code blocks
        'codehilite',      # Syntax highlighting for code blocks
        'sane_lists',      # Better list handling
        'smarty',          # Smart quotes, dashes, etc.
        'attr_list',       # Attribute lists
        'def_list'         # Definition lists
    ]

    # Convert processed markdown to HTML
    html = markdown.markdown(processed_text, extensions=extensions)

    return html
