"""
Configuration Module

This module handles loading and validating configuration from YAML files and environment variables.
"""

import os
import yaml
from dotenv import load_dotenv
import logging

# Default configuration file path
DEFAULT_CONFIG_PATH = 'config.yaml'

def load_config(config_path=None):
    """
    Load configuration from a YAML file and environment variables.
    
    Args:
        config_path (str, optional): Path to the configuration YAML file.
            Defaults to DEFAULT_CONFIG_PATH.
    
    Returns:
        dict: The loaded configuration dictionary, or None if loading failed.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"Configuration loaded successfully from {config_path}")
        
        # Add API keys from environment variables
        gemini_api_key = os.getenv(config.get('gemini_api_key_env_var', 'GEMINI_API_KEY'))
        anthropic_api_key = os.getenv(config.get('claude_api_key_env_var', 'ANTHROPIC_API_KEY'))
        
        # Create nested structure if it doesn't exist
        if 'llm' not in config:
            config['llm'] = {}
        if 'gemini' not in config['llm']:
            config['llm']['gemini'] = {}
        if 'anthropic' not in config['llm']:
            config['llm']['anthropic'] = {}
            
        # Store API keys in config
        config['llm']['gemini']['api_key'] = gemini_api_key
        config['llm']['anthropic']['api_key'] = anthropic_api_key
        
        # Set model names
        config['llm']['gemini']['model'] = config.get('gemini_model', 'gemini-2.5-pro-exp-03-25')
        config['llm']['anthropic']['model'] = config.get('claude_model', 'claude-3-7-sonnet-20250219')
        
        # Set primary and fallback providers
        config['llm']['primary_provider'] = 'gemini'
        config['llm']['fallback_provider'] = 'anthropic' if config.get('use_secondary_fallback', True) else None
        
        # Set retry configuration
        config['llm']['max_retries'] = config.get('max_retries', 3)
        config['llm']['retry_delay_seconds'] = config.get('retry_initial_backoff_seconds', 2)
        config['llm']['request_timeout_seconds'] = config.get('request_timeout_seconds', 120)
        
        # Validate API keys
        if not config['llm']['gemini']['api_key']:
            print(f"Warning: {config.get('gemini_api_key_env_var', 'GEMINI_API_KEY')} not found in environment variables.")
        if not config['llm']['anthropic']['api_key']:
            print(f"Warning: {config.get('claude_api_key_env_var', 'ANTHROPIC_API_KEY')} not found in environment variables.")
            
        # Set up directories
        config['output'] = {
            'base_dir': config.get('output_base_dir', 'generated_answers'),
            'state_db': 'processing_state.db'
        }
        
        config['input'] = {
            'base_dir': config.get('input_base_dir', 'generated_answers'),
            'answer_format': 'md'
        }
        
        # Set up prompt paths
        config['prompts'] = {
            'meta_prompt': config.get('meta_prompt_path', 'prompt_templates/stage1_subprompt_generator.md'),
            'main_context': config.get('main_context_prompt_path', 'prompt_templates/stage2_star_answer_generator.md'),
            'conversation': config.get('conversation_prompt_path', 'prompt_templates/stage3_conversational_transformer.md')
        }
        
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file {config_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading configuration: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    config = load_config()
    if config:
        print("\nLoaded Configuration:")
        print(f"  Output Base Dir: {config.get('output', {}).get('base_dir')}")
        print(f"  Gemini Model: {config.get('llm', {}).get('gemini', {}).get('model')}")
        print(f"  Anthropic Model: {config.get('llm', {}).get('anthropic', {}).get('model')}")
        print(f"  Gemini API Key Loaded: {'Yes' if config.get('llm', {}).get('gemini', {}).get('api_key') else 'No'}")
        print(f"  Anthropic API Key Loaded: {'Yes' if config.get('llm', {}).get('anthropic', {}).get('api_key') else 'No'}")
