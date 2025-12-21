"""
Pre-embedding verification module to ensure content quality before embedding generation
"""
from typing import List, Dict, Any
from src.models.extracted_content import ExtractedContent
from src.storage.content_validator import ContentValidator
from src.utils.logger import logger


class PreEmbeddingChecker:
    """
    Verifies content quality and completeness before embedding generation begins
    """

    def __init__(self):
        self.validator = ContentValidator()

    def check_content_quality(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Check the overall quality of extracted content before embedding

        Args:
            extracted_contents: List of ExtractedContent objects to check

        Returns:
            Dictionary with quality check results
        """
        if not extracted_contents:
            return {
                "valid": False,
                "message": "No content provided for embedding",
                "quality_score": 0.0,
                "issues": ["No content to process"]
            }

        # Validate all content items
        validation_results = self.validator.validate_multiple_contents(extracted_contents)

        # Calculate overall quality metrics
        total_items = len(extracted_contents)
        valid_items = validation_results['valid_count']
        avg_quality_score = validation_results['average_quality_score']

        # Determine if content is of sufficient quality for embedding
        quality_threshold_met = valid_items / total_items >= 0.8  # At least 80% must be valid
        avg_quality_acceptable = avg_quality_score >= 0.5  # Average quality score should be 0.5 or higher

        issues = []
        if not quality_threshold_met:
            issues.append(f"Less than 80% of content items are valid ({valid_items}/{total_items})")

        if not avg_quality_acceptable:
            issues.append(f"Average quality score too low ({avg_quality_score:.2f} < 0.5)")

        return {
            "valid": quality_threshold_met and avg_quality_acceptable,
            "message": f"Quality check passed for {valid_items}/{total_items} items with avg score {avg_quality_score:.2f}",
            "quality_score": avg_quality_score,
            "valid_count": valid_items,
            "total_count": total_items,
            "issues": issues,
            "quality_report": validation_results
        }

    def check_content_diversity(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Check if the content has sufficient diversity to be valuable for embeddings

        Args:
            extracted_contents: List of ExtractedContent objects to check

        Returns:
            Dictionary with diversity check results
        """
        if not extracted_contents:
            return {
                "diverse": False,
                "message": "No content to analyze for diversity",
                "issues": ["No content provided"]
            }

        # Check for content duplication
        content_hashes = set()
        duplicate_count = 0
        total_content = len(extracted_contents)

        for content in extracted_contents:
            if content.content_hash in content_hashes:
                duplicate_count += 1
            else:
                content_hashes.add(content.content_hash)

        # Check for topic diversity (basic check based on titles)
        unique_titles = set(content.title.lower().strip() for content in extracted_contents)
        title_similarity_ratio = len(unique_titles) / total_content if total_content > 0 else 0

        # Check content length distribution
        content_lengths = [len(content.content) for content in extracted_contents]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        min_length = min(content_lengths) if content_lengths else 0

        issues = []
        if duplicate_count > total_content * 0.5:  # More than 50% duplicates
            issues.append(f"High duplication detected: {duplicate_count}/{total_content} items are duplicates")

        if title_similarity_ratio < 0.7:  # Less than 70% unique titles
            issues.append(f"Low title diversity: only {len(unique_titles)}/{total_content} unique titles")

        if avg_length < 100:  # Average content too short
            issues.append(f"Content too short: average length is {avg_length:.1f} characters")

        return {
            "diverse": len(issues) == 0,
            "message": f"Analyzed diversity of {total_content} content items",
            "duplicate_count": duplicate_count,
            "unique_titles_ratio": title_similarity_ratio,
            "average_length": avg_length,
            "min_length": min_length,
            "issues": issues
        }

    def check_content_completeness(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Check if the content is complete and properly structured

        Args:
            extracted_contents: List of ExtractedContent objects to check

        Returns:
            Dictionary with completeness check results
        """
        if not extracted_contents:
            return {
                "complete": False,
                "message": "No content to analyze for completeness",
                "issues": ["No content provided"]
            }

        issues = []
        total_items = len(extracted_contents)
        items_with_issues = 0

        for content in extracted_contents:
            item_issues = []

            # Check if essential fields are present
            if not content.url:
                item_issues.append("Missing URL")
            if not content.title or len(content.title.strip()) < 2:
                item_issues.append("Missing or very short title")
            if not content.content or len(content.content.strip()) < 10:
                item_issues.append("Missing or very short content")
            if not content.id:
                item_issues.append("Missing ID")

            # Check content structure
            if content.metadata:
                # Check if metadata has essential information
                if not content.metadata.get('word_count') or content.metadata['word_count'] < 10:
                    item_issues.append("Invalid word count in metadata")

            if item_issues:
                items_with_issues += 1
                issues.extend([f"Item {content.id[:8]}: {issue}" for issue in item_issues])

        completeness_ratio = (total_items - items_with_issues) / total_items if total_items > 0 else 0
        return {
            "complete": completeness_ratio >= 0.9,  # At least 90% of items should be complete
            "message": f"Completeness check: {total_items - items_with_issues}/{total_items} items complete",
            "complete_count": total_items - items_with_issues,
            "total_count": total_items,
            "completeness_ratio": completeness_ratio,
            "issues": issues
        }

    def run_pre_embedding_verification(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Run comprehensive pre-embedding verification

        Args:
            extracted_contents: List of ExtractedContent objects to verify

        Returns:
            Dictionary with comprehensive verification results
        """
        logger.info(f"Starting pre-embedding verification for {len(extracted_contents)} content items")

        # Run all checks
        quality_check = self.check_content_quality(extracted_contents)
        diversity_check = self.check_content_diversity(extracted_contents)
        completeness_check = self.check_content_completeness(extracted_contents)

        # Overall verification result
        overall_valid = (
            quality_check["valid"] and
            diversity_check["diverse"] and
            completeness_check["complete"]
        )

        issues = []
        issues.extend(quality_check.get("issues", []))
        issues.extend(diversity_check.get("issues", []))
        issues.extend(completeness_check.get("issues", []))

        verification_result = {
            "overall_valid": overall_valid,
            "message": "Pre-embedding verification passed" if overall_valid else "Pre-embedding verification failed",
            "quality_check": quality_check,
            "diversity_check": diversity_check,
            "completeness_check": completeness_check,
            "total_issues": len(issues),
            "issues": issues,
            "content_count": len(extracted_contents)
        }

        if overall_valid:
            logger.info(f"Pre-embedding verification PASSED for {len(extracted_contents)} items")
        else:
            logger.warning(f"Pre-embedding verification FAILED. Issues found: {len(issues)}")

        return verification_result

    def get_verification_report(self, extracted_contents: List[ExtractedContent]) -> str:
        """
        Generate a text report of the pre-embedding verification

        Args:
            extracted_contents: List of ExtractedContent objects to verify

        Returns:
            Formatted text report
        """
        from datetime import datetime

        verification = self.run_pre_embedding_verification(extracted_contents)

        report = []
        report.append("=" * 70)
        report.append("PRE-EMBEDDING VERIFICATION REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Content Items: {verification['content_count']}")
        report.append(f"Overall Status: {'PASS' if verification['overall_valid'] else 'FAIL'}")
        report.append("")

        # Quality check results
        quality = verification['quality_check']
        report.append("QUALITY CHECK:")
        report.append(f"  Status: {'PASS' if quality['valid'] else 'FAIL'}")
        report.append(f"  Valid Items: {quality['valid_count']}/{quality['total_count']}")
        report.append(f"  Average Quality Score: {quality['quality_score']:.2f}")
        report.append("")

        # Diversity check results
        diversity = verification['diversity_check']
        report.append("DIVERSITY CHECK:")
        report.append(f"  Status: {'PASS' if diversity['diverse'] else 'FAIL'}")
        report.append(f"  Duplicate Count: {diversity['duplicate_count']}")
        report.append(f"  Unique Titles Ratio: {diversity['unique_titles_ratio']:.2f}")
        report.append(f"  Average Length: {diversity['average_length']:.1f}")
        report.append("")

        # Completeness check results
        completeness = verification['completeness_check']
        report.append("COMPLETENESS CHECK:")
        report.append(f"  Status: {'PASS' if completeness['complete'] else 'FAIL'}")
        report.append(f"  Complete Items: {completeness['complete_count']}/{completeness['total_count']}")
        report.append(f"  Completeness Ratio: {completeness['completeness_ratio']:.2f}")
        report.append("")

        # Issues
        if verification['issues']:
            report.append("ISSUES FOUND:")
            for i, issue in enumerate(verification['issues'][:10], 1):  # Limit to first 10 issues
                report.append(f"  {i}. {issue}")
            if len(verification['issues']) > 10:
                report.append(f"  ... and {len(verification['issues']) - 10} more issues")
        else:
            report.append("ISSUES FOUND: None")

        report.append("")
        report.append(f"TOTAL ISSUES: {verification['total_issues']}")
        report.append("=" * 70)

        return "\n".join(report)


class ContentQualityGates:
    """
    Implements quality gates that must be passed before content proceeds to embedding
    """

    def __init__(self, min_quality_score: float = 0.5, min_content_length: int = 50,
                 max_duplicate_ratio: float = 0.1, min_items_required: int = 1):
        """
        Initialize quality gates with thresholds

        Args:
            min_quality_score: Minimum quality score for individual content
            min_content_length: Minimum content length in characters
            max_duplicate_ratio: Maximum ratio of duplicate content allowed
            min_items_required: Minimum number of items required
        """
        self.min_quality_score = min_quality_score
        self.min_content_length = min_content_length
        self.max_duplicate_ratio = max_duplicate_ratio
        self.min_items_required = min_items_required

    def apply_gates(self, extracted_contents: List[ExtractedContent]) -> List[ExtractedContent]:
        """
        Apply quality gates to filter content

        Args:
            extracted_contents: List of ExtractedContent objects to filter

        Returns:
            Filtered list of ExtractedContent objects that pass all gates
        """
        initial_count = len(extracted_contents)
        logger.info(f"Applying quality gates to {initial_count} content items")

        # Gate 1: Minimum items required
        if len(extracted_contents) < self.min_items_required:
            logger.warning(f"Insufficient content items: {len(extracted_contents)} < {self.min_items_required}")
            return []

        # Gate 2: Individual content quality
        validator = ContentValidator()
        filtered_contents = []

        for content in extracted_contents:
            validation = validator.validate_content(content)
            if (validation['valid'] and
                validation['quality_score'] >= self.min_quality_score and
                len(content.content) >= self.min_content_length):
                filtered_contents.append(content)
            else:
                logger.debug(f"Content failed quality gates: {content.url} (score: {validation['quality_score']:.2f})")

        # Gate 3: Duplicate content check
        unique_contents = []
        seen_hashes = set()

        for content in filtered_contents:
            if content.content_hash not in seen_hashes:
                unique_contents.append(content)
                seen_hashes.add(content.content_hash)

        # Check if duplicate ratio is acceptable
        original_count = len(filtered_contents)
        final_count = len(unique_contents)
        duplicate_ratio = (original_count - final_count) / original_count if original_count > 0 else 0

        if duplicate_ratio > self.max_duplicate_ratio:
            logger.warning(f"Too many duplicates after filtering: {duplicate_ratio:.2f} > {self.max_duplicate_ratio}")
            # In this case, we'll still return the unique content but log the issue
            logger.info(f"Quality gates reduced {initial_count} -> {final_count} unique content items")

        logger.info(f"Quality gates reduced {initial_count} -> {len(unique_contents)} content items")
        return unique_contents