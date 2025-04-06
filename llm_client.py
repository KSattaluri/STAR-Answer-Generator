"""
LLM Client Module

This module provides a unified client for interacting with multiple LLM providers
(Gemini and Claude), including fallback mechanisms and retry logic.
"""

import os
import time
import json
import random
from typing import Dict, List, Optional, Union, Any

# Import LLM-specific libraries
import google.generativeai as genai
from anthropic import Anthropic

# Import project modules
from logger_setup import logger, setup_logging

class LLMClient:
    """
    A unified client for interacting with multiple LLM providers.
    Supports Gemini and Claude with fallback mechanisms and retry logic.
    """
    
    def __init__(self, config):
        """
        Initialize the LLM client with configuration.
        
        Args:
            config (dict): Configuration dictionary containing LLM settings
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        
        # Get primary and fallback provider settings
        self.primary_provider = self.llm_config.get('primary_provider', 'gemini')
        self.fallback_provider = self.llm_config.get('fallback_provider')
        
        # Get retry settings
        self.max_retries = self.llm_config.get('max_retries', 3)
        self.retry_delay = self.llm_config.get('retry_delay_seconds', 2)
        self.request_timeout = self.llm_config.get('request_timeout_seconds', 120)
        
        # Initialize provider-specific clients
        self._initialize_clients()
        
        print(f"LLM Client initialized with primary provider: {self.primary_provider}")
        if self.fallback_provider:
            print(f"Fallback provider configured: {self.fallback_provider}")
    
    def _initialize_clients(self):
        """Initialize provider-specific clients based on configuration."""
        # Initialize Gemini client if configured
        gemini_config = self.llm_config.get('gemini', {})
        self.gemini_api_key = gemini_config.get('api_key')
        self.gemini_model = gemini_config.get('model', 'gemini-2.5-pro-exp-03-25')
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                print(f"Gemini client initialized with model: {self.gemini_model}")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                if self.primary_provider == 'gemini':
                    print("Primary provider initialization failed!")
        else:
            print("Gemini API key not provided. Gemini client not initialized.")
        
        # Initialize Claude client if configured
        anthropic_config = self.llm_config.get('anthropic', {})
        self.anthropic_api_key = anthropic_config.get('api_key')
        self.anthropic_model = anthropic_config.get('model', 'claude-3-7-sonnet-20250219')
        
        if self.anthropic_api_key:
            try:
                self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                print(f"Claude client initialized with model: {self.anthropic_model}")
            except Exception as e:
                print(f"Failed to initialize Claude client: {e}")
                if self.primary_provider == 'anthropic':
                    print("Primary provider initialization failed!")
        else:
            print("Claude API key not provided. Claude client not initialized.")
    
    def generate_response(self, prompt, max_tokens=None, temperature=0.7, system_prompt=None, json_mode=False):
        """
        Generate a response using the primary LLM, falling back to the secondary LLM if needed.
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int, optional): Maximum number of tokens in the response
            temperature (float, optional): Sampling temperature (0.0 to 1.0)
            system_prompt (str, optional): System prompt for models that support it
            json_mode (bool, optional): Whether to request JSON output
            
        Returns:
            dict: A dictionary containing:
                - 'text': The generated text response
                - 'provider': The provider that generated the response
                - 'model': The model used to generate the response
                - 'tokens': Approximate token count (if available)
        """
        # Try with primary provider
        response = self._generate_with_provider(
            self.primary_provider, 
            prompt, 
            max_tokens, 
            temperature, 
            system_prompt,
            json_mode
        )
        
        # If primary provider failed and fallback is configured, try fallback
        if response is None and self.fallback_provider:
            logger.warning(f"Primary provider {self.primary_provider} failed. Trying fallback provider {self.fallback_provider}")
            response = self._generate_with_provider(
                self.fallback_provider, 
                prompt, 
                max_tokens, 
                temperature, 
                system_prompt,
                json_mode
            )
        
        return response
    
    def _generate_with_provider(self, provider, prompt, max_tokens, temperature, system_prompt, json_mode):
        """
        Generate a response using a specific provider with retry logic.
        
        Args:
            provider (str): The provider to use ('gemini' or 'anthropic')
            prompt (str): The prompt to send to the LLM
            max_tokens (int, optional): Maximum number of tokens in the response
            temperature (float, optional): Sampling temperature (0.0 to 1.0)
            system_prompt (str, optional): System prompt for models that support it
            json_mode (bool, optional): Whether to request JSON output
            
        Returns:
            dict or None: Response dictionary or None if all attempts failed
        """
        if provider not in ['gemini', 'anthropic']:
            logger.error(f"Unknown provider: {provider}")
            return None
        
        # Check if the provider is properly initialized
        if provider == 'gemini' and not self.gemini_api_key:
            logger.error("Gemini API key not configured")
            return None
        
        if provider == 'anthropic' and not self.anthropic_api_key:
            logger.error("Claude API key not configured")
            return None
        
        # Implement retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                if provider == 'gemini':
                    return self._generate_with_gemini(prompt, max_tokens, temperature, system_prompt, json_mode)
                else:  # anthropic
                    return self._generate_with_claude(prompt, max_tokens, temperature, system_prompt, json_mode)
            
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{self.max_retries} with {provider} failed: {str(e)}")
                
                # If this is the last attempt, re-raise the exception
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries} attempts with {provider} failed")
                    return None
                
                # Otherwise, wait before retrying with exponential backoff
                retry_delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                jitter = random.uniform(0, 0.1 * retry_delay)  # Add jitter (0-10%)
                wait_time = retry_delay + jitter
                
                logger.info(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
    
    def _generate_with_gemini(self, prompt, max_tokens, temperature, system_prompt, json_mode):
        """
        Generate a response using the Gemini API.
        
        Args:
            prompt (str): The prompt to send to Gemini
            max_tokens (int, optional): Maximum number of tokens in the response
            temperature (float, optional): Sampling temperature (0.0 to 1.0)
            system_prompt (str, optional): System prompt for Gemini
            json_mode (bool, optional): Whether to request JSON output
            
        Returns:
            dict: Response dictionary
        """
        logger.debug(f"Generating response with Gemini (model: {self.gemini_model})")
        
        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Configure safety settings (default moderate)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Initialize model
        model = genai.GenerativeModel(
            model_name=self.gemini_model,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Prepare content parts
        content_parts = []
        
        # Add system prompt if provided
        if system_prompt:
            content_parts.append({"role": "system", "parts": [system_prompt]})
        
        # Add user prompt
        content_parts.append({"role": "user", "parts": [prompt]})
        
        # Generate response
        response = model.generate_content(content_parts)
        
        # Extract text from response
        text = response.text
        
        # Parse JSON if requested and response looks like JSON
        if json_mode and text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                # Try to parse as JSON to validate
                json.loads(text)
            except json.JSONDecodeError as e:
                logger.warning(f"Requested JSON output but received invalid JSON: {e}")
        
        # Construct result dictionary
        result = {
            'text': text,
            'provider': 'gemini',
            'model': self.gemini_model,
            'tokens': None  # Gemini doesn't provide token count directly
        }
        
        return result
    
    def _generate_with_claude(self, prompt, max_tokens, temperature, system_prompt, json_mode):
        """
        Generate a response using the Claude API.
        
        Args:
            prompt (str): The prompt to send to Claude
            max_tokens (int, optional): Maximum number of tokens in the response
            temperature (float, optional): Sampling temperature (0.0 to 1.0)
            system_prompt (str, optional): System prompt for Claude
            json_mode (bool, optional): Whether to request JSON output
            
        Returns:
            dict: Response dictionary
        """
        logger.debug(f"Generating response with Claude (model: {self.anthropic_model})")
        
        # Prepare request parameters
        params = {
            "model": self.anthropic_model,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt
        
        # Request JSON response if specified
        if json_mode:
            # Claude doesn't have a direct JSON mode, but we can add to the system prompt
            json_instruction = "Return your response as a valid JSON object."
            if system_prompt:
                params["system"] = f"{system_prompt}\n\n{json_instruction}"
            else:
                params["system"] = json_instruction
        
        # Generate response
        response = self.anthropic_client.messages.create(**params)
        
        # Extract text from response
        text = response.content[0].text
        
        # Parse JSON if requested and response looks like JSON
        if json_mode and text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                # Try to parse as JSON to validate
                json.loads(text)
            except json.JSONDecodeError as e:
                logger.warning(f"Requested JSON output but received invalid JSON: {e}")
        
        # Construct result dictionary
        result = {
            'text': text,
            'provider': 'anthropic',
            'model': self.anthropic_model,
            'tokens': {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'total': response.usage.input_tokens + response.usage.output_tokens
            }
        }
        
        return result

if __name__ == '__main__':
    # Set up logging
    setup_logging(log_level="DEBUG")
    
    # Example configuration
    example_config = {
        'llm': {
            'primary_provider': 'gemini',
            'fallback_provider': 'anthropic',
            'max_retries': 3,
            'retry_delay_seconds': 2,
            'request_timeout_seconds': 120,
            'gemini': {
                'api_key': os.getenv('GEMINI_API_KEY'),
                'model': 'gemini-2.5-pro-exp-03-25'
            },
            'anthropic': {
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'model': 'claude-3-7-sonnet-20250219'
            }
        }
    }
    
    # Initialize client
    client = LLMClient(example_config)
    
    # Test prompt
    test_prompt = "Write a short paragraph about artificial intelligence."
    
    # Generate response
    response = client.generate_response(
        prompt=test_prompt,
        max_tokens=100,
        temperature=0.7,
        system_prompt="You are a helpful AI assistant."
    )
    
    if response:
        logger.info(f"Response from {response['provider']} ({response['model']}):")
        logger.info(response['text'])
        if response.get('tokens'):
            logger.info(f"Tokens used: {response['tokens']}")
    else:
        logger.error("Failed to generate response from any provider.")
