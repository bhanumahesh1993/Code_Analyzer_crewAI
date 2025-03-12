"""
CrewAI Code Analyzer
-------------------

A multi-agent system that analyzes Python projects, indexes code,
generates pytest test cases, executes them, and produces documentation.

Main components:
- Code Reading: Extracts Python files from a project
- Code Analysis: Parses code to extract structure and patterns
- Test Generation: Creates pytest test cases based on analysis
- Test Execution: Runs tests and collects results
- Documentation: Generates comprehensive documentation

Developed by: @Bhanu_Mahesh
"""

__version__ = "0.1.0"

from code_analyzer.main import run_analysis

__all__ = ["run_analysis"]