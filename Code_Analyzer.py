"""
CrewAI Code Analyzer Project
----------------------------
A multi-agent system that analyzes Python projects, indexes code,
generates pytest test cases, executes them, and produces documentation.

Developed by: @Bhanu_Mahesh

"""

import os
import sys
import json
import glob
import ast
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from utils import get_openai_api_key

openai_api_key = get_openai_api_key()

# Custom Tools
class CodeReaderTool(BaseTool):
    """Tool for reading Python project files."""
    name: str = "CodeReaderTool"
    description: str = "Reads Python files from a project directory."
    
    def _run(self, project_path: str) -> str:
        """Read all Python files in the specified directory and subdirectories."""
        if not os.path.exists(project_path):
            return f"Error: Path '{project_path}' does not exist."
        
        python_files = {}
        for file_path in glob.glob(f"{project_path}/**/*.py", recursive=True):
            relative_path = os.path.relpath(file_path, project_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    python_files[relative_path] = file.read()
            except Exception as e:
                python_files[relative_path] = f"Error reading file: {str(e)}"
        
        return json.dumps(python_files, indent=2)


class CodeAnalyzerTool(BaseTool):
    """Tool for analyzing Python code structure."""
    name: str = "CodeAnalyzerTool"
    description: str = "Analyzes Python code to extract functions, classes, and dependencies."
    
    def _run(self, code: str, file_path: str = "unknown.py") -> str:
        """Analyze Python code to extract its structure."""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line_number": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "methods": methods,
                        "line_number": node.lineno
                    })
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for name in node.names:
                            imports.append(f"{node.module}.{name.name}")
            
            analysis = {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "imports": imports
            }
            
            return json.dumps(analysis, indent=2)
        except SyntaxError as e:
            return f"Syntax error in {file_path}: {str(e)}"
        except Exception as e:
            return f"Error analyzing {file_path}: {str(e)}"


class TestGeneratorTool(BaseTool):
    """Tool for generating pytest test cases."""
    name: str = "TestGeneratorTool"
    description: str = "Generates pytest test cases based on code analysis."
    
    def _run(self, code_analysis: str, output_dir: str) -> str:
        """Generate pytest test files based on code analysis."""
        try:
            analysis = json.loads(code_analysis)
            file_path = analysis.get("file_path", "unknown.py")
            file_name = os.path.basename(file_path)
            module_name = os.path.splitext(file_name)[0]
            test_file_path = os.path.join(output_dir, f"test_{module_name}.py")
            
            test_code = f"# Generated test file for {file_path}\n"
            test_code += "import pytest\n"
            
            # Create import for the module being tested
            relative_import = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
            test_code += f"from {relative_import} import *\n\n"
            
            # Generate tests for functions
            for func in analysis.get("functions", []):
                func_name = func["name"]
                if func_name.startswith("_"):  # Skip private functions
                    continue
                
                test_code += f"\ndef test_{func_name}():\n"
                test_code += f"    \"\"\"{func_name} should work as expected.\"\"\"\n"
                
                # Create basic assertions based on function name patterns
                if "get" in func_name.lower():
                    test_code += f"    result = {func_name}()\n"
                    test_code += f"    assert result is not None  # Replace with specific assertions\n"
                elif "is_" in func_name.lower() or "has_" in func_name.lower():
                    test_code += f"    result = {func_name}()\n"
                    test_code += f"    assert isinstance(result, bool)\n"
                else:
                    args = ", ".join(["None" for _ in func["args"] if _ != "self"])
                    test_code += f"    result = {func_name}({args})\n"
                    test_code += f"    # TODO: Add assertions for {func_name}\n"
            
            # Generate tests for classes
            for cls in analysis.get("classes", []):
                cls_name = cls["name"]
                test_code += f"\nclass Test{cls_name}:\n"
                
                # Create setup method
                test_code += f"    @pytest.fixture\n"
                test_code += f"    def {cls_name.lower()}_instance(self):\n"
                test_code += f"        return {cls_name}()\n\n"
                
                # Create tests for class methods
                for method in cls.get("methods", []):
                    if method.startswith("_") or method == "__init__":  # Skip private/init methods
                        continue
                    
                    test_code += f"    def test_{method}(self, {cls_name.lower()}_instance):\n"
                    test_code += f"        \"\"\"{cls_name}.{method} should work as expected.\"\"\"\n"
                    test_code += f"        # TODO: Add assertions for {cls_name}.{method}\n"
            
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Write the test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            return f"Generated test file: {test_file_path}"
        except Exception as e:
            return f"Error generating test file: {str(e)}"


