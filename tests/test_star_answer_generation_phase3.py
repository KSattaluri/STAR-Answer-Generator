"""
Test Script for Phase 3 (STAR Answer Generation)

This script tests the STAR answer generation functionality with minimal dependencies.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("\n" + "=" * 80)
    print("TESTING PHASE 3: STAR ANSWER GENERATION")
    print("=" * 80 + "\n")
    
    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    from config import load_config
    config = load_config('config.yaml')
    
    if not config:
        print("  ✗ Failed to load configuration. Exiting.")
        return
    
    print("  ✓ Configuration loaded successfully")
    
    # Step 2: Set up output directories
    print("\nStep 2: Setting up output directories...")
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(output_dir, config.get('subprompts_dir', 'sub_prompts'))
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    
    os.makedirs(answers_dir, exist_ok=True)
    print(f"  ✓ Created output directory: {answers_dir}")
    
    # Step 3: Initialize state manager
    print("\nStep 3: Initializing state manager...")
    from state_manager import StateManager, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_FAILED
    
    db_path = os.path.join(output_dir, 'test_processing_state.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  ✓ Removed existing test database: {db_path}")
    
    state_manager = StateManager(db_path)
    print(f"  ✓ Initialized state manager with database: {db_path}")
    
    # Step 4: Initialize LLM client
    print("\nStep 4: Initializing LLM client...")
    from llm_client import LLMClient
    llm_client = LLMClient(config)
    print("  ✓ Initialized LLM client")
    
    # Step 5: Load sub-prompts
    print("\nStep 5: Loading sub-prompts...")
    
    # Find all sub-prompt files
    subprompt_files = list(Path(subprompts_dir).glob("*.json"))
    
    if not subprompt_files:
        print("  ✗ No sub-prompt files found. Please run Phase 2 first.")
        return
    
    print(f"  ✓ Found {len(subprompt_files)} sub-prompt files")
    
    # Select the first sub-prompt file for testing
    subprompt_file = subprompt_files[0]
    print(f"  ✓ Using sub-prompt file: {subprompt_file}")
    
    # Load the sub-prompts
    from star_answer_generator import load_subprompts
    subprompts = load_subprompts(subprompt_file)
    
    if not subprompts:
        print("  ✗ Failed to load sub-prompts from file")
        return
    
    print(f"  ✓ Loaded {len(subprompts)} sub-prompts")
    
    # Step 6: Load the main context prompt template
    print("\nStep 6: Loading main context prompt template...")
    from prompt_processor import load_prompt_template
    
    template_path = config['prompts']['main_context']
    template = load_prompt_template(template_path)
    
    if not template:
        print(f"  ✗ Failed to load template from {template_path}")
        return
    
    print(f"  ✓ Loaded template from {template_path}")
    
    # Step 7: Extract role, question, and industry from the sub-prompt file name
    print("\nStep 7: Extracting metadata from file name...")
    
    # Parse the file name to extract role, question, and industry
    file_name = os.path.basename(subprompt_file)
    file_name_parts = file_name.replace('.json', '').split('_')
    
    # Reconstruct role name, question, and industry
    role_parts = []
    question_part = None
    industry_parts = []
    
    for part in file_name_parts:
        if part.startswith('q') and len(part) <= 3 and part[1:].isdigit():
            question_part = part
            break
        role_parts.append(part)
    
    if question_part:
        industry_parts = file_name_parts[file_name_parts.index(question_part) + 1:]
    
    role_name = ' '.join(role_parts).replace('_', ' ').title()
    industry = ' '.join(industry_parts).replace('_', ' ').title()
    
    # Get the question from the config based on the question number
    question_index = int(question_part[1:]) - 1 if question_part and question_part[1:].isdigit() else 0
    
    # Handle case where target_questions might not be in config
    target_questions = config.get('target_questions', [])
    if target_questions and question_index < len(target_questions):
        question = target_questions[question_index]
    else:
        # Default question if not found in config
        question = "Talk about a time when you went above and beyond your role to accomplish a goal."
    
    print(f"  ✓ Role: {role_name}")
    print(f"  ✓ Question: {question}")
    print(f"  ✓ Industry: {industry}")
    
    # Step 8: Generate a STAR answer for the first sub-prompt
    print("\nStep 8: Generating STAR answer...")
    print("  This may take a moment...")
    
    # Select the first sub-prompt for testing
    subprompt = subprompts[0]
    
    # Import the generate_star_answer function
    from star_answer_generator import generate_star_answer
    
    start_time = time.time()
    
    # Generate the STAR answer
    success, output_file = generate_star_answer(
        llm_client=llm_client,
        state_manager=state_manager,
        template_path=template_path,
        subprompt=subprompt,
        role_name=role_name,
        industry=industry,
        question=question,
        output_dir=answers_dir,
        config=config
    )
    
    elapsed_time = time.time() - start_time
    
    if success:
        print(f"  ✓ Successfully generated STAR answer in {elapsed_time:.2f} seconds")
        print(f"  ✓ Saved to: {output_file}")
        
        # Step 9: Display the generated STAR answer
        print("\nStep 9: Displaying generated STAR answer...")
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                answer_data = json.load(f)
            
            # Display metadata
            metadata = answer_data.get('metadata', {})
            print("\nMetadata:")
            print(f"  Role: {metadata.get('role', 'N/A')}")
            print(f"  Industry: {metadata.get('industry', 'N/A')}")
            print(f"  Question: {metadata.get('question', 'N/A')}")
            print(f"  Prompt ID: {metadata.get('prompt_id', 'N/A')}")
            print(f"  Skill focus: {metadata.get('skill_focus', 'N/A')}")
            print(f"  Soft skill highlight: {metadata.get('soft_skill_highlight', 'N/A')}")
            print(f"  Scenario theme: {metadata.get('scenario_theme_hint', 'N/A')}")
            print(f"  LLM provider: {metadata.get('llm_provider', 'N/A')}")
            
            # Display STAR sections
            answer = answer_data.get('answer', {})
            print("\nSTAR Answer:")
            print("\nSituation:")
            print(f"  {answer.get('situation', 'N/A')[:200]}...")
            print("\nTask:")
            print(f"  {answer.get('task', 'N/A')[:200]}...")
            print("\nAction:")
            print(f"  {answer.get('action', 'N/A')[:200]}...")
            print("\nResult:")
            print(f"  {answer.get('result', 'N/A')[:200]}...")
            
        except Exception as e:
            print(f"  ✗ Error reading STAR answer file: {e}")
    else:
        print(f"  ✗ Failed to generate STAR answer")
    
    # Step 10: Clean up
    print("\nStep 10: Cleaning up...")
    state_manager.close()
    print("  ✓ Closed state manager")
    
    print("\nTest completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
