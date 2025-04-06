"""
Sub-Prompt Generator Module

This module handles the generation of sub-prompts for the STAR Answer Generation System.
It uses the stage1 prompt template to generate JSON sub-prompts for each role/question/industry
combination defined in the configuration.
"""

import os
import json
import time
from pathlib import Path
import random

# Import project modules
# Use print instead of logger for initialization
from prompt_processor import load_prompt_template, substitute_parameters
from llm_client import LLMClient
from state_manager import StateManager, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_FAILED

def generate_subprompt_parameters(config, role, question, industry, num_prompts=3):
    """
    Generate parameters for the sub-prompt template.
    
    Args:
        config (dict): Configuration dictionary
        role (str): Target role name
        question (str): Interview question
        industry (str): Target industry
        num_prompts (int): Number of sub-prompts to generate
        
    Returns:
        dict: Dictionary of parameters for the template
    """
    # Load role-specific skills
    from prompt_processor import load_role_skills
    role_skills = load_role_skills(role, config)
    
    return {
        "NUM_PROMPTS_TO_GENERATE": str(num_prompts),
        "TARGET_ROLE": role,
        "TARGET_INDUSTRY": industry,
        "CORE_INTERVIEW_QUESTION": question,
        "TARGET_ROLE_SKILLS": role_skills  # Add the role skills for consistent parameter naming
    }

def parse_subprompt_json(json_text):
    """
    Parse the JSON output from the LLM response.
    
    Args:
        json_text (str): JSON text from LLM response
        
    Returns:
        list: List of sub-prompt dictionaries, or None if parsing failed
    """
    try:
        # Find JSON array in the text (it might be surrounded by other text)
        start_idx = json_text.find('[')
        end_idx = json_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            print("No JSON array found in the response")
            return None
            
        json_array_text = json_text[start_idx:end_idx]
        
        # Parse the JSON array
        subprompts = json.loads(json_array_text)
        
        # Validate the structure
        if not isinstance(subprompts, list):
            print("Parsed JSON is not a list")
            return None
            
        # Check if each item has the required fields
        required_fields = [
            "prompt_id", "prompt_number", "total_prompts", 
            "core_interview_question", "llm_instructions",
            "skill_focus", "soft_skill_highlight", 
            "scenario_theme_hint", "final_output_instructions"
        ]
        
        for i, subprompt in enumerate(subprompts):
            missing_fields = [field for field in required_fields if field not in subprompt]
            if missing_fields:
                print(f"Sub-prompt {i+1} is missing required fields: {missing_fields}")
        
        return subprompts
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return None
    except Exception as e:
        print(f"Error parsing sub-prompt JSON: {e}")
        return None

