#!/usr/bin/env python3
"""
Simple test script for markdown rendering
"""
from utils.markdown_utils import render_markdown_to_html

# Test markdown content with various elements
test_markdown = """
# Heading 1
## Heading 2
### Heading 3
#### Heading 4

**Bold text** and *italic text*

- List item 1
- List item 2
  - Nested item

1. Numbered item 1
2. Numbered item 2

[Link example](https://example.com)

```
Code block example
```

> This is a blockquote

Table example:
| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""

# Render markdown to HTML
html_content = render_markdown_to_html(test_markdown)

# Print results
print("\n\n======= ORIGINAL MARKDOWN =======\n")
print(test_markdown)
print("\n\n======= RENDERED HTML =======\n")
print(html_content)
