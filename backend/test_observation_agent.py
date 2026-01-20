"""
Quick test script for ObservationAgent
Tests basic code analysis functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from agents.observation_agent import ObservationAgent
from agents.base_agent import TaskContext
from messaging.message_bus_stub import MessageBusStub
from agents.agent_registry_stub import AgentRegistryStub


# Sample Python code to analyze
SAMPLE_CODE = '''
import ast
from typing import List, Dict

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

def process_data(items: List[str]) -> Dict[str, int]:
    """Process a list of items and return counts."""
    result = {}
    for item in items:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result

class DataProcessor:
    """Process and analyze data."""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, data: List[int]) -> int:
        """Process data and return total."""
        total = 0
        for value in data:
            if value > 0:
                total += value
        return total
'''


async def test_observation_agent():
    """Test ObservationAgent functionality."""
    print("=" * 60)
    print("Testing ObservationAgent")
    print("=" * 60)
    
    # Create dependencies
    message_queue = MessageBusStub()
    
    # Create agent
    agent = ObservationAgent(
        message_queue=message_queue,
        agent_id="test-observation-agent",
        priority=8
    )
    
    print("\n1. Agent Capabilities:")
    for cap in agent.capabilities:
        print(f"   - {cap.name} v{cap.version} (threshold: {cap.confidence_threshold})")
    
    # Create task
    task = TaskContext(
        task_id="test-001",
        task_type="code_analysis",
        payload={
            "code": SAMPLE_CODE,
            "file_path": "sample.py"
        },
        conversation_id="conv-001",
        priority=5
    )
    
    print("\n2. Can Handle Task?")
    can_handle, confidence = await agent.can_handle(task)
    print(f"   Can handle: {can_handle}")
    print(f"   Confidence: {confidence}")
    
    if can_handle:
        print("\n3. Executing Task...")
        result = await agent.execute_task(task)
        
        print(f"\n4. Results:")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        
        if result.success:
            data = result.result
            
            print(f"\n   Summary:")
            print(f"   - Functions: {data['summary']['total_functions']}")
            print(f"   - Classes: {data['summary']['total_classes']}")
            print(f"   - Imports: {data['summary']['total_imports']}")
            print(f"   - Lines of Code: {data['summary']['lines_of_code']}")
            print(f"   - Avg Complexity: {data['summary']['average_complexity']}")
            
            print(f"\n   Functions Found:")
            for func in data['functions']:
                params = ', '.join(func['parameters'])
                print(f"   - {func['name']}({params}) [line {func['line_number']}, complexity: {func['complexity']}]")
                if func['docstring']:
                    print(f"     Docstring: {func['docstring'][:50]}...")
            
            print(f"\n   Classes Found:")
            for cls in data['classes']:
                methods = ', '.join(cls['methods'])
                print(f"   - {cls['name']} [line {cls['line_number']}]")
                print(f"     Methods: {methods}")
                if cls['base_classes']:
                    print(f"     Inherits: {', '.join(cls['base_classes'])}")
            
            print(f"\n   Imports Found:")
            for imp in data['imports']:
                if imp['names']:
                    print(f"   - from {imp['module']} import {', '.join(imp['names'])}")
                else:
                    print(f"   - import {imp['module']}")
            
            print(f"\n   Complexity Metrics:")
            complexity = data['complexity']
            print(f"   - Total Lines: {complexity['total_lines']}")
            print(f"   - Lines of Code: {complexity['loc']}")
            print(f"   - Cyclomatic Complexity: {complexity['cyclomatic_complexity']}")
            print(f"   - Average Complexity: {complexity['average_complexity']}")
        else:
            print(f"   Error: {result.error}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


async def test_invalid_code():
    """Test ObservationAgent with invalid Python code."""
    print("\n" + "=" * 60)
    print("Testing ObservationAgent with Invalid Code")
    print("=" * 60)
    
    # Create dependencies
    message_queue = MessageBusStub()
    
    # Create agent
    agent = ObservationAgent(
        message_queue=message_queue
    )
    
    # Invalid Python code
    invalid_code = '''
def broken_function(
    print("missing closing parenthesis"
'''
    
    task = TaskContext(
        task_id="test-002",
        task_type="code_analysis",
        payload={
            "code": invalid_code,
            "file_path": "broken.py"
        },
        conversation_id="conv-002",
        priority=5
    )
    
    print("\n1. Can Handle Invalid Code?")
    can_handle, confidence = await agent.can_handle(task)
    print(f"   Can handle: {can_handle}")
    print(f"   Confidence: {confidence}")
    
    if not can_handle:
        print("   ✅ Correctly rejected invalid Python code")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_observation_agent())
    asyncio.run(test_invalid_code())
