"""
Test Script for Sub-Prompt Generation

This script tests the sub-prompt generation functionality with a single role/question/industry combination.
"""

import os
import json
import time
from pathlib import Path

from config import load_config
from state_manager import StateManager
from llm_client import LLMClient
from subprompt_generator import generate_subprompts

def main():
    """Main function."""
    print("=" * 80)
    print("TESTING SUB-PROMPT GENERATION")
    print("=" * 80)
    
    # Load configuration
    config = load_config('config.yaml')
    
    if not config:
        print("Failed to load configuration. Exiting.")
        exit(1)
    
    # Create a test directory
    test_dir = os.path.join('generated_answers', 'test')
    os.makedirs(test_dir, exist_ok=True)
    
    # Initialize state manager with a test database
    db_path = os.path.join(test_dir, 'test_state.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Create a test args object
    class TestArgs:
        def __init__(self):
            self.role = "Technical Delivery Manager"
            self.question = "Talk about a time when you went above and beyond"
            self.industry = None
            self.resume = False
    
    args = TestArgs()
    
    print(f"Testing with role: {args.role}")
    print(f"Testing with question: {args.question}")
    print("-" * 80)
    
    # Time the execution
    start_time = time.time()
    
    # Generate sub-prompts
    success = generate_subprompts(config, state_manager, llm_client, args)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    print("-" * 80)
    print(f"Execution time: {elapsed_time:.2f} seconds")
    print(f"Success: {success}")
    
    # Get summary
    summary = state_manager.get_summary(stage='sub_prompt')
    print(f"Summary: {summary}")
    
    # Display generated files
    subprompts_dir = os.path.join(
        config.get('output', {}).get('base_dir', 'generated_answers'),
        config.get('subprompts_dir', 'sub_prompts')
    )
    
    print("\nGenerated files:")
    for file in os.listdir(subprompts_dir):
        if file.endswith('.json'):
            file_path = os.path.join(subprompts_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size} bytes)")
            
            # Display the first sub-prompt from each file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data and len(data) > 0:
                        print(f"    First sub-prompt ID: {data[0].get('prompt_id', 'N/A')}")
                        print(f"    Number of sub-prompts: {len(data)}")
            except Exception as e:
                print(f"    Error reading file: {e}")
    
    # Clean up
    state_manager.close()
    print("=" * 80)

if __name__ == "__main__":
    main()
