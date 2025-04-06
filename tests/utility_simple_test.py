"""
Simple Test Script

This script tests the basic functionality of the system without relying on complex modules.
"""

import os
import json
from pathlib import Path
import time

def main():
    print("=" * 80)
    print("SIMPLE TEST SCRIPT")
    print("=" * 80)
    
    # Test environment setup
    print("\nEnvironment Setup:")
    
    # Check if .env file exists
    if os.path.exists(".env"):
        print("  ✓ .env file exists")
    else:
        print("  ✗ .env file is missing")
    
    # Check if config.yaml exists
    if os.path.exists("config.yaml"):
        print("  ✓ config.yaml exists")
    else:
        print("  ✗ config.yaml is missing")
    
    # Check if prompt templates exist
    prompt_templates_dir = "prompt_templates"
    if os.path.exists(prompt_templates_dir):
        print(f"  ✓ {prompt_templates_dir} directory exists")
        
        # Check stage1 prompt
        stage1_path = os.path.join(prompt_templates_dir, "stage1_subprompt_generator.md")
        if os.path.exists(stage1_path):
            print(f"  ✓ {stage1_path} exists")
        else:
            print(f"  ✗ {stage1_path} is missing")
        
        # Check stage2 prompt
        stage2_path = os.path.join(prompt_templates_dir, "stage2_star_answer_generator.md")
        if os.path.exists(stage2_path):
            print(f"  ✓ {stage2_path} exists")
        else:
            print(f"  ✗ {stage2_path} is missing")
        
        # Check role_skills directory
        role_skills_dir = os.path.join(prompt_templates_dir, "role_skills")
        if os.path.exists(role_skills_dir):
            print(f"  ✓ {role_skills_dir} directory exists")
            
            # Count skills files
            skills_files = [f for f in os.listdir(role_skills_dir) if f.endswith(".md")]
            print(f"    Found {len(skills_files)} skills files")
        else:
            print(f"  ✗ {role_skills_dir} directory is missing")
    else:
        print(f"  ✗ {prompt_templates_dir} directory is missing")
    
    # Test loading a prompt template
    print("\nTesting prompt_processor.py:")
    try:
        from prompt_processor import load_prompt_template
        
        stage1_path = os.path.join("prompt_templates", "stage1_subprompt_generator.md")
        template = load_prompt_template(stage1_path)
        
        if template:
            print(f"  ✓ Successfully loaded template from {stage1_path}")
            print(f"    Template length: {len(template)} characters")
        else:
            print(f"  ✗ Failed to load template from {stage1_path}")
    except Exception as e:
        print(f"  ✗ Error testing prompt_processor.py: {e}")
    
    # Test loading configuration
    print("\nTesting config.py:")
    try:
        from config import load_config
        
        config = load_config("config.yaml")
        
        if config:
            print("  ✓ Successfully loaded configuration")
            
            # Check key sections
            if 'prompts' in config:
                print("  ✓ Configuration contains 'prompts' section")
            else:
                print("  ✗ Configuration missing 'prompts' section")
                
            if 'llm' in config:
                print("  ✓ Configuration contains 'llm' section")
            else:
                print("  ✗ Configuration missing 'llm' section")
                
            if 'target_roles' in config:
                print(f"  ✓ Configuration contains {len(config['target_roles'])} target roles")
            else:
                print("  ✗ Configuration missing 'target_roles' section")
        else:
            print("  ✗ Failed to load configuration")
    except Exception as e:
        print(f"  ✗ Error testing config.py: {e}")
    
    # Test LLM client initialization
    print("\nTesting llm_client.py:")
    try:
        from llm_client import LLMClient
        
        # Only import config if not already imported
        if 'config' not in locals():
            from config import load_config
            config = load_config("config.yaml")
        
        if config:
            llm_client = LLMClient(config)
            print("  ✓ Successfully initialized LLM client")
        else:
            print("  ✗ Failed to initialize LLM client (config not loaded)")
    except Exception as e:
        print(f"  ✗ Error testing llm_client.py: {e}")
    
    # Test state manager initialization
    print("\nTesting state_manager.py:")
    try:
        from state_manager import StateManager
        
        test_db_path = os.path.join("generated_answers", "test_state.db")
        os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
        
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        state_manager = StateManager(test_db_path)
        print(f"  ✓ Successfully initialized state manager with database at {test_db_path}")
        
        # Test adding a file
        state_manager.add_file("test_file_1", "sub_prompt")
        print("  ✓ Successfully added a file to the state manager")
        
        # Test getting status
        status = state_manager.get_file_status("test_file_1")
        print(f"  ✓ Successfully retrieved file status: {status}")
        
        # Clean up
        state_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("  ✓ Successfully cleaned up test database")
    except Exception as e:
        print(f"  ✗ Error testing state_manager.py: {e}")
    
    print("\nTest completed.")
    print("=" * 80)

if __name__ == "__main__":
    main()
