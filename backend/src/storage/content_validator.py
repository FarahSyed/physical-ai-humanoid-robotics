"""
Content validator module for validating extracted content quality before embedding
"""
from typing import List, Dict, Any
from src.models.extracted_content import ExtractedContent
from src.utils.logger import logger


class ContentValidator:
    """
    Validates extracted content quality and completeness before embedding generation
    """

    def __init__(self):
        pass

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
            results['issues'].append('Content too short (<50 characters)')
            results['suggestions'].append('Ensure the page contains substantial content')
        elif content_length < 200:
            results['quality_score'] += 0.3
            results['suggestions'].append('Content is quite short, consider if more content is available')
        elif content_length < 1000:
            results['quality_score'] += 0.6
        else:
            results['quality_score'] += 0.8

        # Check title
        if not extracted_content.title or len(extracted_content.title.strip()) < 3:
            results['valid'] = False
            results['issues'].append('Title too short or missing')
        else:
            results['quality_score'] += 0.15

        # Check URL
        if not extracted_content.url:
            results['valid'] = False
            results['issues'].append('URL missing')
        else:
            results['quality_score'] += 0.05

        # Check for common issues
        if extracted_content.content and '404' in extracted_content.content:
            results['issues'].append('Possible 404 error page detected')
            results['valid'] = False

        if extracted_content.content and 'access denied' in extracted_content.content.lower():
            results['issues'].append('Access denied page detected')
            results['valid'] = False

        # Check for excessive repetition which might indicate poor content
        if content_length > 100:
            # Check if the same sentence appears multiple times
            sentences = extracted_content.content.split('.')
            unique_sentences = set(s.strip() for s in sentences if s.strip())
            if len(sentences) > 10 and len(unique_sentences) / len(sentences) < 0.3:
                results['issues'].append('High content repetition detected')
                results['quality_score'] -= 0.2
                if results['quality_score'] < 0:
                    results['quality_score'] = 0

        # Ensure quality score is between 0 and 1
        results['quality_score'] = min(1.0, max(0.0, results['quality_score']))

        return results

    def validate_multiple_contents(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Validate multiple extracted content items and return overall statistics

        Args:
            extracted_contents: List of ExtractedContent objects to validate

        Returns:
            Dictionary with validation statistics
        """
        total_count = len(extracted_contents)
        valid_contents = []
        invalid_contents = []
        total_quality_score = 0.0

        for content in extracted_contents:
            validation = self.validate_content(content)
            total_quality_score += validation['quality_score']

            if validation['valid']:
                valid_contents.append({
                    'content': content,
                    'validation': validation
                })
            else:
                invalid_contents.append({
                    'content': content,
                    'validation': validation
                })

        avg_quality_score = total_quality_score / total_count if total_count > 0 else 0.0

        return {
            'total_count': total_count,
            'valid_count': len(valid_contents),
            'invalid_count': len(invalid_contents),
            'average_quality_score': avg_quality_score,
            'valid_contents': valid_contents,
            'invalid_contents': invalid_contents,
            'validation_passed': len(valid_contents) / total_count >= 0.8 if total_count > 0 else True  # At least 80% must pass
        }

    def filter_content(self, extracted_contents: List[ExtractedContent], min_quality_score: float = 0.5) -> List[ExtractedContent]:
        """
        Filter out low-quality content based on quality score

        Args:
            extracted_contents: List of ExtractedContent objects
            min_quality_score: Minimum quality score for content to be included

        Returns:
            Filtered list of ExtractedContent objects
        """
        filtered_contents = []

        for content in extracted_contents:
            validation = self.validate_content(content)
            if validation['valid'] and validation['quality_score'] >= min_quality_score:
                filtered_contents.append(content)
            else:
                logger.info(f"Filtered out low-quality content from {content.url} (score: {validation['quality_score']:.2f}): {validation['issues']}")

        logger.info(f"Filtered {len(extracted_contents)} -> {len(filtered_contents)} content items based on quality (min score: {min_quality_score})")
        return filtered_contents

    def check_content_for_embedding(self, extracted_content: ExtractedContent) -> bool:
        """
        Check if content meets requirements for embedding generation

        Args:
            extracted_content: ExtractedContent object to check

        Returns:
            True if content is suitable for embedding, False otherwise
        """
        validation = self.validate_content(extracted_content)
        return validation['valid'] and validation['quality_score'] >= 0.5

    def get_content_quality_report(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """
        Generate a detailed quality report for a list of extracted contents

        Args:
            extracted_contents: List of ExtractedContent objects

        Returns:
            Dictionary with detailed quality metrics
        """
        if not extracted_contents:
            return {"message": "No content to analyze"}

        validation_results = [self.validate_content(content) for content in extracted_contents]

        quality_scores = [result['quality_score'] for result in validation_results]
        valid_count = sum(1 for result in validation_results if result['valid'])
        invalid_items = [
            {
                'url': extracted_contents[i].url,
                'issues': result['issues'],
                'score': result['quality_score']
            }
            for i, result in enumerate(validation_results) if not result['valid']
        ]

        return {
            'total_items': len(extracted_contents),
            'valid_items': valid_count,
            'invalid_items': len(invalid_items),
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'min_quality_score': min(quality_scores) if quality_scores else 0,
            'max_quality_score': max(quality_scores) if quality_scores else 0,
            'invalid_content_details': invalid_items,
            'quality_distribution': {
                'excellent': sum(1 for score in quality_scores if score >= 0.8),
                'good': sum(1 for score in quality_scores if 0.6 <= score < 0.8),
                'fair': sum(1 for score in quality_scores if 0.4 <= score < 0.6),
                'poor': sum(1 for score in quality_scores if score < 0.4)
            }
        }