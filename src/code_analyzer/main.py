"""
Main entry point for the Code Analyzer.
"""

import os
import sys
import asyncio
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from code_analyzer.crew import create_code_analyzer_crew
from code_analyzer.utils import (
    logger,
    setup_output_directories,
    validate_project_path,
    format_time_elapsed,
    is_valid_python_project,
    is_github_url,
    download_github_repo
)
from code_analyzer.config.config import (
    get_openai_api_key,
    get_default_model,
    get_default_output_dir
)


async def run_analysis(
    project_path: str,
    output_dir: str = None,
    model_name: str = None,
    temperature: float = None
) -> Dict[str, Any]:
    """
    Run the complete code analysis process asynchronously.
    
    Args:
        project_path: Path to the project to analyze
        output_dir: Base directory for output files
        model_name: Name of the model to use
        temperature: Temperature for the model
        
    Returns:
        Dictionary with analysis results
    """
    start_time = time.time()
    
    try:
        # Check if the project path is a GitHub URL
        if is_github_url(project_path):
            # Create a temporary directory for the repository
            temp_dir = os.path.join(output_dir or get_default_output_dir(), "repos")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download the repository
            project_path = download_github_repo(project_path, temp_dir)
            logger.info(f"Analyzing downloaded repository: {project_path}")
        
        # Validate and normalize project path
        project_path = validate_project_path(project_path)
        logger.info(f"Analyzing project: {project_path}")
        
        # Use default output directory if not provided
        output_dir = output_dir or get_default_output_dir()
        
        # Extract repo name from project path
        repo_name = os.path.basename(os.path.normpath(project_path))
        
        # Create output directories using repo name instead of timestamp
        output_dirs = setup_output_directories(output_dir, repo_name)
        logger.info(f"Output will be saved to: {output_dirs['main']}")
        
        # Create documentation paths
        docs_path = os.path.join(output_dirs["docs"], "documentation.md")
        
        # Create and run the crew
        crew = create_code_analyzer_crew(
            project_path=project_path,
            output_dirs=output_dirs,
            model_name=model_name,
            temperature=temperature
        )
        
        # Run the crew
        logger.info("Starting analysis...")
        result = await asyncio.to_thread(crew.kickoff)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        formatted_time = format_time_elapsed(elapsed_time)
        
        logger.info(f"Analysis completed in {formatted_time}")
        
        # Return results
        return {
            "status": "success",
            "project_path": project_path,
            "output_dirs": output_dirs,
            "documentation_path": docs_path,
            "elapsed_time": elapsed_time,
            "formatted_time": formatted_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        formatted_time = format_time_elapsed(elapsed_time)
        
        # Return error
        return {
            "status": "error",
            "project_path": project_path,
            "error": str(e),
            "elapsed_time": elapsed_time,
            "formatted_time": formatted_time
        }


def check_api_key() -> bool:
    """
    Check if OpenAI API key is available.
    
    Returns:
        True if API key is available, False otherwise
    """
    try:
        get_openai_api_key()
        return True
    except ValueError:
        return False


def cli():
    """Command line interface for the Code Analyzer."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Analyze Python projects, generate tests, and create documentation."
    )
    
    # Add arguments
    parser.add_argument(
    "project_path",
    help="Path to the Python project to analyze or a GitHub repository URL (e.g., https://github.com/username/repository)"
    )
    parser.add_argument(
    "--output-dir", "-o",
    default="./test_analysis",  # Change this from get_default_output_dir() to "./test_analysis"
    help="Output directory for test files and documentation (default: ./test_analysis)"
    )
    parser.add_argument(
        "--model", "-m",
        default=get_default_model(),
        help=f"OpenAI model to use (default: {get_default_model()})"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.2,
        help="Temperature for the model (default: 0.2)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if API key is available
    if not check_api_key():
        print("Error: OpenAI API key not found.")
        print("Please set the OPENAI_API_KEY environment variable.")
        print("You can do this by running:")
        print("  export OPENAI_API_KEY=your-api-key  # On Linux/macOS")
        print("  set OPENAI_API_KEY=your-api-key     # On Windows")
        sys.exit(1)
    
    # Inside the cli() function where you handle GitHub repositories
    if is_github_url(args.project_path):
        print(f"Detected GitHub repository: {args.project_path}")
        
        # Extract repo name
        repo_name = args.project_path.split('/')[-1].replace('.git', '')
        
        # Create a temporary directory for the repository
        temp_dir = os.path.join(args.output_dir, "repos")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Path to extract the repository to
        repo_path = os.path.join(temp_dir, repo_name)
        
        # Remove the directory if it already exists
        if os.path.exists(repo_path):
            print(f"Repository directory already exists, removing: {repo_path}")
            import shutil
            shutil.rmtree(repo_path)
        
        try:
            # Download the repository
            project_path = download_github_repo(args.project_path, temp_dir)
            print(f"Repository downloaded to: {project_path}")
            args.project_path = project_path
        except Exception as e:
            print(f"Error downloading repository: {str(e)}")
            sys.exit(1)

    # Check if project path is valid
    if not is_valid_python_project(args.project_path):
        print(f"Error: No Python files found in {args.project_path}")
        print("Please provide a valid Python project path.")
        sys.exit(1)
    
    # Set log level
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # Print welcome message
    print("=" * 80)
    print(f"CrewAI Code Analyzer")
    print("=" * 80)
    print(f"Project: {args.project_path}")
    print(f"Output: {args.output_dir}")
    print(f"Model: {args.model}")
    print(f"Temperature: {args.temperature}")
    print("=" * 80)
    

    # Inside the cli() function, before calling run_analysis
    if is_github_url(args.project_path):
        print(f"Detected GitHub repository: {args.project_path}")
        # Create a temporary directory for the repository
        temp_dir = os.path.join(args.output_dir, "repos")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Download the repository
            project_path = download_github_repo(args.project_path, temp_dir)
            print(f"Repository downloaded to: {project_path}")
            args.project_path = os.path.abspath(project_path)
            print(f"Analysis path set to: {args.project_path}")
        except Exception as e:
            print(f"Error downloading repository: {str(e)}")
            sys.exit(1)
    else:
        project_path = args.project_path


    # Run analysis
    try:
        result = asyncio.run(run_analysis(
            project_path=args.project_path,
            output_dir=args.output_dir,
            model_name=args.model,
            temperature=args.temperature
        ))
        
        # Check if analysis was successful
        if result["status"] == "success":
            print("\nAnalysis complete!")
            print(f"Time taken: {result['formatted_time']}")
            print("\nOutput location:")
            for dir_name, dir_path in result["output_dirs"].items():
                print(f"- {dir_name.capitalize()}: {dir_path}")
            
            print(f"\nDocumentation: {result['documentation_path']}")
            
            print("\nSummary:")
            print(result["result"])
        else:
            print("\nAnalysis failed!")
            print(f"Error: {result['error']}")
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()