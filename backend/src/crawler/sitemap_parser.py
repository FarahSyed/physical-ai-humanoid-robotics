"""
Sitemap parser for extracting URLs from sitemap.xml files
"""
import requests
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from src.utils.logger import logger


class SitemapParser:
    """
    Parses sitemap.xml files to extract URLs for crawling
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the sitemap parser

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def fetch_sitemap(self, sitemap_url: str) -> Optional[str]:
        """
        Fetch the sitemap content from the given URL

        Args:
            sitemap_url: URL of the sitemap.xml file

        Returns:
            Content of the sitemap as a string, or None if failed
        """
        try:
            response = requests.get(sitemap_url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch sitemap from {sitemap_url}: {e}")
            return None

    def parse_sitemap_content(self, sitemap_content: str) -> List[str]:
        """
        Parse the sitemap content and extract URLs

        Args:
            sitemap_content: Content of the sitemap.xml file

        Returns:
            List of URLs extracted from the sitemap
        """
        urls = []
        try:
            # Parse the XML content
            root = ET.fromstring(sitemap_content)

            # Handle different namespaces
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }

            # Find all <url><loc> elements (for regular sitemaps)
            for url_elem in root.findall('.//sitemap:url', namespaces):
                loc_elem = url_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())

            # Also look for URLs without namespace (in case sitemap doesn't use namespace)
            if not urls:
                for url_elem in root.findall('.//url'):
                    loc_elem = url_elem.find('loc')
                    if loc_elem is not None and loc_elem.text:
                        urls.append(loc_elem.text.strip())

        except ET.ParseError as e:
            logger.error(f"Failed to parse sitemap XML: {e}")
            return []

        return urls

    def parse_sitemap_index(self, sitemap_content: str) -> List[str]:
        """
        Parse a sitemap index file to extract URLs of individual sitemaps

        Args:
            sitemap_content: Content of the sitemap index XML file

        Returns:
            List of sitemap URLs extracted from the index
        """
        sitemap_urls = []
        try:
            # Parse the XML content
            root = ET.fromstring(sitemap_content)

            # Handle different namespaces
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }

            # Find all <sitemap><loc> elements
            for sitemap_elem in root.findall('.//sitemap:sitemap', namespaces):
                loc_elem = sitemap_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    sitemap_urls.append(loc_elem.text.strip())

        except ET.ParseError as e:
            logger.error(f"Failed to parse sitemap index XML: {e}")
            return []

        return sitemap_urls

    def extract_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Extract all URLs from a sitemap file

        Args:
            sitemap_url: URL of the sitemap.xml file

        Returns:
            List of URLs extracted from the sitemap
        """
        logger.info(f"Extracting URLs from sitemap: {sitemap_url}")

        # Fetch the sitemap content
        sitemap_content = self.fetch_sitemap(sitemap_url)
        if not sitemap_content:
            logger.error(f"Could not fetch sitemap content from {sitemap_url}")
            return []

        # First, check if this is a sitemap index
        sitemap_urls = self.parse_sitemap_index(sitemap_content)

        if sitemap_urls:
            # This is a sitemap index, extract URLs from each referenced sitemap
            all_urls = []
            for s_url in sitemap_urls:
                logger.info(f"Processing sitemap from index: {s_url}")
                urls = self.parse_sitemap_content(self.fetch_sitemap(s_url) or "")
                all_urls.extend(urls)
            return all_urls
        else:
            # This is a regular sitemap, extract URLs directly
            return self.parse_sitemap_content(sitemap_content)

    def normalize_and_filter_urls(
        self,
        urls: List[str],
        base_url: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Normalize URLs and filter them based on patterns

        Args:
            urls: List of URLs to normalize and filter
            base_url: Base URL to resolve relative URLs
            include_patterns: List of patterns that URLs must match to be included
            exclude_patterns: List of patterns that exclude matching URLs

        Returns:
            List of normalized and filtered URLs
        """
        normalized_urls = set()  # Use set to avoid duplicates

        for url in urls:
            # Resolve relative URLs if base_url is provided
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)

            # Validate URL format
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                continue  # Skip invalid URLs

            # Apply include filters
            if include_patterns:
                should_include = any(pattern in url for pattern in include_patterns)
                if not should_include:
                    continue

            # Apply exclude filters
            if exclude_patterns:
                should_exclude = any(pattern in url for pattern in exclude_patterns)
                if should_exclude:
                    continue

            normalized_urls.add(url)

        return list(normalized_urls)

    def get_all_urls(
        self,
        sitemap_url: str,
        base_url: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get all URLs from a sitemap with optional filtering

        Args:
            sitemap_url: URL of the sitemap.xml file
            base_url: Base URL to resolve relative URLs
            include_patterns: List of patterns that URLs must match to be included
            exclude_patterns: List of patterns that exclude matching URLs

        Returns:
            List of normalized and filtered URLs
        """
        logger.info(f"Getting all URLs from sitemap: {sitemap_url}")

        # Extract URLs from the sitemap
        urls = self.extract_urls_from_sitemap(sitemap_url)

        # Normalize and filter the URLs
        filtered_urls = self.normalize_and_filter_urls(
            urls,
            base_url=base_url,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )

        logger.info(f"Extracted {len(filtered_urls)} unique URLs from sitemap")
        return filtered_urls


# Example usage function
def example_usage():
    """
    Example of how to use the SitemapParser
    """
    parser = SitemapParser()

    # Example: Extract all URLs from a sitemap
    sitemap_url = "https://example.com/sitemap.xml"
    urls = parser.get_all_urls(
        sitemap_url,
        include_patterns=["/docs/", "/modules/"],
        exclude_patterns=["/tags/", "/blog/"]
    )

    for url in urls[:10]:  # Print first 10 URLs
        print(url)