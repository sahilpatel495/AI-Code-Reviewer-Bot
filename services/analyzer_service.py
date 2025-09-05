"""
Static Analyzer Service

This module handles running various static analysis tools on code changes
to provide additional context for AI review.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


class AnalyzerService:
    """Service for running static analysis tools on code."""
    
    def __init__(self):
        """Initialize the analyzer service."""
        self.supported_languages = {
            "python": self._analyze_python,
            "javascript": self._analyze_javascript,
            "typescript": self._analyze_typescript,
            "java": self._analyze_java,
            "sql": self._analyze_sql,
            "go": self._analyze_go,
            "rust": self._analyze_rust
        }
        
        logger.info("Analyzer service initialized", supported_languages=list(self.supported_languages.keys()))
    
    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension from path."""
        return Path(file_path).suffix.lower()
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        ext = self._get_file_extension(file_path)
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".sql": "sql",
            ".go": "go",
            ".rs": "rust"
        }
        
        return language_map.get(ext, "unknown")
    
    async def _run_command(self, command: List[str], cwd: Optional[str] = None, timeout: int = 30) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, and stderr."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return (
                process.returncode,
                stdout.decode("utf-8", errors="ignore"),
                stderr.decode("utf-8", errors="ignore")
            )
            
        except asyncio.TimeoutError:
            logger.warning("Command timed out", command=command, timeout=timeout)
            return -1, "", "Command timed out"
        except Exception as e:
            logger.error("Command execution failed", command=command, error=str(e))
            return -1, "", str(e)
    
    async def _analyze_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Python code using various tools."""
        results = {
            "language": "python",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # Run Ruff (linter)
                if settings.enable_python_analyzers:
                    exit_code, stdout, stderr = await self._run_command(
                        ["ruff", "check", temp_file, "--output-format=json"],
                        timeout=30
                    )
                    
                    if exit_code == 0:
                        results["tools"]["ruff"] = {"status": "passed", "output": stdout}
                    else:
                        try:
                            ruff_results = json.loads(stdout) if stdout else []
                            results["tools"]["ruff"] = {"status": "failed", "output": ruff_results}
                            
                            # Convert to issues
                            for issue in ruff_results:
                                results["issues"].append({
                                    "tool": "ruff",
                                    "severity": "medium" if issue.get("code", "").startswith("E") else "low",
                                    "message": issue.get("message", ""),
                                    "line": issue.get("location", {}).get("row", 0),
                                    "code": issue.get("code", "")
                                })
                        except json.JSONDecodeError:
                            results["tools"]["ruff"] = {"status": "error", "output": stderr}
                
                # Run Black (formatter check)
                exit_code, stdout, stderr = await self._run_command(
                    ["black", "--check", "--diff", temp_file],
                    timeout=30
                )
                
                if exit_code == 0:
                    results["tools"]["black"] = {"status": "passed", "output": "Code is properly formatted"}
                else:
                    results["tools"]["black"] = {"status": "failed", "output": stdout}
                    results["issues"].append({
                        "tool": "black",
                        "severity": "low",
                        "message": "Code formatting issues detected",
                        "line": 0,
                        "code": "formatting"
                    })
                
                # Run Bandit (security)
                exit_code, stdout, stderr = await self._run_command(
                    ["bandit", "-f", "json", temp_file],
                    timeout=30
                )
                
                if exit_code == 0:
                    results["tools"]["bandit"] = {"status": "passed", "output": "No security issues found"}
                else:
                    try:
                        bandit_results = json.loads(stdout) if stdout else {}
                        results["tools"]["bandit"] = {"status": "failed", "output": bandit_results}
                        
                        # Convert to issues
                        for issue in bandit_results.get("results", []):
                            results["issues"].append({
                                "tool": "bandit",
                                "severity": "high" if issue.get("issue_severity") == "HIGH" else "medium",
                                "message": issue.get("issue_text", ""),
                                "line": issue.get("line_number", 0),
                                "code": issue.get("test_id", "")
                            })
                    except json.JSONDecodeError:
                        results["tools"]["bandit"] = {"status": "error", "output": stderr}
                
                # Run mypy (type checker)
                exit_code, stdout, stderr = await self._run_command(
                    ["mypy", "--show-error-codes", "--no-error-summary", temp_file],
                    timeout=30
                )
                
                if exit_code == 0:
                    results["tools"]["mypy"] = {"status": "passed", "output": "No type errors found"}
                else:
                    results["tools"]["mypy"] = {"status": "failed", "output": stdout}
                    
                    # Parse mypy output
                    for line in stdout.split('\n'):
                        if 'error:' in line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                line_num = int(parts[1]) if parts[1].isdigit() else 0
                                error_msg = parts[3].strip()
                                results["issues"].append({
                                    "tool": "mypy",
                                    "severity": "medium",
                                    "message": error_msg,
                                    "line": line_num,
                                    "code": "type-check"
                                })
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error("Python analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            high_count = sum(1 for issue in results["issues"] if issue["severity"] == "high")
            medium_count = sum(1 for issue in results["issues"] if issue["severity"] == "medium")
            low_count = sum(1 for issue in results["issues"] if issue["severity"] == "low")
            
            results["summary"] = f"Found {issue_count} issues: {high_count} high, {medium_count} medium, {low_count} low"
        
        return results
    
    async def _analyze_javascript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code using ESLint and Prettier."""
        results = {
            "language": "javascript",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # Run ESLint
                if settings.enable_js_analyzers:
                    exit_code, stdout, stderr = await self._run_command(
                        ["eslint", "--format=json", temp_file],
                        timeout=30
                    )
                    
                    if exit_code == 0:
                        results["tools"]["eslint"] = {"status": "passed", "output": "No linting issues found"}
                    else:
                        try:
                            eslint_results = json.loads(stdout) if stdout else []
                            results["tools"]["eslint"] = {"status": "failed", "output": eslint_results}
                            
                            # Convert to issues
                            for file_result in eslint_results:
                                for message in file_result.get("messages", []):
                                    severity_map = {1: "low", 2: "medium", 3: "high"}
                                    results["issues"].append({
                                        "tool": "eslint",
                                        "severity": severity_map.get(message.get("severity", 1), "low"),
                                        "message": message.get("message", ""),
                                        "line": message.get("line", 0),
                                        "code": message.get("ruleId", "")
                                    })
                        except json.JSONDecodeError:
                            results["tools"]["eslint"] = {"status": "error", "output": stderr}
                
                # Run Prettier (formatter check)
                exit_code, stdout, stderr = await self._run_command(
                    ["prettier", "--check", temp_file],
                    timeout=30
                )
                
                if exit_code == 0:
                    results["tools"]["prettier"] = {"status": "passed", "output": "Code is properly formatted"}
                else:
                    results["tools"]["prettier"] = {"status": "failed", "output": "Code formatting issues detected"}
                    results["issues"].append({
                        "tool": "prettier",
                        "severity": "low",
                        "message": "Code formatting issues detected",
                        "line": 0,
                        "code": "formatting"
                    })
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error("JavaScript analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            high_count = sum(1 for issue in results["issues"] if issue["severity"] == "high")
            medium_count = sum(1 for issue in results["issues"] if issue["severity"] == "medium")
            low_count = sum(1 for issue in results["issues"] if issue["severity"] == "low")
            
            results["summary"] = f"Found {issue_count} issues: {high_count} high, {medium_count} medium, {low_count} low"
        
        return results
    
    async def _analyze_typescript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze TypeScript code using TypeScript compiler and ESLint."""
        results = {
            "language": "typescript",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # Run TypeScript compiler
                exit_code, stdout, stderr = await self._run_command(
                    ["tsc", "--noEmit", "--strict", temp_file],
                    timeout=30
                )
                
                if exit_code == 0:
                    results["tools"]["typescript"] = {"status": "passed", "output": "No type errors found"}
                else:
                    results["tools"]["typescript"] = {"status": "failed", "output": stderr}
                    
                    # Parse TypeScript errors
                    for line in stderr.split('\n'):
                        if 'error TS' in line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                line_num = int(parts[1]) if parts[1].isdigit() else 0
                                error_msg = parts[3].strip()
                                results["issues"].append({
                                    "tool": "typescript",
                                    "severity": "medium",
                                    "message": error_msg,
                                    "line": line_num,
                                    "code": "type-check"
                                })
                
                # Run ESLint for TypeScript
                if settings.enable_js_analyzers:
                    exit_code, stdout, stderr = await self._run_command(
                        ["eslint", "--format=json", temp_file],
                        timeout=30
                    )
                    
                    if exit_code == 0:
                        results["tools"]["eslint"] = {"status": "passed", "output": "No linting issues found"}
                    else:
                        try:
                            eslint_results = json.loads(stdout) if stdout else []
                            results["tools"]["eslint"] = {"status": "failed", "output": eslint_results}
                            
                            # Convert to issues
                            for file_result in eslint_results:
                                for message in file_result.get("messages", []):
                                    severity_map = {1: "low", 2: "medium", 3: "high"}
                                    results["issues"].append({
                                        "tool": "eslint",
                                        "severity": severity_map.get(message.get("severity", 1), "low"),
                                        "message": message.get("message", ""),
                                        "line": message.get("line", 0),
                                        "code": message.get("ruleId", "")
                                    })
                        except json.JSONDecodeError:
                            results["tools"]["eslint"] = {"status": "error", "output": stderr}
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error("TypeScript analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            high_count = sum(1 for issue in results["issues"] if issue["severity"] == "high")
            medium_count = sum(1 for issue in results["issues"] if issue["severity"] == "medium")
            low_count = sum(1 for issue in results["issues"] if issue["severity"] == "low")
            
            results["summary"] = f"Found {issue_count} issues: {high_count} high, {medium_count} medium, {low_count} low"
        
        return results
    
    async def _analyze_java(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Java code using basic syntax checking."""
        results = {
            "language": "java",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Basic Java syntax analysis
            if "public class" not in content and "public interface" not in content:
                results["issues"].append({
                    "tool": "java-syntax",
                    "severity": "medium",
                    "message": "No public class or interface found",
                    "line": 0,
                    "code": "syntax"
                })
            
            # Check for common issues
            if "System.out.println" in content:
                results["issues"].append({
                    "tool": "java-style",
                    "severity": "low",
                    "message": "Consider using a proper logging framework instead of System.out.println",
                    "line": 0,
                    "code": "style"
                })
            
            results["tools"]["java-syntax"] = {"status": "completed", "output": "Basic syntax check completed"}
            
        except Exception as e:
            logger.error("Java analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            results["summary"] = f"Found {issue_count} issues"
        
        return results
    
    async def _analyze_sql(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze SQL code using SQLFluff."""
        results = {
            "language": "sql",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # Run SQLFluff
                if settings.enable_sql_analyzers:
                    exit_code, stdout, stderr = await self._run_command(
                        ["sqlfluff", "lint", "--format=json", temp_file],
                        timeout=30
                    )
                    
                    if exit_code == 0:
                        results["tools"]["sqlfluff"] = {"status": "passed", "output": "No SQL issues found"}
                    else:
                        try:
                            sqlfluff_results = json.loads(stdout) if stdout else []
                            results["tools"]["sqlfluff"] = {"status": "failed", "output": sqlfluff_results}
                            
                            # Convert to issues
                            for file_result in sqlfluff_results:
                                for violation in file_result.get("violations", []):
                                    severity_map = {"E": "high", "W": "medium", "I": "low"}
                                    results["issues"].append({
                                        "tool": "sqlfluff",
                                        "severity": severity_map.get(violation.get("code", "W")[0], "medium"),
                                        "message": violation.get("description", ""),
                                        "line": violation.get("line_no", 0),
                                        "code": violation.get("code", "")
                                    })
                        except json.JSONDecodeError:
                            results["tools"]["sqlfluff"] = {"status": "error", "output": stderr}
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error("SQL analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            results["summary"] = f"Found {issue_count} issues"
        
        return results
    
    async def _analyze_go(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Go code using basic syntax checking."""
        results = {
            "language": "go",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Basic Go syntax analysis
            if "package " not in content:
                results["issues"].append({
                    "tool": "go-syntax",
                    "severity": "high",
                    "message": "Missing package declaration",
                    "line": 0,
                    "code": "syntax"
                })
            
            results["tools"]["go-syntax"] = {"status": "completed", "output": "Basic syntax check completed"}
            
        except Exception as e:
            logger.error("Go analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            results["summary"] = f"Found {issue_count} issues"
        
        return results
    
    async def _analyze_rust(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Rust code using basic syntax checking."""
        results = {
            "language": "rust",
            "tools": {},
            "issues": [],
            "summary": ""
        }
        
        try:
            # Basic Rust syntax analysis
            if "fn main" not in content and "pub fn" not in content:
                results["issues"].append({
                    "tool": "rust-syntax",
                    "severity": "low",
                    "message": "No main function or public function found",
                    "line": 0,
                    "code": "syntax"
                })
            
            results["tools"]["rust-syntax"] = {"status": "completed", "output": "Basic syntax check completed"}
            
        except Exception as e:
            logger.error("Rust analysis failed", error=str(e), file_path=file_path)
            results["error"] = str(e)
        
        # Generate summary
        issue_count = len(results["issues"])
        if issue_count == 0:
            results["summary"] = "No issues found"
        else:
            results["summary"] = f"Found {issue_count} issues"
        
        return results
    
    async def analyze_files(self, file_paths: List[str], file_contents: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze multiple files and return combined results.
        
        Args:
            file_paths: List of file paths to analyze
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            Dictionary containing analysis results for all files
        """
        try:
            results = {
                "files": {},
                "summary": {
                    "total_files": len(file_paths),
                    "languages": {},
                    "total_issues": 0,
                    "issues_by_severity": {"high": 0, "medium": 0, "low": 0}
                }
            }
            
            # Analyze each file
            for file_path in file_paths:
                if file_path not in file_contents:
                    logger.warning("File content not found", file_path=file_path)
                    continue
                
                language = self._detect_language(file_path)
                if language not in self.supported_languages:
                    logger.warning("Unsupported language", file_path=file_path, language=language)
                    continue
                
                # Count languages
                if language not in results["summary"]["languages"]:
                    results["summary"]["languages"][language] = 0
                results["summary"]["languages"][language] += 1
                
                # Analyze file
                file_results = await self.supported_languages[language](
                    file_path, file_contents[file_path]
                )
                
                results["files"][file_path] = file_results
                
                # Update summary
                for issue in file_results.get("issues", []):
                    results["summary"]["total_issues"] += 1
                    severity = issue.get("severity", "low")
                    if severity in results["summary"]["issues_by_severity"]:
                        results["summary"]["issues_by_severity"][severity] += 1
            
            # Generate overall summary
            if results["summary"]["total_issues"] == 0:
                results["summary"]["overall_status"] = "clean"
                results["summary"]["message"] = "No issues found in any files"
            else:
                high_count = results["summary"]["issues_by_severity"]["high"]
                medium_count = results["summary"]["issues_by_severity"]["medium"]
                low_count = results["summary"]["issues_by_severity"]["low"]
                
                if high_count > 0:
                    results["summary"]["overall_status"] = "critical"
                    results["summary"]["message"] = f"Found {high_count} high-severity issues"
                elif medium_count > 0:
                    results["summary"]["overall_status"] = "warning"
                    results["summary"]["message"] = f"Found {medium_count} medium-severity issues"
                else:
                    results["summary"]["overall_status"] = "info"
                    results["summary"]["message"] = f"Found {low_count} low-severity issues"
            
            logger.info(
                "File analysis completed",
                total_files=results["summary"]["total_files"],
                total_issues=results["summary"]["total_issues"],
                overall_status=results["summary"]["overall_status"]
            )
            
            return results
            
        except Exception as e:
            logger.error("File analysis failed", error=str(e))
            raise
    
    async def test_tools(self) -> Dict[str, bool]:
        """Test if all required analysis tools are available."""
        tools_status = {}
        
        # Test Python tools
        if settings.enable_python_analyzers:
            tools_status["ruff"] = await self._test_tool(["ruff", "--version"])
            tools_status["black"] = await self._test_tool(["black", "--version"])
            tools_status["bandit"] = await self._test_tool(["bandit", "--version"])
            tools_status["mypy"] = await self._test_tool(["mypy", "--version"])
        
        # Test JavaScript tools
        if settings.enable_js_analyzers:
            tools_status["eslint"] = await self._test_tool(["eslint", "--version"])
            tools_status["prettier"] = await self._test_tool(["prettier", "--version"])
            tools_status["typescript"] = await self._test_tool(["tsc", "--version"])
        
        # Test SQL tools
        if settings.enable_sql_analyzers:
            tools_status["sqlfluff"] = await self._test_tool(["sqlfluff", "--version"])
        
        return tools_status
    
    async def _test_tool(self, command: List[str]) -> bool:
        """Test if a tool is available and working."""
        try:
            exit_code, _, _ = await self._run_command(command, timeout=10)
            return exit_code == 0
        except Exception:
            return False
