"""
Documentation Generator Tool for the Code Analyzer.
Generates comprehensive documentation based on code analysis and test results.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import Field

from code_analyzer.utils import logger


class DocumentationGeneratorTool(BaseTool):
    """Tool for generating documentation based on code analysis and test results."""
    name: str = "DocumentationGeneratorTool"
    description: str = "Generates comprehensive documentation for the analyzed code and test results."
    
    def _generate_project_overview(self, analysis_data: List[Dict[str, Any]]) -> str:
        """
        Generate project overview section.
        
        Args:
            analysis_data: List of file analysis data
            
        Returns:
            Markdown for project overview section
        """
        # Count valid files (those without errors)
        valid_files = [a for a in analysis_data if "error" not in a]
        
        # Get metrics
        total_loc = sum(a.get("metrics", {}).get("lines_of_code", 0) for a in valid_files)
        total_functions = sum(a.get("metrics", {}).get("function_count", 0) for a in valid_files)
        total_classes = sum(a.get("metrics", {}).get("class_count", 0) for a in valid_files)
        
        # Create markdown
        overview = "## Project Overview\n\n"
        overview += f"This documentation covers {len(valid_files)} Python files.\n\n"
        
        # Project metrics
        overview += "### Project Metrics\n\n"
        overview += "| Metric | Count |\n"
        overview += "| ------ | ----- |\n"
        overview += f"| Python Files | {len(valid_files)} |\n"
        overview += f"| Lines of Code | {total_loc} |\n"
        overview += f"| Functions | {total_functions} |\n"
        overview += f"| Classes | {total_classes} |\n\n"
        
        return overview
    
    def _generate_file_structure(self, analysis_data: List[Dict[str, Any]]) -> str:
        """
        Generate file structure section.
        
        Args:
            analysis_data: List of file analysis data
            
        Returns:
            Markdown for file structure section
        """
        # Group files by directory
        file_paths = [a.get("file_path", "unknown.py") for a in analysis_data]
        
        # Sort file paths
        file_paths.sort()
        
        # Create markdown
        structure = "## File Structure\n\n"
        structure += "```\n"
        
        # Build directory tree
        current_dir = ""
        for path in file_paths:
            # Skip empty paths
            if not path:
                continue
                
            dirs = os.path.dirname(path).split("/")
            filename = os.path.basename(path)
            
            # Handle root files
            if not dirs[0]:
                structure += f"├── {filename}\n"
                continue
            
            # Create proper indentation for directory structure
            dir_path = ""
            for i, d in enumerate(dirs):
                if not d:  # Skip empty directories
                    continue
                    
                dir_path = os.path.join(dir_path, d) if dir_path else d
                
                # Check if we need to print this directory
                if not current_dir.startswith(dir_path):
                    structure += f"{'│   ' * i}├── {d}/\n"
                    
            # Add file with proper indentation
            structure += f"{'│   ' * len(dirs)}├── {filename}\n"
            
            # Update current directory
            current_dir = os.path.dirname(path)
        
        structure += "```\n\n"
        
        return structure
    
    def _generate_module_documentation(self, analysis: Dict[str, Any]) -> str:
        """
        Generate documentation for a single module.
        
        Args:
            analysis: Module analysis data
            
        Returns:
            Markdown for module documentation
        """
        file_path = analysis.get("file_path", "unknown.py")
        
        # Skip files with errors
        if "error" in analysis:
            return f"### {file_path}\n\n**Error:** {analysis['error']}\n\n"
        
        # Create markdown
        doc = f"### {file_path}\n\n"
        
        # Add module docstring if available
        if analysis.get("module_docstring"):
            doc += f"{analysis['module_docstring']}\n\n"
        
        # Add metrics
        metrics = analysis.get("metrics", {})
        if metrics:
            doc += "#### Metrics\n\n"
            doc += "| Metric | Value |\n"
            doc += "| ------ | ----- |\n"
            doc += f"| Lines of Code | {metrics.get('lines_of_code', 'N/A')} |\n"
            doc += f"| Functions | {metrics.get('function_count', 'N/A')} |\n"
            doc += f"| Classes | {metrics.get('class_count', 'N/A')} |\n"
            doc += f"| Imports | {metrics.get('import_count', 'N/A')} |\n\n"
        
        # Add classes
        classes = analysis.get("classes", [])
        if classes:
            doc += "#### Classes\n\n"
            for cls in classes:
                doc += f"##### `{cls['name']}`\n\n"
                
                # Add class docstring
                if cls.get("docstring"):
                    doc += f"{cls['docstring']}\n\n"
                
                # Add inheritance information
                if cls.get("bases"):
                    doc += f"**Inherits from:** {', '.join(cls['bases'])}\n\n"
                
                # Add methods
                methods = cls.get("methods", [])
                if methods:
                    doc += "**Methods:**\n\n"
                    for method in methods:
                        # Skip private methods
                        if method["name"].startswith("_") and not method["name"].startswith("__"):
                            continue
                            
                        # Format method signature
                        args_str = ", ".join([arg["name"] for arg in method.get("args", [])])
                        doc += f"- `{method['name']}({args_str})`"
                        
                        # Add return type if available
                        if method.get("returns"):
                            doc += f" -> {method['returns']}"
                            
                        doc += "\n"
                        
                        # Add method docstring
                        if method.get("docstring"):
                            doc += f"  - {method['docstring']}\n"
                    
                    doc += "\n"
                
                # Add attributes
                attributes = cls.get("attributes", [])
                if attributes:
                    doc += "**Attributes:**\n\n"
                    for attr in attributes:
                        doc += f"- `{attr['name']}`"
                        if attr.get("value"):
                            doc += f" = {attr['value']}"
                        doc += "\n"
                    
                    doc += "\n"
        
        # Add functions
        functions = analysis.get("functions", [])
        if functions:
            doc += "#### Functions\n\n"
            for func in functions:
                # Skip private functions
                if func["name"].startswith("_") and not func["name"].startswith("__"):
                    continue
                    
                # Format function signature
                args_str = ", ".join([arg["name"] for arg in func.get("args", [])])
                doc += f"##### `{func['name']}({args_str})`"
                
                # Add return type if available
                if func.get("returns"):
                    doc += f" -> {func['returns']}"
                    
                doc += "\n\n"
                
                # Add function docstring
                if func.get("docstring"):
                    doc += f"{func['docstring']}\n\n"
        
        # Add imports
        imports = analysis.get("imports", [])
        if imports:
            doc += "#### Dependencies\n\n"
            for imp in imports:
                if imp.get("alias"):
                    doc += f"- `{imp['module']}` as `{imp['alias']}`\n"
                else:
                    doc += f"- `{imp['module']}`\n"
            
            doc += "\n"
        
        return doc
    
    def _generate_recommendations(self, analysis_data: List[Dict[str, Any]], test_results: Dict[str, Any]) -> str:
        """
        Generate recommendations section.
        
        Args:
            analysis_data: List of file analysis data
            test_results: Test results data
            
        Returns:
            Markdown for recommendations section
        """
        # Create markdown
        doc = "## Recommendations\n\n"
        
        recommendations = []
        
        # Check for documentation issues
        missing_docstrings = []
        for analysis in analysis_data:
            file_path = analysis.get("file_path", "unknown.py")
            
            # Skip files with errors
            if "error" in analysis:
                continue
                
            # Check module docstring
            if not analysis.get("module_docstring"):
                missing_docstrings.append(f"{file_path} (module)")
            
            # Check class docstrings
            for cls in analysis.get("classes", []):
                if not cls.get("docstring"):
                    missing_docstrings.append(f"{file_path} (class {cls.get('name', 'unknown')})")
            
            # Check function docstrings
            for func in analysis.get("functions", []):
                # Skip private functions
                if func.get("name", "").startswith("_"):
                    continue
                    
                if not func.get("docstring"):
                    missing_docstrings.append(f"{file_path} (function {func.get('name', 'unknown')})")
        
        if missing_docstrings:
            recommendations.append({
                "title": "Improve Documentation",
                "description": "The following components are missing docstrings:",
                "items": missing_docstrings[:10]  # Limit to 10 items
            })
            
            if len(missing_docstrings) > 10:
                recommendations[-1]["items"].append(f"... and {len(missing_docstrings) - 10} more")
        
        # Check test coverage
        test_summary = test_results.get("parsed_results", {}).get("summary", {})
        if test_summary:
            total_tests = test_summary.get("total", 0)
            total_functions = sum(a.get("metrics", {}).get("function_count", 0) for a in analysis_data if "error" not in a)
            
            if total_tests < total_functions:
                recommendations.append({
                    "title": "Improve Test Coverage",
                    "description": f"The project has {total_tests} tests for {total_functions} functions. Consider adding more tests to improve coverage."
                })
        
        # Generate markdown for recommendations
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                doc += f"### {i}. {rec['title']}\n\n"
                doc += f"{rec['description']}\n\n"
                
                if "items" in rec:
                    for item in rec["items"]:
                        doc += f"- {item}\n"
                    doc += "\n"
        else:
            doc += "No specific recommendations at this time.\n\n"
        
        return doc
    
    def _run(self, code_analysis: str, test_results: str, output_path: str) -> str:
        """
        Generate documentation based on code analysis and test results.
        
        Args:
            code_analysis: JSON string with code analysis results
            test_results: JSON string with test results
            output_path: Path to save the documentation
            
        Returns:
            Path to the generated documentation
        """
        logger.info(f"Generating documentation at: {output_path}")
        
        try:
            # Parse inputs
            analysis_data = json.loads(code_analysis) if isinstance(code_analysis, str) else code_analysis
            results = json.loads(test_results) if isinstance(test_results, str) else test_results
            
            # Ensure analysis_data is a list
            if not isinstance(analysis_data, list):
                analysis_data = [analysis_data]
            
            # Create documentation
            doc = "# Code Analysis and Test Documentation\n\n"
            doc += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            # Project overview
            doc += self._generate_project_overview(analysis_data)
            
            # File structure
            doc += self._generate_file_structure(analysis_data)
            
            # Code documentation
            doc += self._generate_code_documentation(analysis_data)
            
            # Test results
            doc += self._generate_test_documentation(results)
            
            # Recommendations
            doc += self._generate_recommendations(analysis_data, results)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write documentation to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc)
            
            logger.info(f"Documentation generated: {output_path}")
            
            return json.dumps({
                "output_path": output_path,
                "status": "success",
                "message": f"Documentation successfully generated at {output_path}"
            })
            
        except Exception as e:
            error_msg = f"Error generating documentation: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
    
    async def _arun(self, code_analysis: str, test_results: str, output_path: str) -> str:
        """Async version of _run."""
        return self._run(code_analysis, test_results, output_path)
    
    def _generate_code_documentation(self, analysis_data: List[Dict[str, Any]]) -> str:
        """
        Generate code documentation section.
        
        Args:
            analysis_data: List of file analysis data
            
        Returns:
            Markdown for code documentation section
        """
        # Create markdown
        doc = "## Code Documentation\n\n"
        
        # Generate documentation for each module
        for analysis in analysis_data:
            doc += self._generate_module_documentation(analysis)
        
        return doc
    
    def _generate_test_documentation(self, test_results: Dict[str, Any]) -> str:
        """
        Generate test documentation section.
        
        Args:
            test_results: Test results data
            
        Returns:
            Markdown for test documentation section
        """
        # Create markdown
        doc = "## Test Results\n\n"
        
        # Check for errors
        if "error" in test_results:
            doc += f"**Error running tests:** {test_results['error']}\n\n"
            return doc
        
        # Add test summary
        summary = test_results.get("parsed_results", {}).get("summary", {})
        if summary:
            doc += "### Summary\n\n"
            doc += "| Metric | Count |\n"
            doc += "| ------ | ----- |\n"
            doc += f"| Total Tests | {summary.get('total', 'N/A')} |\n"
            doc += f"| Passed | {summary.get('passed', 'N/A')} |\n"
            doc += f"| Failed | {summary.get('failed', 'N/A')} |\n"
            doc += f"| Skipped | {summary.get('skipped', 'N/A')} |\n"
            doc += f"| Errors | {summary.get('error', 'N/A')} |\n\n"
            
            # Add execution information
            doc += f"**Execution Time:** {test_results.get('execution_time', 'N/A'):.2f} seconds\n\n"
            
            # Add test files
            test_files = test_results.get("test_files", [])
            if test_files:
                doc += "### Test Files\n\n"
                for test_file in test_files:
                    doc += f"- `{test_file}`\n"
                doc += "\n"
            
            # Add detailed test results
            tests = test_results.get("parsed_results", {}).get("tests", [])
            if tests:
                doc += "### Detailed Results\n\n"
                
                # Group tests by status
                status_groups = {}
                for test in tests:
                    status = test.get("status", "UNKNOWN")
                    if status not in status_groups:
                        status_groups[status] = []
                    status_groups[status].append(test)
                
                # Add each status group
                for status, tests in status_groups.items():
                    doc += f"#### {status} Tests ({len(tests)})\n\n"
                    for test in tests:
                        doc += f"- `{test.get('name', 'Unknown test')}`\n"
                        
                        # Add details if available
                        details = test.get("details", [])
                        if details:
                            doc += "  ```\n"
                            for detail in details:
                                doc += f"  {detail}\n"
                            doc += "  ```\n"
                    
                    doc += "\n"
        
        # Add raw output if no parsed results
        elif test_results.get("stdout"):
            doc += "### Raw Output\n\n"
            doc += "```\n"
            doc += test_results.get("stdout", "")
            doc += "```\n\n"
        
        # Add stderr if available
        if test_results.get("stderr"):
            doc += "### Errors\n\n"
            doc += "```\n"
            doc += test_results.get("stderr", "")
            doc += "```\n\n"
        
        return doc