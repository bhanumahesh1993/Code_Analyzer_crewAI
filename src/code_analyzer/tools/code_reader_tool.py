"""
Code Reader Tool for the Code Analyzer.
Reads Python files from a project directory.
"""

import os
import glob
import json
from typing import Dict, List, Any
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import Field

from code_analyzer.utils import logger


class CodeReaderTool(BaseTool):
    """Tool for reading Python project files."""
    name: str = "CodeReaderTool"
    description: str = "Reads Python files from a project directory."
    
    project_path: str = Field(
        description="Path to the Python project directory to analyze"
    )
    
    def _run(self, project_path: str = None) -> str:
        """
        Read all Python files in the specified directory and subdirectories.
        
        Args:
            project_path: Path to the Python project directory
            
        Returns:
            JSON string containing file paths and their contents
        """
        # Use provided path or the tool's configured path
        path_to_use = project_path or self.project_path
        
        logger.info(f"CodeReaderTool EXPLICITLY reading Python files from: {path_to_use}")
        logger.info(f"Path exists: {os.path.exists(path_to_use)}")
        logger.info(f"Absolute path: {os.path.abspath(path_to_use)}")
        
        if not os.path.exists(path_to_use):
            error_msg = f"Error: Path '{path_to_use}' does not exist."
            logger.error(error_msg)
            return error_msg
        
        python_files = {}
        file_count = 0
        error_count = 0
        
        # Use Path for better path handling across OS
        project_path_obj = Path(path_to_use).resolve()  # Get absolute path
        
        # Find all Python files
        for file_path in project_path_obj.glob("**/*.py"):
            # Check if the file is actually within the project path
            # This prevents traversing outside the intended directory
            if project_path_obj in file_path.parents or project_path_obj == file_path.parent:
                file_count += 1
                relative_path = file_path.relative_to(project_path_obj).as_posix()
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        python_files[relative_path] = file.read()
                    logger.debug(f"Read file: {relative_path}")
                except Exception as e:
                    error_count += 1
                    python_files[relative_path] = f"Error reading file: {str(e)}"
                    logger.error(f"Error reading {relative_path}: {str(e)}")
        
        logger.info(f"Read {file_count} Python files. Encountered {error_count} errors.")
        
        if not python_files:
            logger.warning(f"No Python files found in {path_to_use}")
            return json.dumps({"error": "No Python files found in the specified path."})
        
        # Return as JSON string
        return json.dumps(python_files, indent=2)
    
    async def _arun(self, project_path: str = None) -> str:
        """Async version of _run."""
        return self._run(project_path)