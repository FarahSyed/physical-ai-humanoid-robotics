"""
Verification reporter module for generating reports on content quality and pipeline status
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.models.extracted_content import ExtractedContent
from src.utils.logger import logger


class VerificationReporter:
    """
    Generates comprehensive reports on content verification and pipeline status
    """

    def __init__(self, report_dir: str = "data/reports"):
        """
        Initialize the verification reporter

        Args:
            report_dir: Directory to store reports
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_extraction_report(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Generate a report on the extraction process

        Args:
            extracted_contents: List of extracted content items

        Returns:
            Dictionary with extraction report data
        """
        if not extracted_contents:
            return {
                "summary": {
                    "total_items": 0,
                    "total_chars": 0,
                    "total_words": 0,
                    "extraction_date": datetime.now().isoformat()
                },
                "content_types": {},
                "modules": {},
                "sections": {},
                "quality_metrics": {
                    "avg_content_length": 0,
                    "avg_word_count": 0
                }
            }

        total_chars = sum(len(content.content) for content in extracted_contents)
        total_words = sum(content.word_count or 0 for content in extracted_contents)

        # Count content types
        content_types = {}
        for content in extracted_contents:
            content_type = content.content_type or "unknown"
            content_types[content_type] = content_types.get(content_type, 0) + 1

        # Count modules and sections
        modules = {}
        sections = {}
        for content in extracted_contents:
            if content.module:
                modules[content.module] = modules.get(content.module, 0) + 1
            if content.section:
                sections[content.section] = sections.get(content.section, 0) + 1

        avg_content_length = total_chars / len(extracted_contents) if extracted_contents else 0
        avg_word_count = total_words / len(extracted_contents) if extracted_contents else 0

        return {
            "summary": {
                "total_items": len(extracted_contents),
                "total_chars": total_chars,
                "total_words": total_words,
                "extraction_date": datetime.now().isoformat()
            },
            "content_types": content_types,
            "modules": modules,
            "sections": sections,
            "quality_metrics": {
                "avg_content_length": avg_content_length,
                "avg_word_count": avg_word_count
            }
        }

    def generate_quality_report(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Generate a quality report for extracted content

        Args:
            extracted_contents: List of extracted content items

        Returns:
            Dictionary with quality report data
        """
        from src.storage.content_validator import ContentValidator

        validator = ContentValidator()
        validation_results = validator.validate_multiple_contents(extracted_contents)

        # Analyze content lengths
        content_lengths = [len(content.content) for content in extracted_contents]
        word_counts = [content.word_count or 0 for content in extracted_contents]

        return {
            "validation_summary": {
                "total_items": len(extracted_contents),
                "valid_items": validation_results['valid_count'],
                "invalid_items": validation_results['invalid_count'],
                "average_quality_score": validation_results['average_quality_score']
            },
            "content_analysis": {
                "avg_length": sum(content_lengths) / len(content_lengths) if content_lengths else 0,
                "min_length": min(content_lengths) if content_lengths else 0,
                "max_length": max(content_lengths) if content_lengths else 0,
                "avg_word_count": sum(word_counts) / len(word_counts) if word_counts else 0
            },
            "quality_distribution": validation_results['validation_summary']
        }

    def generate_embedding_report(self, embedding_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a report on embedding generation process

        Args:
            embedding_results: Results from embedding generation process

        Returns:
            Dictionary with embedding report data
        """
        return {
            "embedding_summary": {
                "status": embedding_results.get('status', 'unknown'),
                "upserted_count": embedding_results.get('upserted_count', 0),
                "batch_count": embedding_results.get('batch_count', 0),
                "collection_name": embedding_results.get('collection_name', 'unknown'),
                "timestamp": datetime.now().isoformat()
            },
            "deduplication_stats": embedding_results.get('deduplication', {}),
            "errors": embedding_results.get('error', None)
        }

    def generate_pipeline_report(self, extraction_report: Dict[str, Any],
                                quality_report: Dict[str, Any],
                                embedding_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive pipeline report combining all stages

        Args:
            extraction_report: Report from extraction stage
            quality_report: Report from quality validation stage
            embedding_report: Report from embedding stage

        Returns:
            Dictionary with comprehensive pipeline report
        """
        return {
            "pipeline_report": {
                "generated_at": datetime.now().isoformat(),
                "stages": {
                    "extraction": extraction_report,
                    "quality_validation": quality_report,
                    "embedding": embedding_report
                },
                "summary": {
                    "total_extracted": extraction_report['summary']['total_items'],
                    "valid_for_embedding": quality_report['validation_summary']['valid_items'],
                    "embedded_count": embedding_report['embedding_summary']['upserted_count'],
                    "success_rate": (
                        embedding_report['embedding_summary']['upserted_count'] /
                        extraction_report['summary']['total_items']
                        if extraction_report['summary']['total_items'] > 0 else 0
                    )
                }
            }
        }

    def save_report(self, report_data: Dict[str, Any], filename: str = None,
                   report_type: str = "pipeline") -> str:
        """
        Save a report to a file

        Args:
            report_data: Report data to save
            filename: Name of the file to save (auto-generated if not provided)
            report_type: Type of report for naming convention

        Returns:
            Path to the saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_report_{timestamp}.json"

        filepath = self.report_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Saved {report_type} report to {filepath}")
        return str(filepath)

    def generate_detailed_report(self, extracted_contents: List[ExtractedContent],
                                embedding_results: Dict[str, Any]) -> str:
        """
        Generate a detailed text report for human consumption

        Args:
            extracted_contents: List of extracted content items
            embedding_results: Results from embedding generation

        Returns:
            Formatted text report
        """
        from src.storage.content_validator import ContentValidator

        validator = ContentValidator()
        validation_results = validator.get_content_quality_report(extracted_contents)

        report = []
        report.append("=" * 80)
        report.append("RAG PIPELINE DETAILED REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Extraction Summary
        report.append("EXTRACTION SUMMARY:")
        report.append(f"  Total Content Items: {len(extracted_contents)}")
        if extracted_contents:
            total_chars = sum(len(content.content) for content in extracted_contents)
            total_words = sum(content.word_count or 0 for content in extracted_contents)
            report.append(f"  Total Characters: {total_chars:,}")
            report.append(f"  Total Words: {total_words:,}")
            report.append(f"  Average Length: {total_chars/len(extracted_contents):.0f} chars")
            report.append(f"  Average Words: {total_words/len(extracted_contents):.1f}")
        report.append("")

        # Quality Summary
        report.append("QUALITY SUMMARY:")
        report.append(f"  Valid Items: {validation_results['valid_items']}")
        report.append(f"  Invalid Items: {validation_results['invalid_items']}")
        report.append(f"  Average Quality Score: {validation_results['average_quality_score']:.2f}")
        report.append(f"  Min Quality Score: {validation_results['min_quality_score']:.2f}")
        report.append(f"  Max Quality Score: {validation_results['max_quality_score']:.2f}")
        report.append("")

        # Quality Distribution
        report.append("QUALITY DISTRIBUTION:")
        dist = validation_results['quality_distribution']
        report.append(f"  Excellent (0.8-1.0): {dist['excellent']}")
        report.append(f"  Good (0.6-0.8): {dist['good']}")
        report.append(f"  Fair (0.4-0.6): {dist['fair']}")
        report.append(f"  Poor (<0.4): {dist['poor']}")
        report.append("")

        # Embedding Results
        report.append("EMBEDDING RESULTS:")
        emb_summary = embedding_results.get('embedding_summary', {})
        report.append(f"  Status: {emb_summary.get('status', 'unknown')}")
        report.append(f"  Items Embedded: {emb_summary.get('upserted_count', 0)}")
        report.append(f"  Batches Processed: {emb_summary.get('batch_count', 0)}")
        report.append(f"  Collection: {emb_summary.get('collection_name', 'unknown')}")
        report.append("")

        # Deduplication Stats
        dedup_stats = embedding_results.get('deduplication', {})
        if dedup_stats:
            report.append("DEDUPLICATION STATS:")
            report.append(f"  Original Count: {dedup_stats.get('original_count', 0)}")
            report.append(f"  Unique Count: {dedup_stats.get('unique_count', 0)}")
            report.append(f"  Duplicates Removed: {dedup_stats.get('duplicates_removed', 0)}")
        report.append("")

        # Invalid Content Samples (first 5)
        if validation_results['invalid_content_details']:
            report.append("INVALID CONTENT SAMPLES (first 5):")
            for i, item in enumerate(validation_results['invalid_content_details'][:5], 1):
                report.append(f"  {i}. {item['url'][:50]}{'...' if len(item['url']) > 50 else ''}")
                report.append(f"     Score: {item['score']:.2f}")
                report.append(f"     Issues: {', '.join(item['issues'])}")
                report.append("")
        else:
            report.append("INVALID CONTENT SAMPLES: None found")
        report.append("")

        # Success Metrics
        success_rate = (emb_summary.get('upserted_count', 0) / len(extracted_contents)) if extracted_contents else 0
        report.append("SUCCESS METRICS:")
        report.append(f"  Extraction to Embedding Success Rate: {success_rate:.1%}")
        report.append(f"  Quality Threshold Met: {validation_results['valid_items'] / len(extracted_contents) >= 0.8 if extracted_contents else False:.1%}")
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def save_detailed_report(self, extracted_contents: List[ExtractedContent],
                           embedding_results: Dict[str, Any], filename: str = None) -> str:
        """
        Save a detailed text report to a file

        Args:
            extracted_contents: List of extracted content items
            embedding_results: Results from embedding generation
            filename: Name of the file to save (auto-generated if not provided)

        Returns:
            Path to the saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_report_{timestamp}.txt"

        filepath = self.report_dir / filename

        detailed_report = self.generate_detailed_report(extracted_contents, embedding_results)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(detailed_report)

        logger.info(f"Saved detailed report to {filepath}")
        return str(filepath)

    def generate_system_report(self) -> Dict[str, Any]:
        """
        Generate a system-level report showing the status of the RAG pipeline

        Returns:
            Dictionary with system report data
        """
        # Get statistics about stored content
        storage_stats = self._get_storage_statistics()

        return {
            "system_report": {
                "generated_at": datetime.now().isoformat(),
                "storage_stats": storage_stats,
                "environment": {
                    "qdrant_host": os.getenv("QDRANT_HOST", "not set"),
                    "cohere_api_key_set": bool(os.getenv("COHERE_API_KEY")),
                    "frontend_sitemap_url": os.getenv("FRONTEND_SITEMAP_URL", "not set")
                }
            }
        }

    def _get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the storage directories

        Returns:
            Dictionary with storage statistics
        """
        import shutil

        def get_directory_size(path):
            """Get the size of a directory in bytes"""
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size

        # Define storage directories to check
        storage_paths = {
            "raw_text": "data/raw_text",
            "metadata": "data/metadata",
            "reports": "data/reports"
        }

        stats = {}
        for name, path in storage_paths.items():
            path_obj = Path(path)
            if path_obj.exists():
                file_count = len(list(path_obj.glob("**/*")))
                size_bytes = get_directory_size(path)
                stats[name] = {
                    "exists": True,
                    "file_count": file_count,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "size_bytes": size_bytes
                }
            else:
                stats[name] = {
                    "exists": False,
                    "file_count": 0,
                    "size_mb": 0,
                    "size_bytes": 0
                }

        return stats


def example_usage():
    """
    Example of how to use the VerificationReporter
    """
    # This would be used in practice with actual extracted content and embedding results
    print("VerificationReporter example usage would go here.")
    print("This module is typically used after extraction and embedding processes.")


if __name__ == "__main__":
    example_usage()