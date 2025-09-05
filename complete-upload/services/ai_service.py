"""
AI Service for Gemini Integration

This module handles interactions with Google's Gemini AI models for
code review analysis and comment generation.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

import google.generativeai as genai
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class AIService:
    """Service for interacting with Gemini AI models."""
    
    def __init__(self):
        """Initialize the AI service with Gemini configuration."""
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize models
        self.pro_model = genai.GenerativeModel(settings.gemini_model_pro)
        self.flash_model = genai.GenerativeModel(settings.gemini_model_flash)
        
        # Load review prompt template
        self.review_prompt_template = self._load_review_prompt()
        
        logger.info("AI service initialized", models=[settings.gemini_model_pro, settings.gemini_model_flash])
    
    def _load_review_prompt(self) -> str:
        """Load the review prompt template."""
        try:
            with open("config/prompts/review_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Review prompt template not found, using default")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default review prompt if template file is not found."""
        return """You are a senior code reviewer with expertise in multiple programming languages and frameworks. Your task is to review code changes in a Pull Request and provide actionable feedback.

## Your Role
- Be precise, concise, and constructive
- Focus on critical issues: bugs, security vulnerabilities, performance problems, and architectural concerns
- Avoid style nitpicks unless they violate established coding standards
- Suggest specific fixes with code examples when possible
- Consider the context of the codebase and the intent of the changes

## Review Guidelines

### High Priority Issues (severity: "high")
- Security vulnerabilities (SQL injection, XSS, authentication bypass, etc.)
- Potential bugs that could cause crashes or data corruption
- Performance issues that could impact user experience
- Breaking changes that aren't properly documented
- Missing error handling for critical operations

### Medium Priority Issues (severity: "medium")
- Code that could be simplified or made more maintainable
- Potential edge cases not handled
- Inconsistent patterns with the rest of the codebase
- Missing tests for complex logic
- Performance optimizations that could be beneficial

### Low Priority Issues (severity: "low")
- Minor code style inconsistencies
- Documentation improvements
- Variable naming suggestions
- Code organization suggestions

### Nitpicks (severity: "nit")
- Very minor style issues
- Personal preference suggestions
- Cosmetic improvements

## Output Format
You must respond with valid JSON matching this exact schema:

```json
{
  "inline_comments": [
    {
      "path": "src/file.js",
      "start_line": 42,
      "end_line": 42,
      "severity": "high|medium|low|nit",
      "category": "security|performance|bug|style|architecture|testing",
      "comment": "Precise, actionable feedback with specific fix suggestion if applicable."
    }
  ],
  "summary": "Overall assessment of the PR with key highlights and recommendations.",
  "tests_to_add": ["List of specific tests that should be added"],
  "risk": "Low|Medium|High",
  "breaking_changes": false,
  "approval_recommendation": "approve|request_changes|comment"
}
```

## Context Information
- Language: {language}
- Framework: {framework}
- File changes: {file_count} files modified
- Lines changed: {lines_added} added, {lines_removed} removed

## Static Analysis Results
{static_analysis_results}

## Code Changes
{code_diff}

## Instructions
1. Analyze the code changes carefully
2. Identify issues based on the severity guidelines above
3. Provide specific, actionable feedback
4. Consider the overall impact and risk of the changes
5. Output only valid JSON - no additional text or formatting"""
    
    def _format_prompt(self, 
                      language: str,
                      framework: str,
                      file_count: int,
                      lines_added: int,
                      lines_removed: int,
                      static_analysis_results: str,
                      code_diff: str) -> str:
        """Format the review prompt with context information."""
        return self.review_prompt_template.format(
            language=language,
            framework=framework,
            file_count=file_count,
            lines_added=lines_added,
            lines_removed=lines_removed,
            static_analysis_results=static_analysis_results,
            code_diff=code_diff
        )
    
    def _detect_language_and_framework(self, file_paths: List[str], languages: Dict[str, int]) -> Tuple[str, str]:
        """Detect the primary language and framework from file paths and language stats."""
        # Determine primary language from GitHub language stats
        primary_language = max(languages.items(), key=lambda x: x[1])[0].lower() if languages else "unknown"
        
        # Detect framework from file paths
        framework = "unknown"
        
        # Check for common frameworks
        if any("package.json" in path for path in file_paths):
            # Check for React, Next.js, Angular, etc.
            if any("next.config" in path for path in file_paths):
                framework = "Next.js"
            elif any("angular.json" in path for path in file_paths):
                framework = "Angular"
            elif any("src/components" in path for path in file_paths):
                framework = "React"
            else:
                framework = "Node.js"
        elif any("requirements.txt" in path for path in file_paths):
            # Check for Django, Flask, FastAPI, etc.
            if any("django" in path for path in file_paths):
                framework = "Django"
            elif any("flask" in path for path in file_paths):
                framework = "Flask"
            elif any("fastapi" in path for path in file_paths):
                framework = "FastAPI"
            else:
                framework = "Python"
        elif any("pom.xml" in path for path in file_paths):
            framework = "Maven"
        elif any("build.gradle" in path for path in file_paths):
            framework = "Gradle"
        
        return primary_language, framework
    
    def _validate_review_response(self, response: str) -> Dict[str, Any]:
        """Validate and parse the AI review response."""
        try:
            # Try to parse as JSON
            review_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["inline_comments", "summary", "risk", "breaking_changes", "approval_recommendation"]
            for field in required_fields:
                if field not in review_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate inline_comments structure
            if not isinstance(review_data["inline_comments"], list):
                raise ValueError("inline_comments must be a list")
            
            for comment in review_data["inline_comments"]:
                comment_fields = ["path", "start_line", "end_line", "severity", "category", "comment"]
                for field in comment_fields:
                    if field not in comment:
                        raise ValueError(f"Missing required field in comment: {field}")
                
                # Validate severity
                if comment["severity"] not in ["high", "medium", "low", "nit"]:
                    raise ValueError(f"Invalid severity: {comment['severity']}")
                
                # Validate category
                if comment["category"] not in ["security", "performance", "bug", "style", "architecture", "testing"]:
                    raise ValueError(f"Invalid category: {comment['category']}")
            
            # Validate risk level
            if review_data["risk"] not in ["Low", "Medium", "High"]:
                raise ValueError(f"Invalid risk level: {review_data['risk']}")
            
            # Validate approval recommendation
            if review_data["approval_recommendation"] not in ["approve", "request_changes", "comment"]:
                raise ValueError(f"Invalid approval recommendation: {review_data['approval_recommendation']}")
            
            return review_data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON", error=str(e), response=response)
            raise ValueError(f"Invalid JSON response: {e}")
        except ValueError as e:
            logger.error("AI response validation failed", error=str(e), response=response)
            raise
    
    async def review_code_changes(self,
                                 file_paths: List[str],
                                 languages: Dict[str, int],
                                 static_analysis_results: str,
                                 code_diff: str,
                                 use_pro_model: bool = True) -> Dict[str, Any]:
        """
        Review code changes using Gemini AI.
        
        Args:
            file_paths: List of file paths that were changed
            languages: Dictionary of language statistics from GitHub
            static_analysis_results: Results from static analysis tools
            code_diff: The actual code diff to review
            use_pro_model: Whether to use the Pro model (True) or Flash model (False)
            
        Returns:
            Dictionary containing review results
        """
        try:
            # Detect language and framework
            language, framework = self._detect_language_and_framework(file_paths, languages)
            
            # Calculate basic stats
            file_count = len(file_paths)
            lines_added = code_diff.count('\n+') - code_diff.count('\n+++')
            lines_removed = code_diff.count('\n-') - code_diff.count('\n---')
            
            # Format the prompt
            prompt = self._format_prompt(
                language=language,
                framework=framework,
                file_count=file_count,
                lines_added=lines_added,
                lines_removed=lines_removed,
                static_analysis_results=static_analysis_results,
                code_diff=code_diff
            )
            
            # Choose model
            model = self.pro_model if use_pro_model else self.flash_model
            model_name = settings.gemini_model_pro if use_pro_model else settings.gemini_model_flash
            
            logger.info(
                "Starting AI review",
                model=model_name,
                language=language,
                framework=framework,
                file_count=file_count,
                lines_added=lines_added,
                lines_removed=lines_removed
            )
            
            # Generate review
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent results
                    max_output_tokens=4096,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from AI model")
            
            # Validate and parse response
            review_data = self._validate_review_response(response.text)
            
            logger.info(
                "AI review completed",
                model=model_name,
                comments_count=len(review_data["inline_comments"]),
                risk_level=review_data["risk"],
                approval_recommendation=review_data["approval_recommendation"]
            )
            
            return review_data
            
        except Exception as e:
            logger.error("AI review failed", error=str(e), model=model_name if 'model_name' in locals() else "unknown")
            raise
    
    async def review_code_changes_batch(self,
                                      file_paths: List[str],
                                      languages: Dict[str, int],
                                      static_analysis_results: str,
                                      code_diff: str,
                                      max_comments: int = 20) -> Dict[str, Any]:
        """
        Review code changes with automatic model selection based on complexity.
        
        Args:
            file_paths: List of file paths that were changed
            languages: Dictionary of language statistics from GitHub
            static_analysis_results: Results from static analysis tools
            code_diff: The actual code diff to review
            max_comments: Maximum number of comments to generate
            
        Returns:
            Dictionary containing review results
        """
        try:
            # Determine complexity and choose model
            diff_size = len(code_diff)
            file_count = len(file_paths)
            
            # Use Pro model for complex changes, Flash for simple ones
            use_pro_model = diff_size > 10000 or file_count > 10 or len(static_analysis_results) > 1000
            
            # Get initial review
            review_data = await self.review_code_changes(
                file_paths=file_paths,
                languages=languages,
                static_analysis_results=static_analysis_results,
                code_diff=code_diff,
                use_pro_model=use_pro_model
            )
            
            # Limit comments if needed
            if len(review_data["inline_comments"]) > max_comments:
                # Sort by severity and keep most important comments
                severity_order = {"high": 4, "medium": 3, "low": 2, "nit": 1}
                review_data["inline_comments"].sort(
                    key=lambda x: severity_order.get(x["severity"], 0),
                    reverse=True
                )
                review_data["inline_comments"] = review_data["inline_comments"][:max_comments]
                
                # Update summary to reflect comment limit
                review_data["summary"] += f"\n\n*Note: Limited to {max_comments} most important comments.*"
            
            return review_data
            
        except Exception as e:
            logger.error("Batch AI review failed", error=str(e))
            raise
    
    async def generate_summary_comment(self, review_data: Dict[str, Any]) -> str:
        """Generate a summary comment for the pull request."""
        try:
            summary_prompt = f"""
            Based on the following code review results, generate a concise summary comment for a GitHub Pull Request:
            
            Review Summary: {review_data['summary']}
            Risk Level: {review_data['risk']}
            Breaking Changes: {review_data['breaking_changes']}
            Approval Recommendation: {review_data['approval_recommendation']}
            Total Comments: {len(review_data['inline_comments'])}
            
            Generate a professional, concise summary (2-3 sentences) that highlights the key findings and recommendation.
            """
            
            response = await asyncio.to_thread(
                self.flash_model.generate_content,
                summary_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            return response.text.strip() if response.text else "Review completed successfully."
            
        except Exception as e:
            logger.error("Failed to generate summary comment", error=str(e))
            return "Review completed successfully."
    
    async def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        try:
            test_prompt = "Hello, this is a test. Please respond with 'OK'."
            response = await asyncio.to_thread(
                self.flash_model.generate_content,
                test_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=10
                )
            )
            
            return response.text is not None and len(response.text.strip()) > 0
            
        except Exception as e:
            logger.error("Gemini API connection test failed", error=str(e))
            return False
