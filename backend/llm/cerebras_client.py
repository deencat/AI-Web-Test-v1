"""
Cerebras LLM Client - Fast, free inference for web element analysis

Cerebras provides ultra-fast inference with Llama models.
Free tier: https://cerebras.ai/

Models available:
- llama3.1-8b (fast, good for simple analysis)
- llama3.1-70b (slower, better reasoning)
"""

import os
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

# Try to import cerebras SDK, fallback to stub
try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False
    logger.warning("Cerebras SDK not installed. Using stub mode.")


class CerebrasClient:
    """
    Client for Cerebras inference API.
    
    Usage:
        client = CerebrasClient(api_key="your-key")
        result = await client.analyze_page_elements(
            html="<html>...</html>",
            basic_elements=[...],
            url="https://example.com/login"
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama3.1-8b",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        Initialize Cerebras client.
        
        Args:
            api_key: Cerebras API key (or set CEREBRAS_API_KEY env var)
            model: Model to use (llama3.1-8b or llama3.1-70b)
            temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if CEREBRAS_AVAILABLE and self.api_key:
            self.client = Cerebras(api_key=self.api_key)
            self.enabled = True
            logger.info(f"Cerebras client initialized with model: {model}")
        else:
            self.client = None
            self.enabled = False
            if not CEREBRAS_AVAILABLE:
                logger.warning("Cerebras SDK not available - install with: pip install cerebras-cloud-sdk")
            elif not self.api_key:
                logger.warning("Cerebras API key not provided - set CEREBRAS_API_KEY environment variable")
    
    async def analyze_page_elements(
        self,
        html: str,
        basic_elements: List[Dict],
        url: str,
        page_title: str = "",
        learned_patterns: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze page HTML to find interactive elements that Playwright might miss.
        
        Args:
            html: Page HTML content
            basic_elements: Elements already found by Playwright
            url: Page URL for context
            page_title: Page title
            learned_patterns: Previously learned patterns for similar pages
        
        Returns:
            Dict with enhanced_elements, suggested_selectors, semantic_info
        """
        if not self.enabled:
            return self._stub_analysis(basic_elements)
        
        try:
            # Build context-rich prompt
            prompt = self._build_analysis_prompt(
                html=html,
                basic_elements=basic_elements,
                url=url,
                page_title=page_title,
                learned_patterns=learned_patterns
            )
            
            # Call Cerebras API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web testing automation assistant. You analyze web pages to identify ALL interactive elements for test generation, including custom components, shadow DOM elements, and dynamic content that standard CSS selectors might miss."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(
                f"LLM analysis found {len(result.get('enhanced_elements', []))} additional elements "
                f"(tokens: {response.usage.total_tokens})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._stub_analysis(basic_elements)
    
    def _build_analysis_prompt(
        self,
        html: str,
        basic_elements: List[Dict],
        url: str,
        page_title: str,
        learned_patterns: Optional[List[Dict]]
    ) -> str:
        """Build prompt for LLM analysis."""
        
        # Truncate HTML if too long (keep under 4K tokens)
        html_snippet = html[:15000] if len(html) > 15000 else html
        
        prompt = f"""
Analyze this web page for test automation.

**Page Context:**
- URL: {url}
- Title: {page_title}
- Purpose: Identify ALL interactive elements for generating Playwright tests

**Elements Already Found (by CSS selectors):**
{json.dumps(basic_elements, indent=2)}

**HTML Snippet:**
```html
{html_snippet}
```
"""
        
        if learned_patterns:
            prompt += f"""

**Previously Learned Patterns (from similar pages):**
{json.dumps(learned_patterns[:5], indent=2)}

Use these as examples to identify similar patterns in this page.
"""
        
        prompt += """

**Your Task:**
Identify interactive elements that CSS selectors might miss:

1. **Custom Components**: Elements with role="button", role="link", onclick handlers
2. **Shadow DOM**: Elements inside custom web components
3. **Dynamic Content**: Elements loaded by JavaScript (check for data-* attributes)
4. **Visual-only Buttons**: Images, divs, spans that look/act like buttons
5. **Semantic Context**: What is each element's purpose? (login, search, submit, navigation)

**Output Format (JSON):**
{
  "enhanced_elements": [
    {
      "type": "button|input|link|form|custom",
      "selector": "CSS selector or XPath",
      "text": "visible text",
      "semantic_purpose": "login|search|navigation|submit|etc",
      "attributes": {"role": "button", "data-testid": "login-btn"},
      "confidence": 0.0-1.0,
      "why_important": "explanation"
    }
  ],
  "suggested_selectors": {
    "login_button": "[data-testid='login'], .login-btn, button:has-text('Login')",
    "search_form": "#search-form, [role='search']"
  },
  "page_patterns": {
    "page_type": "login|dashboard|form|e-commerce|etc",
    "framework": "react|vue|angular|custom",
    "complexity": "simple|medium|complex"
  },
  "missed_by_playwright": [
    {
      "element": "Sign out dropdown",
      "reason": "Hidden until hover, custom dropdown component",
      "selector": "[data-menu='user-dropdown'] > li:last-child"
    }
  ]
}

**Important:**
- Focus on elements users interact with (buttons, forms, links, inputs)
- Provide multiple selector options (CSS, XPath, text-based)
- Explain WHY each element is important for testing
- Higher confidence (0.8-1.0) for obvious elements, lower for uncertain ones
"""
        
        return prompt
    
    def _stub_analysis(self, basic_elements: List[Dict]) -> Dict[str, Any]:
        """
        Stub response when LLM is not available.
        Returns enhanced analysis with mock data.
        """
        return {
            "enhanced_elements": [
                {
                    "type": "button",
                    "selector": "[data-testid='submit']",
                    "text": "Submit",
                    "semantic_purpose": "form_submit",
                    "attributes": {"data-testid": "submit", "role": "button"},
                    "confidence": 0.7,
                    "why_important": "Primary form submission button"
                }
            ],
            "suggested_selectors": {
                "submit_button": "[data-testid='submit'], button:has-text('Submit')"
            },
            "page_patterns": {
                "page_type": "form",
                "framework": "unknown",
                "complexity": "medium"
            },
            "missed_by_playwright": [
                {
                    "element": "Custom dropdown",
                    "reason": "Hidden in shadow DOM",
                    "selector": "custom-dropdown::shadow button"
                }
            ],
            "_note": "STUB MODE - Cerebras API not configured. Set CEREBRAS_API_KEY environment variable."
        }
    
    async def suggest_test_scenarios(
        self,
        elements: List[Dict],
        page_type: str
    ) -> List[str]:
        """
        Suggest test scenarios based on observed elements.
        
        This helps RequirementsAgent generate better test requirements.
        """
        if not self.enabled:
            return [
                "Test that all buttons are clickable",
                "Test that all forms can be submitted",
                "Test navigation links lead to correct pages"
            ]
        
        try:
            prompt = f"""
Given these interactive elements on a {page_type} page:

{json.dumps(elements, indent=2)}

Suggest 5-10 important test scenarios in Given/When/Then format.

Output JSON:
{{
  "test_scenarios": [
    {{
      "given": "User is on the login page",
      "when": "User enters valid credentials and clicks submit",
      "then": "User should be redirected to dashboard",
      "priority": "critical|high|medium|low",
      "risk_level": 0.0-1.0
    }}
  ]
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test automation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("test_scenarios", [])
            
        except Exception as e:
            logger.error(f"Error suggesting test scenarios: {e}")
            return []


# Singleton instance
_cerebras_client: Optional[CerebrasClient] = None


def get_cerebras_client() -> CerebrasClient:
    """Get or create singleton Cerebras client."""
    global _cerebras_client
    if _cerebras_client is None:
        _cerebras_client = CerebrasClient()
    return _cerebras_client
