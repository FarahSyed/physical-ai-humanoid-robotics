"""
Website crawler module for extracting content from Docusaurus websites
"""
import asyncio
import time
from typing import List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from src.utils.logger import logger
from src.utils.config_loader import config
from src.models.extracted_content import ExtractedContent
from src.utils.hash_utils import generate_content_hash


class WebsiteCrawler:
    """
    Crawls websites to extract content from pages
    """

    def __init__(self, delay: float = None, timeout: int = None):
        """
        Initialize the website crawler

        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.delay = delay or config.website_crawl_delay
        self.timeout = timeout or config.extraction_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; RAGBot/1.0; +https://example.com/bot)'
        })

    def crawl_urls(self, urls: List[str]) -> List[ExtractedContent]:
        """
        Crawl a list of URLs and extract content from each

        Args:
            urls: List of URLs to crawl

        Returns:
            List of ExtractedContent objects
        """
        extracted_contents = []

        for i, url in enumerate(urls):
            try:
                # Add delay to respect website crawl limits
                if i > 0:
                    time.sleep(self.delay)

                logger.info(f"Crawling URL {i+1}/{len(urls)}: {url}")

                # Fetch the page content
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Extract content from the page
                content = self.extract_content_from_page(response.text, url)

                if content:
                    extracted_contents.append(content)
                    logger.debug(f"Successfully extracted content from {url}")
                else:
                    logger.warning(f"No content extracted from {url}")

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue

        return extracted_contents

    def extract_content_from_page(self, html_content: str, url: str) -> Optional[ExtractedContent]:
        """
        Extract meaningful content from a single HTML page

        Args:
            html_content: Raw HTML content of the page
            url: URL of the page being processed

        Returns:
            ExtractedContent object or None if extraction fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements (navigation, footer, ads, etc.)
            selectors_to_remove = [
                'nav', 'header', 'footer', 'aside',
                'script', 'style', '.ads', '[class*="ad"]',
                '.cookie-consent', '.popup', '.modal'
            ]

            for selector in selectors_to_remove:
                for element in soup.select(selector):
                    element.decompose()

            # Try to find main content area - common selectors for Docusaurus and documentation sites
            main_content = None
            content_selectors = [
                'main',
                '.main',
                '.container',
                '.docMainContainer',
                '.markdown',
                '.theme-doc-markdown',
                '.article',
                '.post-content',
                '.content',
                '[role="main"]',
                '.docs-content',
                '.doc-content'
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use the body
            if not main_content:
                main_content = soup.find('body')

            # Extract text content
            if main_content:
                # Get text with proper spacing
                content_text = main_content.get_text(separator=' ', strip=True)

                # Clean up excessive whitespace
                import re
                content_text = re.sub(r'\s+', ' ', content_text).strip()
            else:
                content_text = soup.get_text(separator=' ', strip=True)
                content_text = re.sub(r'\s+', ' ', content_text).strip()

            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            else:
                # Fallback: extract from h1 or use URL
                h1_tag = soup.find('h1')
                if h1_tag:
                    title = h1_tag.get_text().strip()
                else:
                    title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()

            # Generate a unique ID based on URL and content
            content_hash = generate_content_hash(content_text[:1000])  # Use first 1000 chars for hash
            url_hash = generate_content_hash(url)
            unique_id = f"{url_hash[:16]}_{content_hash[:16]}"

            # Create ExtractedContent object
            extracted_content = ExtractedContent(
                id=unique_id,
                url=url,
                title=title,
                content=content_text,
                content_type="text/html"
            )

            # Validate the extracted content
            if extracted_content.validate() and len(content_text) > 50:  # Require minimum content length
                return extracted_content
            else:
                logger.warning(f"Content validation failed for {url} or content too short")
                return None

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None


class ContentExtractor:
    """
    Extracts and normalizes content from web pages
    """

    def __init__(self):
        pass

    def extract_main_content(self, html: str, url: str = "") -> str:
        """
        Extract the main content from HTML, removing navigation, footer, etc.

        Args:
            html: HTML content to extract from
            url: URL of the page (for context)

        Returns:
            Extracted main content as text
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove common non-content elements
        for element in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript']):
            element.decompose()

        # Remove elements with common ad/cookie class names
        ad_selectors = ['[class*="ad"]', '.ads', '.advertisement', '.cookie', '.banner', '.popup']
        for selector in ad_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Look for main content containers (prioritized list for Docusaurus sites)
        main_selectors = [
            'main',
            '.main',
            '.container',
            '.docMainContainer',
            '.markdown',
            '.theme-doc-markdown',
            '.article',
            '.post-content',
            '.docs-content',
            '.doc-content',
            '[role="main"]'
        ]

        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            content_text = main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback to body content
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator=' ', strip=True)
            else:
                content_text = soup.get_text(separator=' ', strip=True)

        # Clean up the text
        import re
        content_text = re.sub(r'\s+', ' ', content_text).strip()

        return content_text

    def extract_metadata(self, html: str, url: str) -> dict:
        """
        Extract metadata from HTML page

        Args:
            html: HTML content to extract from
            url: URL of the page

        Returns:
            Dictionary containing extracted metadata
        """
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'author': '',
            'published_date': '',
            'tags': []
        }

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Extract description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '')

        # Extract author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            metadata['author'] = author_tag.get('content', '')

        # Extract Open Graph tags
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and not metadata['title']:
            metadata['title'] = og_title.get('content', '')

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and not metadata['description']:
            metadata['description'] = og_desc.get('content', '')

        # Extract tags/keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            keywords = keywords_tag.get('content', '')
            if keywords:
                metadata['tags'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]

        return metadata

    def normalize_content(self, content: str) -> str:
        """
        Normalize content by cleaning up formatting and encoding issues

        Args:
            content: Raw content to normalize

        Returns:
            Normalized content
        """
        if not content:
            return content

        # Remove extra whitespace
        import re
        content = re.sub(r'\s+', ' ', content)

        # Clean up common formatting issues
        content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Remove extra spaces around punctuation
        content = re.sub(r'\s+([,.!?;:])', r'\1', content)

        # Strip leading/trailing whitespace
        content = content.strip()

        return content