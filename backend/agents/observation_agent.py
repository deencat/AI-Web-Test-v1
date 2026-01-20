"""
ObservationAgent - Analyzes code structure and complexity

This agent uses Python's Abstract Syntax Tree (AST) module to analyze Python code
and extract valuable information about its structure, complexity, and components.

Capabilities:
- code_analysis: Analyze Python code structure (functions, classes, imports)
- complexity_analysis: Calculate code complexity metrics (LOC, cyclomatic complexity)

Usage:
    agent = ObservationAgent(message_bus, agent_registry)
    await agent.start()
    
    task = TaskContext(
        task_id="obs-1",
        task_type="code_analysis",
        payload={"code": "def hello(): print('world')"}
    )
    
    result = await agent.execute_task(task)
    # result.result = {
    #     "functions": [...],
    #     "classes": [...],
    #     "imports": [...],
    #     "complexity": {...}
    # }
"""

import ast
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from agents.base_agent import (
    BaseAgent,
    AgentCapability,
    TaskContext,
    TaskResult
)

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function in the code."""
    name: str
    parameters: List[str]
    return_type: Optional[str]
    line_number: int
    end_line_number: int
    docstring: Optional[str]
    decorators: List[str]
    is_async: bool
    complexity: int  # Cyclomatic complexity


@dataclass
class ClassInfo:
    """Information about a class in the code."""
    name: str
    base_classes: List[str]
    methods: List[str]
    line_number: int
    end_line_number: int
    docstring: Optional[str]
    decorators: List[str]


@dataclass
class ImportInfo:
    """Information about imports in the code."""
    module: str
    names: List[str]  # Specific names imported (empty for 'import module')
    alias: Optional[str]
    line_number: int


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity."""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class ObservationAgent(BaseAgent):
    """
    Agent that analyzes Python code structure and complexity.
    
    This agent can:
    1. Extract functions with parameters, return types, and decorators
    2. Extract classes with methods and inheritance
    3. Extract import statements
    4. Calculate complexity metrics (LOC, cyclomatic complexity)
    5. Identify code patterns and potential issues
    """
    
    def __init__(
        self,
        message_queue,
        agent_id: Optional[str] = None,
        priority: int = 5,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ObservationAgent.
        
        Args:
            message_queue: MessageBus instance for communication
            agent_id: Optional custom agent ID (auto-generated if not provided)
            priority: Agent priority (1-10, higher = more important)
            config: Agent-specific configuration
        """
        super().__init__(
            agent_id=agent_id or "observation-agent-1",
            agent_type="observation",
            priority=priority,
            message_queue=message_queue,
            config=config
        )
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """
        Declare agent capabilities.
        
        Returns:
            List of capabilities this agent supports
        """
        return [
            AgentCapability(
                name="code_analysis",
                version="1.0.0",
                confidence_threshold=0.8,
                description="Analyze Python code structure (functions, classes, imports)"
            ),
            AgentCapability(
                name="complexity_analysis",
                version="1.0.0",
                confidence_threshold=0.8,
                description="Calculate code complexity metrics"
            )
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """
        Determine if this agent can handle the given task.
        
        Args:
            task: Task to evaluate
        
        Returns:
            Tuple of (can_handle: bool, confidence: float)
        """
        # Check if task type matches our capabilities
        if task.task_type in ["code_analysis", "complexity_analysis"]:
            # Check if we have the required code payload
            if "code" in task.payload:
                code = task.payload["code"]
                
                # Quick validation - can we parse this as Python?
                try:
                    ast.parse(code)
                    return True, 0.9  # High confidence for valid Python code
                except SyntaxError:
                    logger.warning(f"Cannot parse code in task {task.task_id}: Invalid Python syntax")
                    return False, 0.0
            else:
                logger.warning(f"Task {task.task_id} missing 'code' in payload")
                return False, 0.0
        
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        Execute code analysis task.
        
        Args:
            task: Task to execute
        
        Returns:
            TaskResult with analysis results
        """
        try:
            code = task.payload.get("code", "")
            file_path = task.payload.get("file_path", "unknown")
            
            logger.info(f"Analyzing code from {file_path} (task {task.task_id})")
            
            # Parse code into AST
            tree = ast.parse(code, filename=file_path)
            
            # Extract information
            functions = self._extract_functions(tree, code)
            classes = self._extract_classes(tree, code)
            imports = self._extract_imports(tree)
            complexity = self._calculate_complexity(tree, code)
            
            # Calculate overall confidence based on analysis completeness
            confidence = self._calculate_confidence(functions, classes, imports, complexity)
            
            result = {
                "file_path": file_path,
                "functions": [self._function_to_dict(f) for f in functions],
                "classes": [self._class_to_dict(c) for c in classes],
                "imports": [self._import_to_dict(i) for i in imports],
                "complexity": complexity,
                "summary": {
                    "total_functions": len(functions),
                    "total_classes": len(classes),
                    "total_imports": len(imports),
                    "lines_of_code": complexity["loc"],
                    "average_complexity": complexity["average_complexity"]
                }
            }
            
            logger.info(
                f"Analysis complete for {file_path}: "
                f"{len(functions)} functions, {len(classes)} classes, "
                f"{complexity['loc']} LOC"
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=confidence
            )
        
        except SyntaxError as e:
            logger.error(f"Syntax error in task {task.task_id}: {e}")
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"Invalid Python syntax: {str(e)}",
                confidence=0.0
            )
        
        except Exception as e:
            logger.error(f"Error analyzing code in task {task.task_id}: {e}")
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"Analysis failed: {str(e)}",
                confidence=0.0
            )
    
    def _extract_functions(self, tree: ast.AST, code: str) -> List[FunctionInfo]:
        """Extract all functions from the AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Extract function parameters
                params = [arg.arg for arg in node.args.args]
                
                # Extract return type annotation if present
                return_type = None
                if node.returns:
                    return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                # Extract decorators
                decorators = [ast.unparse(dec) if hasattr(ast, 'unparse') else dec.id 
                             for dec in node.decorator_list]
                
                # Calculate cyclomatic complexity for this function
                visitor = ComplexityVisitor()
                visitor.visit(node)
                
                functions.append(FunctionInfo(
                    name=node.name,
                    parameters=params,
                    return_type=return_type,
                    line_number=node.lineno,
                    end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    docstring=docstring,
                    decorators=decorators,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    complexity=visitor.complexity
                ))
        
        return functions
    
    def _extract_classes(self, tree: ast.AST, code: str) -> List[ClassInfo]:
        """Extract all classes from the AST."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract base classes
                base_classes = []
                for base in node.bases:
                    if hasattr(ast, 'unparse'):
                        base_classes.append(ast.unparse(base))
                    elif isinstance(base, ast.Name):
                        base_classes.append(base.id)
                
                # Extract methods
                methods = [
                    n.name for n in node.body 
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                # Extract decorators
                decorators = [ast.unparse(dec) if hasattr(ast, 'unparse') else dec.id 
                             for dec in node.decorator_list]
                
                classes.append(ClassInfo(
                    name=node.name,
                    base_classes=base_classes,
                    methods=methods,
                    line_number=node.lineno,
                    end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    docstring=docstring,
                    decorators=decorators
                ))
        
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract all imports from the AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],  # Empty for 'import module'
                        alias=alias.asname,
                        line_number=node.lineno
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    line_number=node.lineno
                ))
        
        return imports
    
    def _calculate_complexity(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Calculate various complexity metrics."""
        # Lines of Code (LOC)
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Total cyclomatic complexity
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        total_complexity = visitor.complexity
        
        # Count functions for average complexity
        function_count = sum(1 for node in ast.walk(tree) 
                           if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        average_complexity = total_complexity / max(function_count, 1)
        
        return {
            "loc": loc,
            "total_lines": len(lines),
            "cyclomatic_complexity": total_complexity,
            "average_complexity": round(average_complexity, 2),
            "function_count": function_count
        }
    
    def _calculate_confidence(
        self,
        functions: List[FunctionInfo],
        classes: List[ClassInfo],
        imports: List[ImportInfo],
        complexity: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score based on analysis completeness.
        
        Higher confidence when:
        - We successfully extracted functions/classes
        - Code has reasonable complexity (not too simple/complex)
        - We have docstrings and type hints
        """
        confidence = 0.5  # Base confidence
        
        # Bonus for finding functions
        if functions:
            confidence += 0.15
            # Bonus for functions with docstrings
            documented = sum(1 for f in functions if f.docstring)
            if documented / len(functions) > 0.5:
                confidence += 0.1
        
        # Bonus for finding classes
        if classes:
            confidence += 0.1
        
        # Bonus for reasonable complexity (not too simple, not too complex)
        avg_complexity = complexity["average_complexity"]
        if 2 <= avg_complexity <= 10:
            confidence += 0.1
        
        # Bonus for imports (indicates real code, not just examples)
        if imports:
            confidence += 0.05
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        """Convert FunctionInfo to dictionary."""
        return {
            "name": func.name,
            "parameters": func.parameters,
            "return_type": func.return_type,
            "line_number": func.line_number,
            "end_line_number": func.end_line_number,
            "docstring": func.docstring,
            "decorators": func.decorators,
            "is_async": func.is_async,
            "complexity": func.complexity
        }
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        """Convert ClassInfo to dictionary."""
        return {
            "name": cls.name,
            "base_classes": cls.base_classes,
            "methods": cls.methods,
            "line_number": cls.line_number,
            "end_line_number": cls.end_line_number,
            "docstring": cls.docstring,
            "decorators": cls.decorators
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        """Convert ImportInfo to dictionary."""
        return {
            "module": imp.module,
            "names": imp.names,
            "alias": imp.alias,
            "line_number": imp.line_number
        }
