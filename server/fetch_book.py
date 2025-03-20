#!/usr/bin/env python3
"""
Command-line utility to fetch book content using book IDs.

Usage:
    python fetch_book.py <book_id>

Example:
    python fetch_book.py 12550-1
"""

import sys
import json
import os
from libs.data_source import fetch_book_content


def main():
    """Main function that processes command-line arguments and fetches book content."""
    # Validate command-line arguments
    if len(sys.argv) < 2:
        print("Error: Missing book ID.")
        print("Usage: python fetch_book.py <book_id>")
        print("Example: python fetch_book.py 12550-1")
        sys.exit(1)

    book_id = sys.argv[1]
    print(f"🔍 Fetching content for book ID: {book_id}...")

    try:
        # Fetch the book content
        result = fetch_book_content(book_id)

        if result:
            print("\n📖 Book details:")
            print(f"ID: {result['book_id']}")
            print(f"Title: {result['book_title']}")
            print(f"Description: {result['book_description']}")

            # Print content with formatting
            print("\n📑 Content preview:")
            content = result['book_content']
            # If content is long, just show a preview
            if len(content) > 500:
                print(content[:500] + "...\n")
                print(f"(Content truncated, total length: {len(content)} characters)")
            else:
                print(content)

            # Offer to save the full content to a file
            save_option = input("\nSave full content to a file? (y/n): ").lower()
            if save_option == 'y':
                filename = f"book_{book_id}.txt"
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(f"Title: {result['book_title']}\n")
                    file.write(f"Description: {result['book_description']}\n\n")
                    file.write(result['book_content'])
                print(f"✅ Content saved to {os.path.abspath(filename)}")
        else:
            print(f"❌ No book found with ID: {book_id}")
            print("Available test book IDs: 12550-1, 2590-3, 2940-5")

    except Exception as e:
        print(f"❌ Error fetching book content: {str(e)}")
        print("Make sure your environment is properly configured with database credentials.")
        sys.exit(1)


if __name__ == "__main__":
    main()
