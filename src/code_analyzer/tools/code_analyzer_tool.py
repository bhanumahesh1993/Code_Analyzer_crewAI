"""
Code Analyzer Tool for the Code Analyzer.
Analyzes Python code to extract structure and relationships.
"""

import ast
import json
from typing import Dict, List, Any, Union, Optional, Tuple
import traceback

from crewai.tools import BaseTool
from pydantic import Field

from code_analyzer.utils import logger


class CodeAnalyzerTool(BaseTool):
    """Tool for analyzing Python code structure."""
    name: str = "CodeAnalyzerTool"
    description: str = "Analyzes Python code to extract functions, classes, and dependencies."
    
    def _extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Extract docstring from an AST node if it exists."""
        if not hasattr(node, 'body') or not node.body:
            return None
            
        first_node = node.body[0]
        if isinstance(first_node, ast.Expr) and isinstance(first_node.value, ast.Str):
            return first_node.value.s
        return None
    
    def _extract_function_details(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract detailed information about a function."""
        # Get docstring
        docstring = self._extract_docstring(node)
        
        # Get arguments
        args = []
        for arg in node.args.args:
            args.append({
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if hasattr(arg, 'annotation') and arg.annotation else None
            })
        
        # Get default values
        defaults = []
        if node.args.defaults:
            defaults = [ast.unparse(default) for default in node.args.defaults]
        
        # Get return annotation
        returns = ast.unparse(node.returns) if node.returns else None
        
        # Check for decorators
        decorators = []
        if node.decorator_list:
            for decorator in node.decorator_list:
                decorators.append(ast.unparse(decorator))
        
        return {
            "name": node.name,
            "args": args,
            "defaults": defaults,
            "returns": returns,
            "decorators": decorators,
            "docstring": docstring,
            "line_number": node.lineno,
            "end_line_number": node.end_lineno if hasattr(node, 'end_lineno') else None
        }
    
    def _extract_class_details(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract detailed information about a class."""
        # Get docstring
        docstring = self._extract_docstring(node)
        
        # Get base classes
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))
        
        # Get methods
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._extract_function_details(item))
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append({
                            "name": target.id,
                            "value": ast.unparse(item.value) if item.value else None,
                            "line_number": item.lineno
                        })
        
        return {
            "name": node.name,
            "bases": bases,
            "methods": methods,
            "attributes": attributes,
            "docstring": docstring,
            "line_number": node.lineno,
            "end_line_number": node.end_lineno if hasattr(node, 'end_lineno') else None
        }
    
    def _analyze_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file to extract its structure."""
        try:
            tree = ast.parse(code)
            
            # Initialize results
            functions = []
            classes = []
            imports = []
            global_variables = []
            
            # Walk through the AST
            for node in ast.iter_child_nodes(tree):
                # Extract functions
                if isinstance(node, ast.FunctionDef):
                    functions.append(self._extract_function_details(node))
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    classes.append(self._extract_class_details(node))
                
                # Extract imports
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append({
                            "module": name.name,
                            "alias": name.asname,
                            "line_number": node.lineno
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    for name in node.names:
                        imports.append({
                            "module": f"{node.module}.{name.name}" if node.module else name.name,
                            "alias": name.asname,
                            "line_number": node.lineno
                        })
                
                # Extract global variables
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            global_variables.append({
                                "name": target.id,
                                "value": ast.unparse(node.value) if node.value else None,
                                "line_number": node.lineno
                            })
            
            # Get module docstring
            module_docstring = self._extract_docstring(tree)
            
            # Determine complexity metrics
            loc = len(code.splitlines())
            function_count = len(functions)
            class_count = len(classes)
            
            analysis = {
                "file_path": file_path,
                "module_docstring": module_docstring,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "global_variables": global_variables,
                "metrics": {
                    "lines_of_code": loc,
                    "function_count": function_count,
                    "class_count": class_count,
                    "import_count": len(imports)
                }
            }
            
            return analysis
            
        except SyntaxError as e:
            error_msg = f"Syntax error in {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "file_path": file_path,
                "error": error_msg,
                "traceback": traceback.format_exc()
            }
        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "file_path": file_path,
                "error": error_msg,
                "traceback": traceback.format_exc()
            }
    
    def _run(self, code: str, file_path: str = "unknown.py") -> str:
        """
        Analyze Python code to extract its structure.
        
        Args:
            code: Python code to analyze
            file_path: Path to the file being analyzed
            
        Returns:
            JSON string with analysis results
        """
        logger.info(f"Analyzing code from: {file_path}")
        
        # Check if input is JSON containing multiple files
        try:
            files_dict = json.loads(code)
            if isinstance(files_dict, dict):
                # Analyze each file
                results = []
                for path, content in files_dict.items():
                    if isinstance(content, str) and not content.startswith("Error reading file:"):
                        result = self._analyze_code(content, path)
                        results.append(result)
                    else:
                        logger.warning(f"Skipping {path}: Not a valid Python file or contains errors")
                
                logger.info(f"Completed analysis of {len(results)} files")
                return json.dumps(results, indent=2)
        except json.JSONDecodeError:
            # Not a JSON string, analyze as a single file
            pass
        
        # Analyze single file
        result = self._analyze_code(code, file_path)
        return json.dumps(result, indent=2)
    
    async def _arun(self, code: str, file_path: str = "unknown.py") -> str:
        """Async version of _run."""
        return self._run(code, file_path)