def save_subprompts(subprompts, output_dir, role_name, question_index, industry):
    """
    Save sub-prompts to a JSON file.
    
    Args:
        subprompts (list): List of sub-prompt dictionaries
        output_dir (str): Directory to save the file
        role_name (str): Target role name
        question_index (int): Index of the question
        industry (str): Target industry
        
    Returns:
        str: Path to the saved file, or None if saving failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get role abbreviation from config
        role_base = role_name.split('(')[0].strip()
        role_abbr = None
        
        # Get the config to access role mappings
        from config import load_config
        config = load_config('config.yaml')
        
        # Look up role abbreviation
        role_mappings = config.get('role_mappings', {})
        for mapped_role, role_info in role_mappings.items():
            if role_base == mapped_role:
                role_abbr = role_info.get('abbreviation')
                break
                
        if not role_abbr:
            # Fallback to old method if no abbreviation found
            role_abbr = role_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
        else:
            role_abbr = role_abbr.lower()  # Ensure lowercase for filenames
            
        # Get industry abbreviation from config
        industry_abbr = None
        industry_mappings = config.get('industry_mappings', {})
        if industry in industry_mappings:
            industry_abbr = industry_mappings[industry].get('abbreviation')
            
        if not industry_abbr:
            # Fallback to old method if no abbreviation found
            industry_abbr = industry.replace(" ", "_").replace("/", "_").lower()
        else:
            industry_abbr = industry_abbr.lower()  # Ensure lowercase for filenames
            
        # Get question ID from config
        question_id = f"q{question_index+1}"  # Default format for backwards compatibility
        for role_config in config.get('target_roles', []):
            if role_config.get('name') == role_base:
                questions = role_config.get('questions', [])
                if question_index < len(questions) and isinstance(questions[question_index], dict):
                    question_id = questions[question_index].get('id', f"q{question_index+1}").lower()
        
        # Create the output file path using the new naming scheme
        output_file = os.path.join(
            output_dir, 
            f"{role_abbr}_{question_id}_{industry_abbr}_subprompts.json"
        )
        
        # Save the sub-prompts to the file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(subprompts, f, indent=2)
            
        print(f"Saved {len(subprompts)} sub-prompts to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error saving sub-prompts: {e}")
        return None

def generate_subprompts(config, state_manager, llm_client, args=None):
    """
    Generate sub-prompts for all role/question/industry combinations.
    
    Args:
        config (dict): Configuration dictionary
        state_manager (StateManager): State manager instance
        llm_client (LLMClient): LLM client instance
        args (argparse.Namespace, optional): Command-line arguments
        
    Returns:
        bool: True if all sub-prompts were generated successfully, False otherwise
    """
    print("Starting sub-prompt generation (Stage 1)")
    
    # Get the stage1 prompt template
    template_path = config['prompts']['meta_prompt']
    template = load_prompt_template(template_path)
    
    if not template:
        print(f"Failed to load stage1 prompt template from {template_path}")
        return False
        
    # Get the stage2 prompt template for context
    main_context_path = config['prompts']['main_context']
    main_context = load_prompt_template(main_context_path)
    
    if not main_context:
        print(f"Failed to load stage2 prompt template from {main_context_path}")
        return False
    
    # Get configuration values
    target_roles = config.get('target_roles', [])
    target_industries = config.get('target_industries', [])
    num_answers_per_question = config.get('num_answers_per_question', 3)
    industry_distribution = config.get('industry_distribution', 'cycle')
    
    # Create output directory
    subprompts_dir = os.path.join(
        config.get('output', {}).get('base_dir', 'generated_answers'),
        config.get('subprompts_dir', 'sub_prompts')
    )
    os.makedirs(subprompts_dir, exist_ok=True)
    
    # Track overall success
    all_successful = True
    
    # Apply filters if specified in args
    role_filter = getattr(args, 'role', None)
    question_filter = getattr(args, 'question', None)
    industry_filter = getattr(args, 'industry', None)
    
    # Process each role
    for role_config in target_roles:
        # Handle both dictionary and string formats for roles
        if isinstance(role_config, dict):
            # Get the base role name
            base_role_name = role_config.get('name')
            
            # Get questions from the new interview_questions format
            interview_questions = role_config.get('interview_questions', {})
            questions = []
            
            # Convert the dictionary format to a list for backwards compatibility
            if interview_questions:
                for q_id, q_text in interview_questions.items():
                    questions.append({
                        'id': q_id,
                        'text': q_text
                    })
            # Fallback to old format if interview_questions not found
            elif 'questions' in role_config:
                questions = role_config.get('questions', [])
        else:
            # If role_config is a string, use it directly as the base role name
            base_role_name = role_config
            # Use the target_questions from the main config for string roles
            questions = config.get('target_questions', [])
        
        # Check if this role has a mapping in the config
        role_mappings = config.get('role_mappings', {})
        # Extract just the main part of the role name (in case it already has an abbreviation in parentheses)
        base_role_key = base_role_name.split('(')[0].strip()
        
        # Try to find the role mapping
        if base_role_key in role_mappings:
            role_info = role_mappings[base_role_key]
            abbr = role_info.get('abbreviation')
            role_name = f"{base_role_key} ({abbr})"
            print(f"Using mapped role name: {role_name}")
        else:
            # If no mapping found, try partial matches
            match_found = False
            for mapped_role, role_info in role_mappings.items():
                if base_role_key.startswith(mapped_role) or mapped_role.startswith(base_role_key):
                    abbr = role_info.get('abbreviation')
                    role_name = f"{mapped_role} ({abbr})"
                    print(f"Using partially matched role name: {role_name}")
                    match_found = True
                    break
            
            # If still no mapping found, use the original name
            if not match_found:
                role_name = base_role_name
        
        # Skip if role filter is specified and doesn't match
        if role_filter and role_filter.lower() not in role_name.lower():
            print(f"Skipping role {role_name} due to role filter")
            continue
        
        # Process each question for this role
        for q_index, question_item in enumerate(questions):
            # Handle both old and new question formats
            if isinstance(question_item, dict):
                question_id = question_item.get('id', f"Q{q_index+1}")
                question = question_item.get('text', '')
            else:
                # If it's just a string, use it directly
                question = question_item
                question_id = f"Q{q_index+1}"
                
            # Skip if question filter is specified and doesn't match
            if question_filter and question_filter.lower() not in question.lower():
                print(f"Skipping question '{question}' due to question filter")
                continue
                
            # Determine which industries to use for this question
            industries_to_use = []
            
            if industry_distribution == 'cycle':
                # Use one industry in rotation
                industry_index = q_index % len(target_industries)
                industries_to_use = [target_industries[industry_index]]
            elif industry_distribution == 'random':
                # Use a random industry
                industries_to_use = [random.choice(target_industries)]
            elif industry_distribution == 'balanced':
                # Use all industries
                industries_to_use = target_industries
            else:
                # Default to all industries
                industries_to_use = target_industries
            
            # Process each industry for this question
            for industry in industries_to_use:
                # Skip if industry filter is specified and doesn't match
                if industry_filter and industry_filter.lower() not in industry.lower():
                    print(f"Skipping industry {industry} due to industry filter")
                    continue
                    
                # Create a file path for tracking in the state manager that matches the actual filename
                role_slug = role_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
                industry_slug = industry.replace(" ", "_").replace("/", "_").lower()
                file_id = f"{role_slug}_q{q_index+1}_{industry_slug}"
                
                # Check if this combination has already been processed
                if args and hasattr(args, 'resume') and args.resume:
                    status = state_manager.get_file_status(file_id)
                    if status == STATUS_COMPLETE:
                        print(f"Skipping already completed: {role_name}, Q{q_index+1}, {industry}")
                        continue
                
                # Add to state manager with pending status
                state_manager.add_file(file_id, 'sub_prompt')
                state_manager.update_status(file_id, STATUS_IN_PROGRESS)
                
                try:
                    # Generate parameters for this combination
                    params = generate_subprompt_parameters(
                        config, role_name, question, industry, num_answers_per_question
                    )
                    
                    # Generate the sub-prompt by substituting parameters
                    prompt = substitute_parameters(template, params)
                    
                    # Append the main context prompt for reference
                    full_prompt = f"{prompt}\n\n{main_context}"
                    
                    print(f"Generating sub-prompts for: {role_name}, Q{q_index+1}, {industry}")
                    
                    # Call the LLM to generate sub-prompts
                    response = llm_client.generate_response(
                        prompt=full_prompt,
                        max_tokens=config.get('step1_max_tokens', 4000),
                        temperature=0.7,
                        json_mode=True
                    )
                    
                    if not response:
                        print(f"Failed to get response from LLM for {file_id}")
                        state_manager.update_status(file_id, STATUS_FAILED, error_message="No response from LLM")
                        all_successful = False
                        continue
                    
                    # Parse the JSON response
                    subprompts = parse_subprompt_json(response['text'])
                    
                    if not subprompts:
                        print(f"Failed to parse sub-prompts for {file_id}")
                        state_manager.update_status(file_id, STATUS_FAILED, error_message="Failed to parse JSON response")
                        all_successful = False
                        continue
                    
                    # Save the sub-prompts to a file
                    output_file = save_subprompts(subprompts, subprompts_dir, role_name, q_index, industry)
                    
                    if not output_file:
                        print(f"Failed to save sub-prompts for {file_id}")
                        state_manager.update_status(file_id, STATUS_FAILED, error_message="Failed to save sub-prompts")
                        all_successful = False
                        continue
                    
                    # Update state manager with success
                    state_manager.update_status(file_id, STATUS_COMPLETE, processed_file_path=output_file)
                    print(f"Successfully generated sub-prompts for: {role_name}, Q{q_index+1}, {industry}")
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(config.get('api_delay_seconds', 2))
                    
                except Exception as e:
                    print(f"Error generating sub-prompts for {file_id}: {e}")
                    state_manager.update_status(file_id, STATUS_FAILED, error_message=str(e))
                    all_successful = False
    
    # Log summary
    summary = state_manager.get_summary(stage='sub_prompt')
    if summary:
        print(f"Sub-prompt generation summary: {summary}")
    
    return all_successful

if __name__ == "__main__":
    # This is for testing the module directly
    from logger_setup import setup_logging
    from config import load_config
    from state_manager import StateManager
    from llm_client import LLMClient
    import argparse
    
    # Set up logging
    setup_logging(log_level="DEBUG")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Sub-Prompt Generator')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--role', type=str, help='Process only a specific role')
    parser.add_argument('--question', type=str, help='Process only a specific question')
    parser.add_argument('--industry', type=str, help='Process only a specific industry')
    parser.add_argument('--resume', action='store_true', help='Resume from last successful point')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    if not config:
        print("Failed to load configuration. Exiting.")
        exit(1)
    
    # Initialize state manager
    db_path = os.path.join(
        config.get('output', {}).get('base_dir', 'generated_answers'),
        'processing_state.db'
    )
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Generate sub-prompts
    success = generate_subprompts(config, state_manager, llm_client, args)
    
    # Clean up
    state_manager.close()
    
    if success:
        print("Sub-prompt generation completed successfully")
    else:
        print("Sub-prompt generation completed with errors")
