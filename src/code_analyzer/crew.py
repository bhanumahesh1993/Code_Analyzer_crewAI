"""
Crew orchestration for the Code Analyzer.
"""

import os
from typing import Dict, List, Any, Optional
import yaml

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from code_analyzer.tools import (
    CodeReaderTool,
    CodeAnalyzerTool,
    TestGeneratorTool,
    TestRunnerTool,
    DocumentationGeneratorTool
)
from code_analyzer.config.config import (
    load_agents_config,
    load_tasks_config,
    get_openai_api_key,
    get_default_model,
    get_model_temperature
)
from code_analyzer.utils import logger


def create_tools(project_path: str, output_dirs: Dict[str, str]) -> Dict[str, Any]:
    """
    Create all the tools needed for the code analysis.
    
    Args:
        project_path: Path to the project being analyzed
        output_dirs: Dictionary of output directories
        
    Returns:
        Dictionary of tool instances
    """
    logger.info("Creating tools...")
    
    # Create output directories
    for dir_name, dir_path in output_dirs.items():
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
    
    return {
        "CodeReaderTool": CodeReaderTool(project_path=project_path),
        "CodeAnalyzerTool": CodeAnalyzerTool(),
        "TestGeneratorTool": TestGeneratorTool(output_dir=output_dirs["tests"]),
        "TestRunnerTool": TestRunnerTool(),
        "DocumentationGeneratorTool": DocumentationGeneratorTool()
    }


def create_agents(tools: Dict[str, Any], model_name: str = None, temperature: float = None) -> Dict[str, Agent]:
    """
    Create all the agents needed for the code analysis.
    
    Args:
        tools: Dictionary of tool instances
        model_name: Name of the model to use
        temperature: Temperature for the model
        
    Returns:
        Dictionary of agent instances
    """
    logger.info("Creating agents...")
    
    # Get configuration
    agents_config = load_agents_config()
    
    # Use provided values or defaults
    model = model_name or get_default_model()
    temp = temperature if temperature is not None else get_model_temperature()
    
    logger.info(f"Using model: {model}, temperature: {temp}")
    
    # Create agents
    agents = {}
    
    for agent_id, config in agents_config.items():
        # Get tools for this agent
        agent_tools = [tools[tool_name] for tool_name in config.get("tools", [])]
        
        # Create agent
        agents[agent_id] = Agent(
            role=config.get("role", f"Agent {agent_id}"),
            goal=config.get("goal", "Assist with code analysis"),
            backstory=config.get("backstory", ""),
            tools=agent_tools,
            allow_delegation=config.get("allow_delegation", True),
            verbose=config.get("verbose", True)
        )
        
        logger.debug(f"Created agent: {agent_id}")
    
    return agents


def create_tasks(agents: Dict[str, Agent], project_path: str, output_dirs: Dict[str, str]) -> List[Task]:
    """
    Create all the tasks needed for the code analysis.
    
    Args:
        agents: Dictionary of agent instances
        project_path: Path to the project being analyzed
        output_dirs: Dictionary of output directories
        
    Returns:
        List of task instances
    """
    logger.info("Creating tasks...")
    logger.info(f"Using project path for tasks: {project_path}")  # Add debugging
    
    # Get configuration
    tasks_config = load_tasks_config()
    
    # Create tasks
    tasks = []
    created_tasks = {}
    
    for task_id, config in tasks_config.items():
        # Replace placeholders in description
        description = config.get("description", "")
        description = description.replace("{project_path}", project_path)
        
        # Add explicit project path to all tasks - THIS IS KEY
        if "code_reader" in config.get("agent", ""):
            description += f"\n\nThe exact project path to analyze is: {project_path}"
        
        # Replace output directories in description
        for dir_name, dir_path in output_dirs.items():
            description = description.replace(f"{{{dir_name}}}", dir_path)
        
        # Get context tasks
        context_task_ids = config.get("context", [])
        context_tasks = []
        
        # Add context from other tasks
        for context_task_id in context_task_ids:
            if context_task_id in created_tasks:
                context_tasks.append(created_tasks[context_task_id])
        
        # Create task with context
        task = Task(
            description=description,
            expected_output=config.get("expected_output", ""),
            agent=agents[config.get("agent")],
            context=context_tasks  # Pass the context tasks directly
        )
        
        # Store task for context references
        created_tasks[task_id] = task
        tasks.append(task)
        logger.debug(f"Created task: {task_id}")
    
    return tasks


def create_crew(agents: Dict[str, Agent], tasks: List[Task], model_name: str = None) -> Crew:
    """
    Create a crew for the code analysis.
    
    Args:
        agents: Dictionary of agent instances
        tasks: List of task instances
        model_name: Name of the model to use
        
    Returns:
        Crew instance
    """
    logger.info("Creating crew...")
    
    # Use provided model or default
    model = model_name or get_default_model()
    
    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        manager_llm=ChatOpenAI(model=model, temperature=0.2),
        process=Process.sequential,
        verbose=True
    )


def create_code_analyzer_crew(project_path: str, output_dirs: Dict[str, str], model_name: str = None, temperature: float = None) -> Crew:
    """
    Create a complete code analyzer crew with all agents and tasks.
    
    Args:
        project_path: Path to the project being analyzed
        output_dirs: Dictionary of output directories
        model_name: Name of the model to use
        temperature: Temperature for the model
        
    Returns:
        Crew instance
    """
    logger.info(f"Creating Code Analyzer crew for project: {project_path}")
    
    # Create tools
    tools = create_tools(project_path, output_dirs)
    
    # Create agents
    agents = create_agents(tools, model_name, temperature)
    
    # Create tasks
    tasks = create_tasks(agents, project_path, output_dirs)
    
    # Create crew
    crew = create_crew(agents, tasks, model_name)
    
    return crew