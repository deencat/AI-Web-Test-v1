"""Test generation service using OpenRouter LLM."""
from typing import List, Dict, Optional
from app.services.openrouter import OpenRouterService


class TestGenerationService:
    """Service for generating test cases using LLM."""
    
    def __init__(self):
        self.openrouter = OpenRouterService()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for test generation."""
        return """You are an expert test case generator for web applications.

Your task is to generate comprehensive, well-structured test cases based on user requirements.

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
        "Step 2: Next action",
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

IMPORTANT: Return ONLY valid JSON, no additional text or explanation."""

    def _build_user_prompt(
        self,
        requirement: str,
        test_type: Optional[str] = None,
        num_tests: int = 3
    ) -> str:
        """
        Build the user prompt for test generation.
        
        Args:
            requirement: The feature or requirement to test
            test_type: Type of tests to generate (e2e, unit, integration, api)
            num_tests: Number of test cases to generate
        """
        prompt = f"Generate {num_tests} test case(s) for the following requirement:\n\n{requirement}"
        
        if test_type:
            prompt += f"\n\nTest Type: {test_type}"
        
        prompt += "\n\nGenerate comprehensive test cases covering positive scenarios, negative scenarios, and edge cases where applicable."
        
        return prompt
    
    async def generate_tests(
        self,
        requirement: str,
        test_type: Optional[str] = None,
        num_tests: int = 3,
        model: Optional[str] = None
    ) -> Dict:
        """
        Generate test cases based on a requirement.
        
        Args:
            requirement: The feature or requirement to test
            test_type: Type of tests (e2e, unit, integration, api)
            num_tests: Number of test cases to generate (default: 3)
            model: Optional model override
            
        Returns:
            Dict with generated test cases and metadata
            
        Raises:
            Exception: If generation fails
        """
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(requirement, test_type, num_tests)}
        ]
        
        # Call OpenRouter
        try:
            response = await self.openrouter.chat_completion(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=2000
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
                "tokens": response.get("usage", {}).get("total_tokens", 0)
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Test generation failed: {str(e)}")
    
    async def generate_tests_for_page(
        self,
        page_name: str,
        page_description: str,
        num_tests: int = 5,
        model: Optional[str] = None
    ) -> Dict:
        """
        Generate E2E test cases for a specific page.
        
        Args:
            page_name: Name of the page (e.g., "Login Page")
            page_description: Description of page functionality
            num_tests: Number of test cases to generate
            model: Optional model override
            
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
            model=model
        )
    
    async def generate_api_tests(
        self,
        endpoint: str,
        method: str,
        description: str,
        num_tests: int = 4,
        model: Optional[str] = None
    ) -> Dict:
        """
        Generate API test cases for an endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/users")
            method: HTTP method (GET, POST, PUT, DELETE)
            description: What the endpoint does
            num_tests: Number of test cases to generate
            model: Optional model override
            
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
            model=model
        )

