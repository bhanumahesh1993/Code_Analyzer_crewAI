# CrewAI Code Analyzer

A multi-agent system powered by CrewAI that analyzes Python projects, indexes code, generates and runs pytest test cases, and produces comprehensive documentation.

![Code Analyzer Banner](https://i.postimg.cc/Hkchq2jb/code-analyzer.jpg)

## 🌟 Features

- 🔍 **Automatic Code Reading**: Scans directories to discover and extract Python files
- 📊 **Detailed Code Analysis**: Parses Python files to extract functions, classes, methods, dependencies, and detects design patterns
- ✅ **Intelligent Test Generation**: Creates pytest test cases based on code analysis and function signatures
- 🧪 **Test Execution**: Runs the generated tests and captures detailed results
- 📝 **Comprehensive Documentation**: Generates well-structured Markdown documentation including code structure, test results, and improvement recommendations
- 🛠️ **Customizable Configuration**: YAML-based configuration for agents and tasks
- 🧠 **Knowledge-Based Analysis**: Uses a knowledge base of design patterns and code smells for better analysis

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in requirements.txt

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crewai-code-analyzer.git
cd crewai-code-analyzer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env to add your OpenAI API key
```

## 🔧 Usage

### Command Line Interface

```bash
# Basic usage
python -m code_analyzer.main /path/to/your/python/project

# With custom options
python -m code_analyzer.main /path/to/your/python/project \
    --output-dir ./my_analysis \
    --model gpt-4o \
    --temperature 0.3 \
    --verbose
```

### Command Line Arguments

- `project_path`: Path to the Python project to analyze (required)
- `--output-dir`, `-o`: Output directory for test files and documentation (default: "./output")
- `--model`, `-m`: OpenAI model to use (default: "gpt-3.5-turbo")
- `--temperature`, `-t`: Temperature for the model (default: 0.2)
- `--verbose`, `-v`: Enable verbose output

### Use as a Library

```python
import asyncio
from code_analyzer.main import run_analysis

async def analyze_my_project():
    result = await run_analysis(
        project_path="/path/to/your/project",
        output_dir="./my_analysis",
        model_name="gpt-3.5-turbo",
        temperature=0.2
    )
    
    print(f"Analysis completed in {result['formatted_time']}")
    print(f"Documentation available at: {result['documentation_path']}")

# Run the analysis
asyncio.run(analyze_my_project())
```

## 🧠 How It Works

The system uses CrewAI to coordinate multiple specialized AI agents:

### 👥 Agents

1. **Code Reader Agent**: Scans the project directory and reads all Python files
2. **Code Analyzer Agent**: Analyzes the code structure to extract functions, classes, and dependencies
3. **Test Writer Agent**: Generates pytest test cases based on the code analysis
4. **Test Runner Agent**: Executes the generated tests and collects results
5. **Documentation Agent**: Creates comprehensive documentation of the code and test results

### 🔄 Workflow

These agents work together in a sequential workflow:

```
Code Reader → Code Analyzer → Test Writer → Test Runner → Documentation Generator
```

## 📂 Project Structure

```
crewai-code-analyzer/
├── .gitignore
├── README.md
├── pyproject.toml
├── .env.example
├── requirements.txt
├── knowledge/
│   └── code_analyzer_patterns.json
└── src/
    └── code_analyzer/
        ├── __init__.py
        ├── main.py
        ├── crew.py
        ├── utils.py
        ├── tools/
        │   ├── __init__.py
        │   ├── code_reader_tool.py
        │   ├── code_analyzer_tool.py
        │   ├── test_generator_tool.py
        │   ├── test_runner_tool.py
        │   └── documentation_tool.py
        └── config/
            ├── __init__.py
            ├── agents.yaml
            ├── tasks.yaml
            └── config.py
```

## 📝 Output

The system generates the following outputs in the specified output directory:

- `tests/`: Contains generated pytest test files for each analyzed Python module
- `docs/documentation.md`: Comprehensive documentation of:
  - Project overview and metrics
  - Code structure and organization
  - Detailed documentation of classes and functions
  - Test results and coverage
  - Recommendations for improvements

## 🎯 Example

```bash
# Analyze the code analyzer itself
python -m code_analyzer.main ./src/code_analyzer --output-dir ./analysis --model gpt-4o
```

This will:
1. Read all Python files in `./src/code_analyzer`
2. Analyze the code structure
3. Generate test files in `./analysis/[timestamp]/tests`
4. Run the tests
5. Create documentation at `./analysis/[timestamp]/docs/documentation.md`

## 🚧 Customization

### Agents Configuration

Edit `src/code_analyzer/config/agents.yaml` to customize the agents' roles, goals, and backstories.

### Tasks Configuration

Edit `src/code_analyzer/config/tasks.yaml` to customize the tasks and their descriptions.

### Knowledge Base

Edit `knowledge/code_analyzer_patterns.json` to expand the knowledge base with additional design patterns, code smells, and testing patterns.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.