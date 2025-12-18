"""Test generation service using Universal LLM (supports Google, Cerebras, OpenRouter)."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.services.universal_llm import UniversalLLMService
from app.services.kb_context import KBContextService


class TestGenerationService:
    """Service for generating test cases using LLM."""
    
    def __init__(self):
        self.llm = UniversalLLMService()
        self.kb_context = KBContextService()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for test generation."""
        return """You are an expert test case generator for web applications.

Your task is to generate comprehensive, well-structured test cases based on user requirements.

**IMPORTANT: When Knowledge Base (KB) context is provided:**
- Reference specific KB documents in test steps
- Use exact field names and UI paths from KB system guides  
- Include realistic test data from KB product catalogs
- Cite KB sources in test steps using format: "(per [Document Name])" or "(ref: [Document Name])"
- Validate test assertions against documented procedures in KB
- Prioritize information from KB documents over general knowledge

OUTPUT FORMAT:
Generate test cases in the following JSON format:
{
  "test_cases": [
    {
      "title": "Test case title",
      "description": "What this test verifies",
      "test_type": "e2e|unit|integration|api",
      "priority": "high|medium|low",
      "steps": [
        "Step 1: Action to take",
        "Step 2: Next action (per KB_Document.pdf)",
        "Step 3: Final action"
      ],
      "expected_result": "What should happen",
      "preconditions": "Any setup required (optional)",
      "test_data": {
        "key": "value"
      }
    }
  ]
}

GUIDELINES:
- Be specific and actionable
- Include realistic test data
- Cover both positive and negative scenarios
- Prioritize critical functionality as "high"
- Use clear, concise language
- Each test should be independent and repeatable
- Include edge cases when relevant
- When KB context is available, cite the source document for domain-specific steps

IMPORTANT: Return ONLY valid JSON, no additional text or explanation."""

    def _build_user_prompt(
        self,
        requirement: str,
        test_type: Optional[str] = None,
        num_tests: int = 3,
        kb_context: str = ""
    ) -> str:
        """
        Build the user prompt for test generation.
        
        Args:
            requirement: The feature or requirement to test
            test_type: Type of tests to generate (e2e, unit, integration, api)
            num_tests: Number of test cases to generate
            kb_context: Knowledge Base context (formatted string from KBContextService)
        """
        prompt = f"Generate {num_tests} test case(s) for the following requirement:\n\n{requirement}"
        
        if test_type:
            prompt += f"\n\nTest Type: {test_type}"
        
        # Add KB context if provided
        if kb_context:
            prompt += f"\n\n{kb_context}"
            prompt += "\n\n**IMPORTANT: Use the Knowledge Base documents above to:**"
            prompt += "\n- Include exact UI paths, field names, and system terminology"
            prompt += "\n- Use realistic test data from the documented examples"
            prompt += "\n- Cite KB sources when referencing documented procedures"
            prompt += "\n- Ensure test steps match documented workflows"
        
        prompt += "\n\nGenerate comprehensive test cases covering positive scenarios, negative scenarios, and edge cases where applicable."
        
        return prompt
    
    async def generate_tests(
        self,
        requirement: str,
        test_type: Optional[str] = None,
        num_tests: int = 3,
        model: Optional[str] = None,
        category_id: Optional[int] = None,
        db: Optional[Session] = None,
        use_kb_context: bool = True,
        max_kb_docs: int = 10,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Generate test cases based on a requirement.
        
        Args:
            requirement: The feature or requirement to test
            test_type: Type of tests (e2e, unit, integration, api)
            num_tests: Number of test cases to generate (default: 3)
            model: Optional model override
            category_id: Optional KB category ID for context
            db: Optional database session for KB context retrieval
            use_kb_context: Whether to use KB context if available
            max_kb_docs: Maximum number of KB documents to include
            user_id: Optional user ID to load generation settings from
            
        Returns:
            Dict with generated test cases and metadata
            
        Raises:
            Exception: If generation fails
        """
        # Load user's generation settings if user_id provided
        user_config = None
        if db and user_id:
            try:
                from app.services.user_settings_service import user_settings_service
                user_config = user_settings_service.get_provider_config(
                    db=db,
                    user_id=user_id,
                    config_type="generation"
                )
                if user_config:
                    print(f"[DEBUG] 🎯 Loaded user generation config: provider={user_config.get('provider')}, model={user_config.get('model')}")
            except Exception as e:
                print(f"[DEBUG] ⚠️ Could not load user generation settings: {str(e)}")
                user_config = None
        
        # Retrieve KB context if requested
        kb_context = ""
        kb_docs_used = 0
        
        if db and use_kb_context:
            try:
                kb_context = await self.kb_context.get_category_context(
                    db=db,
                    category_id=category_id,  # None = all categories
                    max_docs=max_kb_docs
                )
                if kb_context:
                    # Count documents in context
                    kb_docs_used = kb_context.count("[Document ")
            except Exception as e:
                # Log error but continue without KB context
                print(f"Warning: Could not retrieve KB context: {str(e)}")
                kb_context = ""
        
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(requirement, test_type, num_tests, kb_context)}
        ]
        
        # Determine provider/model/temperature/max_tokens from user config or defaults
        if user_config:
            # Use user's generation settings
            provider = user_config.get("provider", "openrouter")
            generation_model = user_config.get("model") if not model else model  # Explicit model param takes precedence
            temperature = user_config.get("temperature", 0.7)
            max_tokens_val = user_config.get("max_tokens", 2000)
            print(f"[DEBUG] 🎯 Using user's generation config: {provider}/{generation_model} (temp={temperature}, max_tokens={max_tokens_val})")
        else:
            # Fall back to .env defaults
            provider = "openrouter"
            generation_model = model  # Use explicit model param or None (will use settings default)
            temperature = 0.7
            max_tokens_val = 2000
            print(f"[DEBUG] 📋 Using .env defaults: {provider} (temp={temperature}, max_tokens={max_tokens_val})")
        
        # Call Universal LLM service (supports Google, Cerebras, OpenRouter)
        try:
            response = await self.llm.chat_completion(
                messages=messages,
                provider=provider,
                model=generation_model,
                temperature=temperature,
                max_tokens=max_tokens_val
            )
            
            # Extract content
            if "choices" not in response or len(response["choices"]) == 0:
                raise Exception("No response from LLM")
            
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            import json
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # If JSON parsing fails, return raw content for debugging
                raise Exception(f"Failed to parse LLM response as JSON: {str(e)}\n\nRaw response:\n{content[:500]}")
            
            # Validate structure
            if "test_cases" not in result:
                raise Exception("Response missing 'test_cases' field")
            
            # Add metadata
            result["metadata"] = {
                "requirement": requirement,
                "test_type": test_type,
                "num_requested": num_tests,
                "num_generated": len(result.get("test_cases", [])),
                "model": response.get("model", "unknown"),
                "tokens": response.get("usage", {}).get("total_tokens", 0),
                "kb_context_used": bool(kb_context),
                "kb_category_id": category_id,
                "kb_documents_used": kb_docs_used
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Test generation failed: {str(e)}")
    
    async def generate_tests_for_page(
        self,
        page_name: str,
        page_description: str,
        num_tests: int = 5,
        model: Optional[str] = None,
        category_id: Optional[int] = None,
        db: Optional[Session] = None,
        use_kb_context: bool = True,
        max_kb_docs: int = 10,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Generate E2E test cases for a specific page.
        
        Args:
            page_name: Name of the page (e.g., "Login Page")
            page_description: Description of page functionality
            num_tests: Number of test cases to generate
            model: Optional model override
            category_id: Optional KB category ID for context
            db: Optional database session for KB context
            use_kb_context: Whether to use KB context if available
            max_kb_docs: Maximum number of KB documents to include
            user_id: Optional user ID to load generation settings from
            
        Returns:
            Dict with generated test cases
        """
        requirement = f"""
Page: {page_name}

Description:
{page_description}

Generate comprehensive E2E test cases for this page including:
- Happy path scenarios
- Validation errors
- Edge cases
- User interactions
"""
        
        return await self.generate_tests(
            requirement=requirement,
            test_type="e2e",
            num_tests=num_tests,
            model=model,
            category_id=category_id,
            db=db,
            use_kb_context=use_kb_context,
            max_kb_docs=max_kb_docs,
            user_id=user_id
        )
    
    async def generate_api_tests(
        self,
        endpoint: str,
        method: str,
        description: str,
        num_tests: int = 4,
        model: Optional[str] = None,
        category_id: Optional[int] = None,
        db: Optional[Session] = None,
        use_kb_context: bool = True,
        max_kb_docs: int = 10,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Generate API test cases for an endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/users")
            method: HTTP method (GET, POST, PUT, DELETE)
            description: What the endpoint does
            num_tests: Number of test cases to generate
            model: Optional model override
            category_id: Optional KB category ID for context
            db: Optional database session for KB context
            use_kb_context: Whether to use KB context if available
            max_kb_docs: Maximum number of KB documents to include
            user_id: Optional user ID to load generation settings from
            
        Returns:
            Dict with generated test cases
        """
        requirement = f"""
API Endpoint: {method} {endpoint}

Description:
{description}

Generate API test cases including:
- Valid requests with expected responses
- Invalid requests (bad data, missing fields)
- Authentication/authorization scenarios
- Edge cases (empty data, large payloads)
"""
        
        return await self.generate_tests(
            requirement=requirement,
            test_type="api",
            num_tests=num_tests,
            model=model,
            category_id=category_id,
            db=db,
            use_kb_context=use_kb_context,
            max_kb_docs=max_kb_docs,
            user_id=user_id
        )

