#!/usr/bin/env python
"""
Example runner script for the CrewAI Code Analyzer.
This script demonstrates how to use the analyzer on a sample project.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the run_analysis function
from Code_Analyzer import run_analysis

async def main():
    # Path to the sample project
    sample_project_path = "./sample_project"
    
    # Output directory
    output_dir = "./analysis_output"
    
    print(f"Starting analysis of {sample_project_path}")
    print(f"Results will be saved to {output_dir}")
    
    # Run the analysis
    result = await run_analysis(
        project_path=sample_project_path,
        output_dir=output_dir,
        model_name="gpt-3.5-turbo"  # Use gpt-4 for better results if available
    )
    
    print("\nAnalysis complete!")
    print("\nSummary:")
    print(result)
    
    # Print paths to the generated files
    docs_path = os.path.join(output_dir, "documentation.md")
    tests_dir = os.path.join(output_dir, "tests")
    
    print(f"\nDocumentation: {docs_path}")
    print(f"Test files: {tests_dir}")
    
    # List generated test files
    test_files = list(Path(tests_dir).glob("*.py"))
    if test_files:
        print("\nGenerated test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")

if __name__ == "__main__":
    asyncio.run(main())