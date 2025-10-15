"""
Claude API Client - Infrastructure Layer
Low-level Claude API integration with error handling and retries.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Low-level Claude API client for infrastructure layer."""
    
    def __init__(self):
        """Initialize Claude API client."""
        self.api_key = self._get_api_key()
        self.client = self._setup_client()
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            return None
        return api_key.strip()
    
    def _setup_client(self):
        """Setup Anthropic client with proper configuration."""
        if not self.api_key:
            return None
        
        try:
            import anthropic
            import httpx
            
            # Setup custom HTTP client with retries and proper headers
            custom_client = httpx.Client(
                timeout=60.0,
                verify=True,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Connection': 'keep-alive'
                },
                transport=httpx.HTTPTransport(retries=3)
            )
            
            return anthropic.Anthropic(
                api_key=self.api_key,
                timeout=60.0,
                max_retries=2,
                http_client=custom_client
            )
        except ImportError:
            logger.error("Anthropic library not installed")
            return None
    
    def is_available(self) -> bool:
        """Check if Claude API client is available."""
        return self.client is not None and self.api_key is not None
    
    def send_text_message(self, prompt: str, model: str = "claude-sonnet-4-20250514", 
                         max_tokens: int = 2000, temperature: float = 0.0) -> Optional[str]:
        """Send text message to Claude API."""
        if not self.is_available():
            logger.error("Claude API client not available")
            return None
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API text message failed: {e}")
            return None
    
    def send_document_message(self, pdf_path: str, prompt: str, 
                            model: str = "claude-sonnet-4-20250514") -> Optional[str]:
        """Send document (PDF) to Claude API with prompt."""
        if not self.is_available():
            logger.error("Claude API client not available")
            return None
        
        try:
            import base64
            
            # Convert PDF to base64
            with open(pdf_path, 'rb') as file:
                pdf_base64 = base64.b64encode(file.read()).decode('utf-8')
            
            response = self.client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API document message failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test Claude API connection."""
        if not self.is_available():
            return False
        
        try:
            response = self.send_text_message(
                prompt="Test connection - respond only 'OK'",
                max_tokens=10
            )
            return response and "OK" in response
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Claude models."""
        return [
            "claude-sonnet-4-20250514",      # Current working model
            "claude-3-5-sonnet-20250106",   # Latest Sonnet
            "claude-3-5-sonnet-20241022",   # Previous Sonnet
            "claude-3-5-haiku-20241022",    # Latest Haiku
            "claude-3-sonnet-20240229",     # Older Sonnet fallback
            "claude-3-haiku-20240307"       # Oldest fallback
        ]
    
    def send_message_with_fallback(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Send message with model fallback strategy."""
        models = self.get_available_models()
        
        for model in models:
            try:
                result = self.send_text_message(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.0
                )
                if result:
                    logger.info(f"Successfully used Claude model: {model}")
                    return result
            except Exception as e:
                if "not_found_error" in str(e):
                    logger.warning(f"Model {model} not found, trying next model")
                    continue
                else:
                    logger.error(f"Error with model {model}: {e}")
                    break
        
        logger.error("All Claude models failed")
        return None
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get client information and status."""
        return {
            "api_key_set": self.api_key is not None,
            "client_available": self.client is not None,
            "connection_test": self.test_connection() if self.is_available() else False,
            "available_models": self.get_available_models()
        }


# Global instance
claude_api_client = ClaudeAPIClient()