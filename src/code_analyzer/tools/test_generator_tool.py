"""
Test Generator Tool for the Code Analyzer.
Generates pytest test cases based on code analysis.
"""

import os
import json
from typing import Dict, List, Any, Optional
import ast
from crewai.tools import BaseTool
from pydantic import Field

from code_analyzer.utils import logger


class TestGeneratorTool(BaseTool):
    """Tool for generating pytest test cases."""
    name: str = "TestGeneratorTool"
    description: str = "Generates pytest test cases based on code analysis."
    
    output_dir: str = Field(
        description="Output directory for the generated test files"
    )
    
    def _create_test_file_path(self, file_path: str) -> str:
        """
        Create a path for the test file based on the original file path.
        
        Args:
            file_path: Path to the original Python file
            
        Returns:
            Path to the test file
        """
        # Get filename without extension
        filename = os.path.basename(file_path)
        module_name = os.path.splitext(filename)[0]
        
        # Create test file path
        test_file_path = os.path.join(self.output_dir, f"test_{module_name}.py")
        
        return test_file_path
    
    def _generate_import_statement(self, file_path: str) -> str:
        """
        Generate an import statement for the module being tested.
        
        Args:
            file_path: Path to the original Python file
            
        Returns:
            Import statement
        """
        # Convert path to module name
        # Replace slashes with dots and remove .py extension
        relative_import = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        
        return f"from {relative_import} import *"
    
    def _generate_function_test(self, func: Dict[str, Any]) -> str:
        """
        Generate a test for a function.
        
        Args:
            func: Function details
            
        Returns:
            Test code for the function
        """
        func_name = func["name"]
        
        # Skip private functions
        if func_name.startswith("_"):
            return ""
        
        test_code = f"\n\ndef test_{func_name}():\n"
        test_code += f'    """Test the {func_name} function."""\n'
        
        # Get function args excluding 'self'
        args = [arg["name"] for arg in func.get("args", []) if arg["name"] != "self"]
        
        # Create test based on function name patterns
        if "get" in func_name.lower() or "fetch" in func_name.lower() or "retrieve" in func_name.lower():
            args_str = ", ".join(["None" for _ in args]) if args else ""
            test_code += f"    result = {func_name}({args_str})\n"
            test_code += f"    assert result is not None, \"Should return a value\"\n"
        
        elif "is_" in func_name.lower() or "has_" in func_name.lower() or "check" in func_name.lower():
            args_str = ", ".join(["None" for _ in args]) if args else ""
            test_code += f"    result = {func_name}({args_str})\n"
            test_code += f"    assert isinstance(result, bool), \"Should return a boolean\"\n"
        
        elif "calculate" in func_name.lower() or "compute" in func_name.lower() or "sum" in func_name.lower():
            args_str = ", ".join(["0" for _ in args]) if args else ""
            test_code += f"    result = {func_name}({args_str})\n"
            test_code += f"    assert result is not None, \"Should return a calculated value\"\n"
        
        else:
            args_str = ", ".join(["None" for _ in args]) if args else ""
            test_code += f"    # TODO: Add proper test parameters\n"
            test_code += f"    result = {func_name}({args_str})\n"
            test_code += f"    # TODO: Add appropriate assertions for {func_name}\n"
        
        return test_code
    
    def _generate_class_test(self, cls: Dict[str, Any]) -> str:
        """
        Generate tests for a class.
        
        Args:
            cls: Class details
            
        Returns:
            Test code for the class
        """
        cls_name = cls["name"]
        
        test_code = f"\n\nclass Test{cls_name}:\n"
        
        # Create fixture for class instance
        test_code += f"    @pytest.fixture\n"
        test_code += f"    def {cls_name.lower()}_instance(self):\n"
        test_code += f"        \"\"\"{cls_name} instance for testing.\"\"\"\n"
        test_code += f"        return {cls_name}()\n"
        
        # Generate tests for methods
        for method in cls.get("methods", []):
            method_name = method["name"]
            
            # Skip private and special methods
            if method_name.startswith("_"):
                continue
            
            test_code += f"\n    def test_{method_name}(self, {cls_name.lower()}_instance):\n"
            test_code += f'        """Test the {method_name} method."""\n'
            
            # Get method args excluding self
            args = [arg["name"] for arg in method.get("args", []) if arg["name"] != "self"]
            
            # Generate test based on method name patterns
            if "get" in method_name.lower() or "fetch" in method_name.lower():
                args_str = ", ".join(["None" for _ in args]) if args else ""
                test_code += f"        result = {cls_name.lower()}_instance.{method_name}({args_str})\n"
                test_code += f"        assert result is not None, \"Should return a value\"\n"
            
            elif "is_" in method_name.lower() or "has_" in method_name.lower():
                args_str = ", ".join(["None" for _ in args]) if args else ""
                test_code += f"        result = {cls_name.lower()}_instance.{method_name}({args_str})\n"
                test_code += f"        assert isinstance(result, bool), \"Should return a boolean\"\n"
            
            else:
                args_str = ", ".join(["None" for _ in args]) if args else ""
                test_code += f"        # TODO: Add proper test parameters\n"
                test_code += f"        result = {cls_name.lower()}_instance.{method_name}({args_str})\n"
                test_code += f"        # TODO: Add appropriate assertions for {method_name}\n"
        
        return test_code
    
    def _generate_test_file(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a test file for a module.
        
        Args:
            analysis: Analysis of the module
            
        Returns:
            Path to the generated test file
        """
        file_path = analysis.get("file_path", "unknown.py")
        
        # Skip files with errors
        if "error" in analysis:
            logger.warning(f"Skipping test generation for {file_path}: {analysis['error']}")
            return f"Skipped {file_path} due to analysis errors"
        
        # Create test file path
        test_file_path = self._create_test_file_path(file_path)
        
        # Start generating test code
        test_code = f"# Generated test file for {file_path}\n"
        test_code += "import pytest\n"
        
        # Add import for the module being tested
        test_code += self._generate_import_statement(file_path) + "\n"
        
        # Generate tests for functions
        for func in analysis.get("functions", []):
            test_code += self._generate_function_test(func)
        
        # Generate tests for classes
        for cls in analysis.get("classes", []):
            test_code += self._generate_class_test(cls)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        
        # Write test file
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        logger.info(f"Generated test file: {test_file_path}")
        
        return test_file_path
    
    def _run(self, code_analysis: str, output_dir: str = None) -> str:
        """
        Generate pytest test files based on code analysis.
        
        Args:
            code_analysis: JSON string with code analysis results
            output_dir: Output directory for test files (overrides the tool's configured output_dir)
            
        Returns:
            Summary of generated test files
        """
        # Use provided output directory or the tool's configured one
        self.output_dir = output_dir or self.output_dir
        
        logger.info(f"Generating test files in: {self.output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            # Parse analysis results
            analysis_data = json.loads(code_analysis)
            
            generated_files = []
            
            # Handle both single file and multiple files analysis
            if isinstance(analysis_data, list):
                # Multiple files
                for file_analysis in analysis_data:
                    test_file_path = self._generate_test_file(file_analysis)
                    generated_files.append(test_file_path)
            else:
                # Single file
                test_file_path = self._generate_test_file(analysis_data)
                generated_files.append(test_file_path)
            
            # Create summary
            summary = {
                "generated_test_files": generated_files,
                "file_count": len(generated_files)
            }
            
            logger.info(f"Generated {len(generated_files)} test files")
            
            return json.dumps(summary, indent=2)
            
        except Exception as e:
            error_msg = f"Error generating test files: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
    
    async def _arun(self, code_analysis: str, output_dir: str = None) -> str:
        """Async version of _run."""
        return self._run(code_analysis, output_dir)