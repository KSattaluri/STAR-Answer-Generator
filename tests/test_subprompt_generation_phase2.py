"""
Test Script for Phase 2 (Sub-Prompt Generation)

This script tests the sub-prompt generation functionality with minimal dependencies.
"""

import os
import json
import time
from pathlib import Path

def main():
    print("\n" + "=" * 80)
    print("TESTING PHASE 2: SUB-PROMPT GENERATION")
    print("=" * 80 + "\n")
    
    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    from config import load_config
    config = load_config('config.yaml')
    
    if not config:
        print("  ✗ Failed to load configuration. Exiting.")
        return
    
    print("  ✓ Configuration loaded successfully")
    
    # Step 2: Create output directory
    print("\nStep 2: Setting up output directory...")
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(output_dir, config.get('subprompts_dir', 'sub_prompts'))
    os.makedirs(subprompts_dir, exist_ok=True)
    print(f"  ✓ Created output directory: {subprompts_dir}")
    
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
    
    # Step 5: Load prompt templates
    print("\nStep 5: Loading prompt templates...")
    from prompt_processor import load_prompt_template, substitute_parameters
    
    # Get the stage1 prompt template
    template_path = config['prompts']['meta_prompt']
    template = load_prompt_template(template_path)
    
    if not template:
        print(f"  ✗ Failed to load stage1 prompt template from {template_path}")
        return
    
    print(f"  ✓ Loaded stage1 prompt template from {template_path}")
    
    # Get the stage2 prompt template for context
    main_context_path = config['prompts']['main_context']
    main_context = load_prompt_template(main_context_path)
    
    if not main_context:
        print(f"  ✗ Failed to load stage2 prompt template from {main_context_path}")
        return
    
    print(f"  ✓ Loaded stage2 prompt template from {main_context_path}")
    
    # Step 6: Generate a sub-prompt for a single role/question/industry combination
    print("\nStep 6: Generating a sub-prompt...")
    
    # Select a single role, question, and industry for testing
    role_name = "Technical Delivery Manager (TDM)"
    question = "Talk about a time when you went above and beyond your role to accomplish a goal."
    industry = "Finance / Financial Services"
    num_prompts = 1  # Just generate one sub-prompt for testing
    
    print(f"  Role: {role_name}")
    print(f"  Question: {question}")
    print(f"  Industry: {industry}")
    print(f"  Number of sub-prompts: {num_prompts}")
    
    # Create a file ID for tracking in the state manager
    file_id = f"{role_name.replace(' ', '_')}_0_{industry.replace(' ', '_')}"
    
    # Add to state manager with pending status
    state_manager.add_file(file_id, 'sub_prompt')
    state_manager.update_status(file_id, STATUS_IN_PROGRESS)
    print(f"  ✓ Added file to state manager: {file_id}")
    
    # Generate parameters for this combination
    params = {
        "NUM_PROMPTS_TO_GENERATE": str(num_prompts),
        "TARGET_ROLE": role_name,
        "TARGET_INDUSTRY": industry,
        "CORE_INTERVIEW_QUESTION": question
    }
    
    # Generate the sub-prompt by substituting parameters
    prompt = substitute_parameters(template, params)
    
    # Append the main context prompt for reference
    full_prompt = f"{prompt}\n\n{main_context}"
    
    print("  ✓ Generated prompt with parameters")
    
    # Step 7: Call the LLM to generate sub-prompts
    print("\nStep 7: Calling LLM to generate sub-prompts...")
    print("  This may take a moment...")
    
    start_time = time.time()
    
    try:
        response = llm_client.generate_response(
            prompt=full_prompt,
            max_tokens=config.get('step1_max_tokens', 4000),
            temperature=0.7,
            json_mode=True
        )
        
        if not response:
            print(f"  ✗ Failed to get response from LLM")
            state_manager.update_status(file_id, STATUS_FAILED, error_message="No response from LLM")
            return
        
        print(f"  ✓ Received response from LLM ({response.get('provider', 'unknown')})")
        
        # Step 8: Parse the JSON response
        print("\nStep 8: Parsing JSON response...")
        
        # Find JSON array in the text (it might be surrounded by other text)
        json_text = response['text']
        start_idx = json_text.find('[')
        end_idx = json_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            print("  ✗ No JSON array found in the response")
            state_manager.update_status(file_id, STATUS_FAILED, error_message="No JSON array found in response")
            return
            
        json_array_text = json_text[start_idx:end_idx]
        
        # Parse the JSON array
        try:
            subprompts = json.loads(json_array_text)
            
            if not isinstance(subprompts, list):
                print("  ✗ Parsed JSON is not a list")
                state_manager.update_status(file_id, STATUS_FAILED, error_message="Parsed JSON is not a list")
                return
            
            print(f"  ✓ Successfully parsed JSON response with {len(subprompts)} sub-prompts")
            
            # Step 9: Save the sub-prompts to a file
            print("\nStep 9: Saving sub-prompts to file...")
            
            # Create a sanitized filename
            role_slug = role_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
            industry_slug = industry.replace(" ", "_").replace("/", "_").lower()
            
            # Create the output file path
            output_file = os.path.join(
                subprompts_dir, 
                f"{role_slug}_q1_{industry_slug}_subprompts.json"
            )
            
            # Save the sub-prompts to the file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(subprompts, f, indent=2)
                
            print(f"  ✓ Saved {len(subprompts)} sub-prompts to {output_file}")
            
            # Update state manager with success
            state_manager.update_status(file_id, STATUS_COMPLETE, processed_file_path=output_file)
            
            # Display the first sub-prompt
            if len(subprompts) > 0:
                print("\nFirst sub-prompt:")
                print(f"  Prompt ID: {subprompts[0].get('prompt_id', 'N/A')}")
                print(f"  Skill focus: {subprompts[0].get('skill_focus', 'N/A')}")
                print(f"  Soft skill highlight: {subprompts[0].get('soft_skill_highlight', 'N/A')}")
                print(f"  Scenario theme: {subprompts[0].get('scenario_theme_hint', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"  ✗ Failed to parse JSON: {e}")
            state_manager.update_status(file_id, STATUS_FAILED, error_message=f"JSON parse error: {e}")
            return
    except Exception as e:
        print(f"  ✗ Error generating sub-prompts: {e}")
        state_manager.update_status(file_id, STATUS_FAILED, error_message=str(e))
        return
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print(f"\nElapsed time: {elapsed_time:.2f} seconds")
    
    # Step 10: Clean up
    print("\nStep 10: Cleaning up...")
    state_manager.close()
    print("  ✓ Closed state manager")
    
    print("\nTest completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
