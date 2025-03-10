# Code Analysis and Test Documentation

## Project Overview

This documentation covers 3 Python files.

## Code Structure

### utils.py

#### Functions

- `load_env()`
- `get_openai_api_key()`
- `get_serper_api_key()`
- `pretty_print_result(result)`

#### Dependencies

- os
- dotenv.load_dotenv
- dotenv.find_dotenv

### Code_Analyzer.py

#### Classes

- **CodeReaderTool**
  - `_run()`
- **CodeAnalyzerTool**
  - `_run()`
- **TestGeneratorTool**
  - `_run()`
- **TestRunnerTool**
  - `_run()`
- **DocumentationGeneratorTool**
  - `_run()`

#### Functions

- `create_agents(model_name, temperature)`
- `create_tasks(agents, project_path, output_dir)`
- `create_crew(agents, tasks, model_name)`
- `main()`
- `_run(self, project_path)`
- `_run(self, code, file_path)`
- `_run(self, code_analysis, output_dir)`
- `_run(self, test_dir)`
- `_run(self, code_analysis, test_results, output_path)`

#### Dependencies

- os
- sys
- json
- glob
- ast
- asyncio
- subprocess
- pathlib.Path
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- crewai.Agent
- crewai.Task
- crewai.Crew
- crewai.Process
- crewai.tools.BaseTool
- langchain_openai.ChatOpenAI
- pydantic.BaseModel
- pydantic.Field
- utils.get_openai_api_key
- argparse

### example_runner.py

#### Dependencies

- os
- sys
- asyncio
- pathlib.Path
- Code_Analyzer.run_analysis

## Test Results

### Summary

Test execution return code: -1

