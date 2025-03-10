# CrewAI Code Analyzer

A multi-agent system that analyzes Python projects, indexes code, generates and runs pytest test cases, and produces comprehensive documentation.

## Features

- 🔍 **Automatic Code Reading**: Scans directories to discover and extract Python files
- 📊 **Code Analysis**: Parses Python files to extract functions, classes, methods, and dependencies
- ✅ **Test Generation**: Creates pytest test cases based on code analysis
- 🧪 **Test Execution**: Runs the generated tests and captures results
- 📝 **Documentation**: Generates comprehensive Markdown documentation

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in requirements.txt

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crewai-code-analyzer.git
cd crewai-code-analyzer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key  # On Windows: set OPENAI_API_KEY=your-api-key

# Run the analyzer
python code_analyzer.py /path/to/your/python/project --output-dir output --model gpt-3.5-turbo
```

### Command Line Arguments

- `project_path`: Path to the Python project to analyze (required)
- `--output-dir`, `-o`: Output directory for test files and documentation (default: "output")
- `--model`, `-m`: OpenAI model to use (default: "gpt-3.5-turbo")

## How It Works

The system uses CrewAI to coordinate multiple specialized agents:

1. **Code Reader Agent**: Scans the project directory and reads all Python files
2. **Code Analyzer Agent**: Analyzes the code structure to extract functions, classes, and dependencies
3. **Test Writer Agent**: Generates pytest test cases based on the code analysis
4. **Test Runner Agent**: Executes the generated tests and collects results
5. **Documentation Agent**: Creates comprehensive documentation of the code and test results

These agents work together in a sequential workflow, with each agent building on the output of the previous ones.

## Output

The system generates the following outputs in the specified output directory:

- `/tests`: Contains generated pytest test files
- `documentation.md`: Comprehensive documentation of the code structure and test results

## Example

```bash
python code_analyzer.py ./my_python_project --output-dir ./analysis_results
```

This will:
1. Read all Python files in `./my_python_project`
2. Analyze the code structure
3. Generate test files in `./analysis_results/tests`
4. Run the tests
5. Create documentation at `./analysis_results/documentation.md`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.