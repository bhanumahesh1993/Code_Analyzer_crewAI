"""
Test Runner Tool for the Code Analyzer.
Runs pytest test cases and captures results.
"""

import os
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional, Union
import time
import re

from crewai.tools import BaseTool
from pydantic import Field

from code_analyzer.utils import logger


class TestRunnerTool(BaseTool):
    """Tool for running pytest test cases."""
    name: str = "TestRunnerTool"
    description: str = "Runs pytest test cases and captures results."
    
    def _parse_test_results(self, stdout: str) -> Dict[str, Any]:
        """
        Parse pytest output to extract structured test results.
        
        Args:
            stdout: Standard output from pytest
            
        Returns:
            Dictionary with parsed test results
        """
        lines = stdout.splitlines()
        
        # Extract test results
        tests = []
        current_test = None
        
        for line in lines:
            # Match test case line
            test_match = re.match(r'(PASSED|FAILED|SKIPPED|XFAILED|XPASSED|ERROR)\s+(.*)', line)
            if test_match:
                status, name = test_match.groups()
                current_test = {
                    "name": name.strip(),
                    "status": status,
                    "details": []
                }
                tests.append(current_test)
                continue
            
            # Add details to current test if available
            if current_test and line.strip() and not line.startswith('='):
                current_test["details"].append(line.strip())
        
        # Count results by status
        summary = {
            "total": len(tests),
            "passed": len([t for t in tests if t["status"] == "PASSED"]),
            "failed": len([t for t in tests if t["status"] == "FAILED"]),
            "skipped": len([t for t in tests if t["status"] == "SKIPPED"]),
            "error": len([t for t in tests if t["status"] == "ERROR"]),
            "xfailed": len([t for t in tests if t["status"] == "XFAILED"]),
            "xpassed": len([t for t in tests if t["status"] == "XPASSED"])
        }
        
        return {
            "tests": tests,
            "summary": summary
        }
    
    def _run_pytest(self, test_dir: str, verbose: bool = True, coverage: bool = True) -> Dict[str, Any]:
        """
        Run pytest on the specified test directory.
        
        Args:
            test_dir: Directory containing the test files
            verbose: Whether to run with verbose output
            coverage: Whether to collect coverage information
            
        Returns:
            Dictionary with test results
        """
        # Prepare command
        cmd = [sys.executable, "-m", "pytest", test_dir]
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov", "--cov-report", "term"])
        
        # Add option to disable headers for cleaner output
        cmd.append("--no-header")
        
        logger.info(f"Running pytest with command: {' '.join(cmd)}")
        
        # Measure execution time
        start_time = time.time()
        
        try:
            # Run pytest
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # Parse test results if available
            parsed_results = None
            if result.stdout:
                parsed_results = self._parse_test_results(result.stdout)
            
            # Create result object
            return {
                "command": " ".join(cmd),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "parsed_results": parsed_results
            }
            
        except Exception as e:
            logger.error(f"Error running pytest: {str(e)}")
            return {
                "command": " ".join(cmd),
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _run(self, test_dir: str) -> str:
        """
        Run pytest on the specified test directory and return results.
        
        Args:
            test_dir: Directory containing test files
            
        Returns:
            JSON string with test results
        """
        logger.info(f"Running tests in directory: {test_dir}")
        
        # Check if directory exists
        if not os.path.exists(test_dir):
            error_msg = f"Error: Test directory '{test_dir}' does not exist."
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
        
        # Check if directory contains any test files
        test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
        if not test_files:
            warning_msg = f"Warning: No test files found in '{test_dir}'."
            logger.warning(warning_msg)
            return json.dumps({"warning": warning_msg, "test_files_found": 0})
        
        logger.info(f"Found {len(test_files)} test files: {', '.join(test_files)}")
        
        # Run pytest
        result = self._run_pytest(test_dir)
        
        # Add test file information
        result["test_files"] = test_files
        result["test_files_count"] = len(test_files)
        
        return json.dumps(result, indent=2)
    
    async def _arun(self, test_dir: str) -> str:
        """Async version of _run."""
        return self._run(test_dir)