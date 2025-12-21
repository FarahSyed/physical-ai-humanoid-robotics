"""
Unit tests for the sitemap parser
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from src.crawler.sitemap_parser import SitemapParser


class TestSitemapParser:
    """Test cases for SitemapParser class"""

    def test_sitemap_parser_initialization(self):
        """Test that SitemapParser initializes correctly"""
        parser = SitemapParser(timeout=60)
        assert parser.timeout == 60

        # Test default timeout
        parser = SitemapParser()
        assert parser.timeout == 30

    @patch('src.crawler.sitemap_parser.requests.get')
    def test_fetch_sitemap_success(self, mock_get):
        """Test successful fetching of sitemap"""
        # Mock response
        mock_response = Mock()
        mock_response.text = "<xml>sitemap content</xml>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        parser = SitemapParser()
        result = parser.fetch_sitemap("https://example.com/sitemap.xml")

        assert result == "<xml>sitemap content</xml>"
        mock_get.assert_called_once_with("https://example.com/sitemap.xml", timeout=30)

    @patch('src.crawler.sitemap_parser.requests.get')
    def test_fetch_sitemap_request_exception(self, mock_get):
        """Test handling of request exceptions when fetching sitemap"""
        # Mock request exception
        mock_get.side_effect = Exception("Network error")

        parser = SitemapParser()
        result = parser.fetch_sitemap("https://example.com/sitemap.xml")

        assert result is None

    @patch('src.crawler.sitemap_parser.requests.get')
    def test_fetch_sitemap_http_error(self, mock_get):
        """Test handling of HTTP errors when fetching sitemap"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_get.return_value = mock_response

        parser = SitemapParser()
        result = parser.fetch_sitemap("https://example.com/sitemap.xml")

        assert result is None

    def test_parse_sitemap_content_valid_xml(self):
        """Test parsing valid sitemap XML content"""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
                <lastmod>2023-01-02</lastmod>
            </url>
        </urlset>"""

        parser = SitemapParser()
        urls = parser.parse_sitemap_content(sitemap_content)

        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    def test_parse_sitemap_content_with_namespace(self):
        """Test parsing sitemap XML content with namespace"""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/namespace-page</loc>
            </url>
        </urlset>"""

        parser = SitemapParser()
        urls = parser.parse_sitemap_content(sitemap_content)

        assert len(urls) == 1
        assert urls[0] == "https://example.com/namespace-page"

    def test_parse_sitemap_content_invalid_xml(self):
        """Test handling of invalid XML content"""
        invalid_content = "<invalid>xml content without proper closing"

        parser = SitemapParser()
        urls = parser.parse_sitemap_content(invalid_content)

        assert urls == []

    def test_parse_sitemap_content_empty_content(self):
        """Test parsing empty sitemap content"""
        parser = SitemapParser()
        urls = parser.parse_sitemap_content("")

        assert urls == []

    def test_parse_sitemap_index_valid(self):
        """Test parsing valid sitemap index XML content"""
        sitemap_index_content = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap1.xml</loc>
                <lastmod>2023-01-01</lastmod>
            </sitemap>
            <sitemap>
                <loc>https://example.com/sitemap2.xml</loc>
                <lastmod>2023-01-02</lastmod>
            </sitemap>
        </sitemapindex>"""

        parser = SitemapParser()
        sitemap_urls = parser.parse_sitemap_index(sitemap_index_content)

        assert len(sitemap_urls) == 2
        assert "https://example.com/sitemap1.xml" in sitemap_urls
        assert "https://example.com/sitemap2.xml" in sitemap_urls

    def test_parse_sitemap_index_invalid_xml(self):
        """Test handling of invalid sitemap index XML content"""
        invalid_content = "<invalid>xml content"

        parser = SitemapParser()
        sitemap_urls = parser.parse_sitemap_index(invalid_content)

        assert sitemap_urls == []

    def test_normalize_and_filter_urls_basic(self):
        """Test basic URL normalization and filtering"""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://other.com/page3"
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(urls)

        assert len(result) == 3
        assert set(result) == set(urls)

    def test_normalize_and_filter_urls_with_base_url(self):
        """Test URL normalization with base URL"""
        urls = [
            "/page1",
            "page2",
            "/docs/guide"
        ]
        base_url = "https://example.com"

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(urls, base_url=base_url)

        expected = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/docs/guide"
        ]

        assert len(result) == 3
        for exp in expected:
            assert exp in result

    def test_normalize_and_filter_urls_with_include_patterns(self):
        """Test URL filtering with include patterns"""
        urls = [
            "https://example.com/docs/guide1",
            "https://example.com/api/ref",
            "https://example.com/blog/post",
            "https://example.com/docs/guide2"
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(
            urls,
            include_patterns=["/docs/"]
        )

        assert len(result) == 2
        assert "https://example.com/docs/guide1" in result
        assert "https://example.com/docs/guide2" in result
        assert "https://example.com/api/ref" not in result
        assert "https://example.com/blog/post" not in result

    def test_normalize_and_filter_urls_with_exclude_patterns(self):
        """Test URL filtering with exclude patterns"""
        urls = [
            "https://example.com/docs/guide1",
            "https://example.com/tags/react",
            "https://example.com/blog/post",
            "https://example.com/tags/python"
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(
            urls,
            exclude_patterns=["/tags/"]
        )

        assert len(result) == 2
        assert "https://example.com/docs/guide1" in result
        assert "https://example.com/blog/post" in result
        assert "https://example.com/tags/react" not in result
        assert "https://example.com/tags/python" not in result

    def test_normalize_and_filter_urls_with_both_patterns(self):
        """Test URL filtering with both include and exclude patterns"""
        urls = [
            "https://example.com/docs/guide1",
            "https://example.com/docs/api",
            "https://example.com/tags/react",
            "https://example.com/blog/post"
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(
            urls,
            include_patterns=["/docs/"],
            exclude_patterns=["/api"]
        )

        assert len(result) == 1
        assert "https://example.com/docs/guide1" in result
        assert "https://example.com/docs/api" not in result

    def test_normalize_and_filter_urls_removes_duplicates(self):
        """Test that duplicate URLs are removed"""
        urls = [
            "https://example.com/page1",
            "https://example.com/page1",  # duplicate
            "https://example.com/page2"
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(urls)

        assert len(result) == 2
        assert result.count("https://example.com/page1") == 1

    def test_normalize_and_filter_urls_removes_invalid_urls(self):
        """Test that invalid URLs are removed"""
        urls = [
            "https://example.com/valid",
            "invalid-url",
            "/relative-url",  # without base_url, this might be filtered
            ""
        ]

        parser = SitemapParser()
        result = parser.normalize_and_filter_urls(urls)

        assert "https://example.com/valid" in result
        # Invalid URLs should be filtered out

    @patch.object(SitemapParser, 'fetch_sitemap')
    def test_extract_urls_from_sitemap_regular_sitemap(self, mock_fetch_sitemap):
        """Test extracting URLs from a regular sitemap (not index)"""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
            </url>
        </urlset>"""

        mock_fetch_sitemap.return_value = sitemap_content

        parser = SitemapParser()
        urls = parser.extract_urls_from_sitemap("https://example.com/sitemap.xml")

        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    @patch.object(SitemapParser, 'fetch_sitemap')
    def test_extract_urls_from_sitemap_sitemap_index(self, mock_fetch_sitemap):
        """Test extracting URLs from a sitemap index"""
        # First call returns sitemap index
        # Subsequent calls return individual sitemaps
        sitemap_index_content = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap1.xml</loc>
            </sitemap>
        </sitemapindex>"""

        sitemap1_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
            </url>
        </urlset>"""

        def side_effect(url):
            if url == "https://example.com/sitemap.xml":
                return sitemap_index_content
            elif url == "https://example.com/sitemap1.xml":
                return sitemap1_content
            return ""

        mock_fetch_sitemap.side_effect = side_effect

        parser = SitemapParser()
        urls = parser.extract_urls_from_sitemap("https://example.com/sitemap.xml")

        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    @patch.object(SitemapParser, 'extract_urls_from_sitemap')
    @patch.object(SitemapParser, 'normalize_and_filter_urls')
    def test_get_all_urls_integration(self, mock_normalize, mock_extract):
        """Test the full get_all_urls method"""
        # Mock the extraction to return some URLs
        mock_extract.return_value = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]

        # Mock the normalization to return filtered URLs
        mock_normalize.return_value = [
            "https://example.com/page1",
            "https://example.com/page2"
        ]

        parser = SitemapParser()
        result = parser.get_all_urls(
            "https://example.com/sitemap.xml",
            include_patterns=["/page"],
            exclude_patterns=["/page3"]
        )

        # Verify the extraction was called
        mock_extract.assert_called_once_with("https://example.com/sitemap.xml")

        # Verify the normalization was called with the right parameters
        mock_normalize.assert_called_once()
        args, kwargs = mock_normalize.call_args
        assert args[0] == ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
        assert kwargs["include_patterns"] == ["/page"]
        assert kwargs["exclude_patterns"] == ["/page3"]

        # Verify the result
        assert result == ["https://example.com/page1", "https://example.com/page2"]


if __name__ == "__main__":
    pytest.main([__file__])