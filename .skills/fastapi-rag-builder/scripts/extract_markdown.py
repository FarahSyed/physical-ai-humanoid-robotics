#!/usr/bin/env python3
"""
Extract and chunk markdown content for RAG system.

Usage:
    python extract_markdown.py --input docs/ --output data/chunked/chunked_content.json
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import re


def extract_markdown_files(input_dir: Path) -> List[Path]:
    """Find all markdown files in directory."""
    return list(input_dir.rglob("*.md"))


def chunk_content(content: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Chunk content into smaller pieces with overlap.

    Args:
        content: Full text content
        chunk_size: Target size for each chunk (in characters)
        overlap: Overlap between chunks (in characters)

    Returns:
        List of content chunks
    """
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    start = 0

    while start < len(content):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(content):
            # Look for sentence endings
            sentence_end = content.rfind('. ', start, end)
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1

        chunks.append(content[start:end].strip())
        start = end - overlap

    return chunks


def extract_metadata(file_path: Path, base_dir: Path) -> Dict[str, Any]:
    """Extract metadata from markdown file."""
    relative_path = file_path.relative_to(base_dir)

    # Extract title from first heading
    content = file_path.read_text(encoding='utf-8')
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem

    return {
        "source_url": str(relative_path),
        "title": title,
        "source_type": "markdown",
        "file_path": str(file_path)
    }


def process_markdown_files(input_dir: Path, chunk_size: int = 2000) -> List[Dict[str, Any]]:
    """
    Process all markdown files and create chunks.

    Args:
        input_dir: Directory containing markdown files
        chunk_size: Target size for chunks

    Returns:
        List of chunk dictionaries
    """
    md_files = extract_markdown_files(input_dir)
    print(f"Found {len(md_files)} markdown files")

    all_chunks = []
    chunk_counter = 1

    for md_file in md_files:
        print(f"Processing: {md_file.name}")

        try:
            content = md_file.read_text(encoding='utf-8')

            # Remove frontmatter if present
            content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

            # Extract metadata
            metadata = extract_metadata(md_file, input_dir)

            # Chunk content
            chunks = chunk_content(content, chunk_size=chunk_size)

            # Create chunk objects
            for idx, chunk_text in enumerate(chunks):
                chunk = {
                    "id": f"chunk_{chunk_counter}",
                    "content": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "token_count": len(chunk_text.split()),
                        "chunk_type": "sentence_based"
                    }
                }
                all_chunks.append(chunk)
                chunk_counter += 1

        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            continue

    return all_chunks


def main():
    parser = argparse.ArgumentParser(description="Extract and chunk markdown content")
    parser.add_argument("--input", type=str, required=True, help="Input directory with markdown files")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    parser.add_argument("--chunk-size", type=int, default=2000, help="Target chunk size in characters")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_file = Path(args.output)

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return

    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Process files
    chunks = process_markdown_files(input_dir, chunk_size=args.chunk_size)

    # Save to JSON
    output_data = {"chunks": chunks}

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Total chunks: {len(chunks)}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
