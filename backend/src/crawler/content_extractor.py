"""
Content extractor module for extracting and normalizing content from web pages
"""
from typing import Dict, Any, List, Optional
import re
from bs4 import BeautifulSoup
from src.models.extracted_content import ExtractedContent
from src.utils.logger import logger
from src.utils.hash_utils import generate_content_hash


class ContentExtractor:
    """
    Extracts and normalizes content from web pages, focusing on Docusaurus documentation sites
    """

    def __init__(self):
        self.content_selectors = [
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

        self.remove_selectors = [
            'nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript',
            '.ads', '[class*="ad"]', '.advertisement', '.cookie-consent',
            '.popup', '.modal', '.toc', '.table-of-contents'
        ]

    def extract_content_from_html(self, html: str, url: str, title: str = None) -> ExtractedContent:
        """
        Extract content from HTML and create an ExtractedContent object

        Args:
            html: HTML content to extract from
            url: URL of the page
            title: Title of the page (will be extracted from HTML if not provided)

        Returns:
            ExtractedContent object
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        self._remove_unwanted_elements(soup)

        # Extract title if not provided
        if not title:
            title = self._extract_title(soup, url)

        # Extract main content
        content_text = self._extract_main_content(soup)

        # Extract metadata
        metadata = self._extract_metadata(soup, url)

        # Normalize content
        normalized_content = self.normalize_content(content_text)

        # Generate ID
        content_hash = generate_content_hash(normalized_content[:1000])  # Use first 1000 chars for hash
        url_hash = generate_content_hash(url)
        unique_id = f"{url_hash[:16]}_{content_hash[:16]}"

        # Create ExtractedContent object
        extracted_content = ExtractedContent(
            id=unique_id,
            url=url,
            title=title,
            content=normalized_content,
            content_type="text/html",
            metadata=metadata
        )

        return extracted_content

    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """
        Remove unwanted elements from the soup object

        Args:
            soup: BeautifulSoup object to clean
        """
        for selector in self.remove_selectors:
            for element in soup.select(selector):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract title from soup object or generate from URL

        Args:
            soup: BeautifulSoup object
            url: URL of the page

        Returns:
            Extracted or generated title
        """
        # Try to find title in various locations
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            if title:
                return title

        # Try h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.get_text().strip()
            if title:
                return title

        # Try Open Graph title
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            title = og_title.get('content', '').strip()
            if title:
                return title

        # Fallback: generate from URL
        return url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from soup object

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted content text
        """
        # Look for main content containers
        main_content = None
        for selector in self.content_selectors:
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

        return content_text

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract metadata from soup object

        Args:
            soup: BeautifulSoup object
            url: URL of the page

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'url': url,
            'description': '',
            'author': '',
            'published_date': '',
            'tags': [],
            'headings': [],
            'word_count': 0,
            'extracted_at': None
        }

        # Extract description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '')

        # Extract Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and not metadata['description']:
            metadata['description'] = og_desc.get('content', '')

        # Extract author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            metadata['author'] = author_tag.get('content', '')

        # Extract tags/keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            keywords = keywords_tag.get('content', '')
            if keywords:
                metadata['tags'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]

        # Extract headings
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    metadata['headings'].append({
                        'level': i,
                        'text': text
                    })

        # Calculate word count
        content_text = self._extract_main_content(soup)
        metadata['word_count'] = len(content_text.split()) if content_text else 0

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
        content = re.sub(r'\s+', ' ', content)

        # Clean up common formatting issues
        content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Remove extra spaces around punctuation
        content = re.sub(r'\s+([,.!?;:])', r'\1', content)

        # Strip leading/trailing whitespace
        content = content.strip()

        return content

    def extract_code_blocks(self, html: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from HTML content

        Args:
            html: HTML content to extract from

        Returns:
            List of dictionaries containing code blocks and their languages
        """
        soup = BeautifulSoup(html, 'html.parser')
        code_blocks = []

        # Find all code blocks (common patterns in documentation sites)
        code_elements = soup.find_all(['code', 'pre'])

        for element in code_elements:
            code_text = element.get_text()
            if code_text.strip():
                # Try to determine language from class
                lang = ""
                if element.get('class'):
                    classes = element.get('class')
                    for cls in classes:
                        if 'language-' in cls:
                            lang = cls.replace('language-', '')
                            break
                        elif 'lang-' in cls:
                            lang = cls.replace('lang-', '')
                            break

                code_blocks.append({
                    'code': code_text,
                    'language': lang,
                    'type': element.name
                })

        return code_blocks

    def extract_links(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """
        Extract links from HTML content

        Args:
            html: HTML content to extract from
            base_url: Base URL to resolve relative links

        Returns:
            List of dictionaries containing link information
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()

            # Resolve relative URLs
            if base_url and href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif base_url and not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                href = base_url.rstrip('/') + '/' + href

            if text and href:
                links.append({
                    'url': href,
                    'text': text
                })

        return links


class ContentValidator:
    """
    Validates extracted content quality and completeness
    """

    def validate_content(self, extracted_content: ExtractedContent) -> Dict[str, Any]:
        """
        Validate extracted content and return quality metrics

        Args:
            extracted_content: ExtractedContent object to validate

        Returns:
            Dictionary with validation results and quality metrics
        """
        results = {
            'valid': True,
            'quality_score': 0.0,
            'issues': [],
            'suggestions': []
        }

        # Check content length
        content_length = len(extracted_content.content) if extracted_content.content else 0
        if content_length < 50:
            results['valid'] = False
            results['issues'].append('Content too short')
            results['suggestions'].append('Ensure the page contains substantial content')
        elif content_length < 200:
            results['quality_score'] += 0.3
            results['suggestions'].append('Content is quite short, consider if more content is available')
        else:
            results['quality_score'] += 0.5

        # Check title
        if not extracted_content.title or len(extracted_content.title.strip()) < 3:
            results['valid'] = False
            results['issues'].append('Title too short or missing')
        else:
            results['quality_score'] += 0.2

        # Check URL
        if not extracted_content.url:
            results['valid'] = False
            results['issues'].append('URL missing')
        else:
            results['quality_score'] += 0.1

        # Check for common issues
        if extracted_content.content and '404' in extracted_content.content:
            results['issues'].append('Possible 404 error page detected')
            results['valid'] = False

        if extracted_content.content and 'access denied' in extracted_content.content.lower():
            results['issues'].append('Access denied page detected')
            results['valid'] = False

        # Ensure quality score is between 0 and 1
        results['quality_score'] = min(1.0, results['quality_score'])

        return results

    def filter_content(self, extracted_contents: List[ExtractedContent]) -> List[ExtractedContent]:
        """
        Filter out low-quality content

        Args:
            extracted_contents: List of ExtractedContent objects

        Returns:
            Filtered list of ExtractedContent objects
        """
        validator = ContentValidator()
        filtered_contents = []

        for content in extracted_contents:
            validation = validator.validate_content(content)
            if validation['valid'] and validation['quality_score'] >= 0.5:  # Only keep content with 50%+ quality
                filtered_contents.append(content)
            else:
                logger.info(f"Filtered out low-quality content from {content.url}: {validation['issues']}")

        return filtered_contents