class TestRunnerTool(BaseTool):
    """Tool for running pytest test cases."""
    name: str = "TestRunnerTool"
    description: str = "Runs pytest test cases and captures results."
    
    def _run(self, test_dir: str) -> str:
        """Run pytest on the specified test directory and return results."""
        try:
            if not os.path.exists(test_dir):
                return f"Error: Test directory '{test_dir}' does not exist."
            
            # Run pytest with detailed output
            result = subprocess.run(
                ["python", "-m", "pytest", test_dir, "-v", "--no-header"],
                capture_output=True,
                text=True
            )
            
            return {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return f"Error running tests: {str(e)}"


class DocumentationGeneratorTool(BaseTool):
    """Tool for generating documentation based on code analysis and test results."""
    name: str = "DocumentationGeneratorTool"
    description: str = "Generates comprehensive documentation for the analyzed code and test results."
    
    def _run(self, code_analysis: str, test_results: str, output_path: str) -> str:
        """Generate documentation based on code analysis and test results."""
        try:
            # Parse inputs
            analysis = json.loads(code_analysis) if isinstance(code_analysis, str) else code_analysis
            results = json.loads(test_results) if isinstance(test_results, str) else test_results
            
            # Create documentation
            doc = "# Code Analysis and Test Documentation\n\n"
            
            # Project overview
            doc += "## Project Overview\n\n"
            files = list(set([a.get("file_path", "unknown.py") for a in analysis if isinstance(a, dict)]))
            doc += f"This documentation covers {len(files)} Python files.\n\n"
            
            # Code structure
            doc += "## Code Structure\n\n"
            for file_analysis in analysis:
                if not isinstance(file_analysis, dict):
                    continue
                    
                file_path = file_analysis.get("file_path", "unknown.py")
                doc += f"### {file_path}\n\n"
                
                # Classes
                classes = file_analysis.get("classes", [])
                if classes:
                    doc += "#### Classes\n\n"
                    for cls in classes:
                        doc += f"- **{cls['name']}**\n"
                        for method in cls.get("methods", []):
                            doc += f"  - `{method}()`\n"
                    doc += "\n"
                
                # Functions
                functions = file_analysis.get("functions", [])
                if functions:
                    doc += "#### Functions\n\n"
                    for func in functions:
                        args = ", ".join(func.get("args", []))
                        doc += f"- `{func['name']}({args})`\n"
                    doc += "\n"
                
                # Dependencies
                imports = file_analysis.get("imports", [])
                if imports:
                    doc += "#### Dependencies\n\n"
                    for imp in imports:
                        doc += f"- {imp}\n"
                    doc += "\n"
            
            # Test results
            doc += "## Test Results\n\n"
            
            if isinstance(results, dict):
                return_code = results.get("return_code", -1)
                stdout = results.get("stdout", "")
                stderr = results.get("stderr", "")
                
                doc += f"### Summary\n\n"
                doc += f"Test execution return code: {return_code}\n\n"
                
                if stdout:
                    doc += "### Test Output\n\n"
                    doc += "```\n"
                    doc += stdout
                    doc += "```\n\n"
                
                if stderr:
                    doc += "### Errors\n\n"
                    doc += "```\n"
                    doc += stderr
                    doc += "```\n\n"
            
            # Write documentation to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc)
            
            return f"Documentation generated: {output_path}"
        except Exception as e:
            return f"Error generating documentation: {str(e)}"


# Creating Agents
def create_agents(model_name="gpt-4", temperature=0.2):
    """Create all the specialized agents needed for the project."""
    
    # Tools initialization
    code_reader_tool = CodeReaderTool()
    code_analyzer_tool = CodeAnalyzerTool()
    test_generator_tool = TestGeneratorTool()
    test_runner_tool = TestRunnerTool()
    doc_generator_tool = DocumentationGeneratorTool()
    
    # Code Reader Agent
    code_reader_agent = Agent(
        role="Code Reader",
        goal="Read and collect all Python code from a project directory",
        backstory="You are an expert at navigating project structures and extracting all relevant code files. "
                "You make sure no important code files are missed, and you organize them properly.",
        verbose=True,
        tools=[code_reader_tool],
        allow_delegation=True
    )
    
    # Code Analyzer Agent
    code_analyzer_agent = Agent(
        role="Code Analyzer",
        goal="Analyze Python code to understand its structure, logic, and relationships",
        backstory="You are a seasoned Python developer with an eye for detail. "
                "You can quickly understand code architecture, identify patterns, and extract meaningful insights.",
        verbose=True,
        tools=[code_analyzer_tool],
        allow_delegation=True
    )
    
    # Test Writer Agent
    test_writer_agent = Agent(
        role="Test Writer",
        goal="Create comprehensive pytest test cases for Python code",
        backstory="You are a test-driven development expert who creates efficient, effective tests. "
                "You know how to test edge cases and ensure high code coverage.",
        verbose=True,
        tools=[test_generator_tool],
        allow_delegation=True
    )
    
    # Test Runner Agent
    test_runner_agent = Agent(
        role="Test Runner",
        goal="Execute test cases and collect detailed results",
        backstory="You are a QA professional who ensures tests run correctly and results are accurately reported. "
                "You can diagnose test failures and provide clear information.",
        verbose=True,
        tools=[test_runner_tool],
        allow_delegation=True
    )
    
    # Documentation Agent
    documentation_agent = Agent(
        role="Documentation Specialist",
        goal="Create comprehensive documentation that is clear, complete, and professional",
        backstory="You are an expert technical writer who can translate complex technical details into "
                "accessible, well-organized documentation. You know how to structure technical documents "
                "for maximum clarity and usefulness.",
        verbose=True,
        tools=[doc_generator_tool],
        allow_delegation=True
    )
    
    return {
        "code_reader": code_reader_agent,
        "code_analyzer": code_analyzer_agent,
        "test_writer": test_writer_agent,
        "test_runner": test_runner_agent,
        "documentation": documentation_agent
    }


# Creating Tasks
def create_tasks(agents, project_path, output_dir):
    """Create all the required tasks for the project analysis workflow."""
    
    # Task 1: Read all Python files from the project
    read_code_task = Task(
        description=(
            f"Read all Python code files from the project located at '{project_path}'. "
            f"Make sure to explore all subdirectories and collect all .py files."
        ),
        expected_output=(
            "A JSON string containing all the Python files in the project, "
            "with file paths as keys and file contents as values."
        ),
        agent=agents["code_reader"]
    )
    
    # Task 2: Analyze the code structure
    analyze_code_task = Task(
        description=(
            "Analyze each Python file to extract functions, classes, methods, and dependencies. "
            "Identify the key components and relationships in the code."
        ),
        expected_output=(
            "A list of JSON objects, each containing the analysis of a Python file, "
            "including functions, classes, methods, and imports."
        ),
        agent=agents["code_analyzer"],
        context=[read_code_task]
    )
    
    # Task 3: Generate test cases
    generate_tests_task = Task(
        description=(
            f"Generate pytest test cases for the analyzed code. Save the test files to '{output_dir}/tests'. "
            f"Create appropriate test files, fixtures, and assertions based on the code analysis."
        ),
        expected_output=(
            "A list of generated test file paths and a summary of the test coverage."
        ),
        agent=agents["test_writer"],
        context=[analyze_code_task]
    )
    
    # Task 4: Run the test cases
    run_tests_task = Task(
        description=(
            f"Run the generated test cases using pytest and collect the results. "
            f"Execute tests in the directory '{output_dir}/tests'."
        ),
        expected_output=(
            "Complete test results including successes, failures, and error messages."
        ),
        agent=agents["test_runner"],
        context=[generate_tests_task]
    )
    
    # Task 5: Generate documentation
    generate_docs_task = Task(
        description=(
            f"Create comprehensive documentation based on the code analysis and test results. "
            f"Save the documentation to '{output_dir}/documentation.md'. "
            f"Include code structure, relationships, test results, and recommendations."
        ),
        expected_output=(
            "A comprehensive Markdown file documenting the project structure, code components, "
            "test results, and suggestions for improvement."
        ),
        agent=agents["documentation"],
        context=[analyze_code_task, run_tests_task]
    )
    
    return [
        read_code_task,
        analyze_code_task,
        generate_tests_task,
        run_tests_task,
        generate_docs_task
    ]


# Creating the Crew
def create_crew(agents, tasks, model_name="gpt-4o-mini"):
    """Create a CrewAI crew with the specified agents and tasks."""
    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        manager_llm=ChatOpenAI(model=model_name, temperature=0.2),
        process=Process.sequential,
        verbose=True
    )


# Asynchronous execution
async def run_analysis(project_path, output_dir, model_name="gpt-4o-mini"):
    """Run the complete code analysis process asynchronously."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "tests"), exist_ok=True)
    
    # Create agents, tasks, and crew
    agents = create_agents(model_name=model_name)
    tasks = create_tasks(agents, project_path, output_dir)
    crew = create_crew(agents, tasks, model_name=model_name)
    
    # Run the crew
    return await asyncio.to_thread(crew.kickoff)


# Main function
def main():
    """Main entry point for the CLI application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Python projects, generate tests, and create documentation.")
    parser.add_argument("project_path", help="Path to the Python project to analyze")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory for test files and documentation")
    parser.add_argument("--model", "-m", default="gpt-3.5-turbo", help="OpenAI model to use (default: gpt-3.5-turbo)")
    
    args = parser.parse_args()
    
    # Run the analysis
    print(f"Starting analysis of project: {args.project_path}")
    print(f"Output will be saved to: {args.output_dir}")
    print(f"Using model: {args.model}")
    
    result = asyncio.run(run_analysis(args.project_path, args.output_dir, args.model))
    
    print("Analysis complete!")
    print(result)


if __name__ == "__main__":
    main()