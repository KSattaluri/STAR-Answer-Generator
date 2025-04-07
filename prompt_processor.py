"""
Prompt Processor Module

This module handles loading, processing, and parameter substitution for prompt templates.
It includes functions for loading role-specific skills and other dynamic content.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from logger_setup import logger

def load_prompt_template(template_path):
    """
    Load a prompt template from a file.
    
    Args:
        template_path (str): Path to the template file
        
    Returns:
        str: The template content, or None if loading failed
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        print(f"Loaded prompt template from {template_path}")
        logger.debug(f"Loaded prompt template from {template_path}")
        return template
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        logger.error(f"Template file not found: {template_path}")
        return None
    except Exception as e:
        print(f"Error loading template {template_path}: {e}")
        logger.error(f"Error loading template {template_path}: {e}")
        return None

def load_role_skills(role_name, config=None):
    """
    Load skills for a specific role from the corresponding skills file.
    
    Args:
        role_name (str): The name of the role (e.g., "Technical Delivery Manager (TDM)")
        config (dict, optional): Configuration dictionary containing role_mappings
        
    Returns:
        str: The role-specific skills content, or a default message if loading failed
    """
    # Try to load config if not provided
    if config is None:
        try:
            from config import load_config
            config = load_config('config.yaml')
        except Exception as e:
            logger.error(f"Error loading config for role mappings: {e}")
            config = {}
    
    role_mappings = config.get('role_mappings', {})
    skills_file = None
    base_role_name = None
    
    # First, extract the base role name (without the abbreviation in parentheses)
    match = re.search(r'(.+?)\s*\([^)]+\)', role_name)
    if match:
        base_role_name = match.group(1).strip()
    else:
        base_role_name = role_name.strip()
    
    # Try to find a direct match in role_mappings
    if base_role_name in role_mappings:
        role_info = role_mappings[base_role_name]
        skills_file = role_info.get('skills_file')
        logger.debug(f"Found exact role mapping for '{base_role_name}': {skills_file}")
    else:
        # Try to find a partial match (role name might be slightly different)
        for mapped_role, role_info in role_mappings.items():
            if base_role_name.startswith(mapped_role) or mapped_role.startswith(base_role_name):
                skills_file = role_info.get('skills_file')
                logger.debug(f"Found partial role mapping for '{base_role_name}' via '{mapped_role}': {skills_file}")
                break
    
    if not skills_file:
        # Fallback to the old method if no mapping found
        logger.warning(f"No skill file mapping found for role: {role_name}")
        
        # Extract abbreviation if present
        abbr_match = re.search(r'\(([^)]+)\)', role_name)
        if abbr_match:
            abbr = abbr_match.group(1)
            skills_file = f"prompt_templates/role_skills/{abbr}-Skills.md"
        else:
            # No abbreviation, try to create one from the role name
            words = role_name.split()
            if len(words) > 1 and len(words[-1]) <= 5 and words[-1][0].isupper():
                abbr = words[-1].upper()
            else:
                abbr = ''.join(word[0] for word in words if word[0].isupper())
            
            skills_file = f"prompt_templates/role_skills/{abbr}-Skills.md"
    
    # Check if the file exists, if not try alternative formats
    if not os.path.exists(skills_file):
        # Try without the hyphen
        skills_file = f"prompt_templates/role_skills/{role_abbr}Skills.md"
        
        if not os.path.exists(skills_file):
            # Try with lowercase abbreviation
            skills_file = f"prompt_templates/role_skills/{role_abbr.lower()}-Skills.md"
            
            if not os.path.exists(skills_file):
                # Try with uppercase abbreviation
                skills_file = f"prompt_templates/role_skills/{role_abbr.upper()}-Skills.md"
                
                if not os.path.exists(skills_file):
                    print(f"Could not find skills file for role: {role_name} (tried abbreviation: {role_abbr})")
                    logger.warning(f"Could not find skills file for role: {role_name} (tried abbreviation: {role_abbr})")
                    return f"Skills specific to the {role_name} role"
    
    # Load the skills file content
    try:
        with open(skills_file, 'r', encoding='utf-8') as f:
            skills_content = f.read()
        print(f"Loaded skills for {role_name} from {skills_file}")
        logger.debug(f"Loaded skills for {role_name} from {skills_file}")
        return skills_content
    except Exception as e:
        print(f"Error loading skills file {skills_file}: {e}")
        logger.error(f"Error loading skills file {skills_file}: {e}")
        return f"Skills specific to the {role_name} role"

def save_full_prompt(prompt_text, stage_name, parameters=None, config=None):
    """
    Save the full prompt to a file after parameter substitution.
    
    Args:
        prompt_text (str): The complete prompt text after parameter substitution
        stage_name (str): The name of the stage (e.g., 'subprompt', 'star_answer', 'conversational')
        parameters (dict, optional): The parameters used for substitution
        config (dict, optional): Configuration dictionary
        
    Returns:
        str: Path to the saved file, or None if saving failed
    """
    # Load config if not provided
    if not config:
        try:
            from config import load_config
            config = load_config('config.yaml')
            logger.debug(f"Loaded config for prompt logging")
        except Exception as e:
            logger.error(f"Error loading config for prompt logging: {e}")
            return None
    
    # Always enable prompt logging by default if not specified
    if 'save_full_prompts' not in config:
        config['save_full_prompts'] = True
        
    # Check if prompt logging is enabled
    if not config.get('save_full_prompts', True):  # Default to True 
        logger.debug(f"Prompt logging is disabled in config")
        return None
    
    logger.info(f"Saving {stage_name} prompt to log file")
    
    try:
        # Get output directories from config
        base_dir = config.get('output_base_dir', 'generated_answers')
        prompt_logs_dir = os.path.join(base_dir, config.get('prompt_logs_dir', 'prompt_logs'))
        
        # Create directory if it doesn't exist
        os.makedirs(prompt_logs_dir, exist_ok=True)
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract identifiers from parameters if available
        role_abbr = "unknown_role"
        question_id = "unknown_q"
        industry_abbr = "unknown_ind"
        
        if parameters:
            # Handle role abbreviation
            if 'TARGET_ROLE' in parameters:
                role = parameters['TARGET_ROLE']
                # Try to extract abbreviation from parentheses (e.g., "Technical Delivery Manager (TDM)")
                match = re.search(r'\(([^)]+)\)', role)
                if match:
                    role_abbr = match.group(1).lower()
                else:
                    # If no parentheses, try to map from config if available
                    try:
                        # Try to get abbreviation from config
                        if config and 'role_mappings' in config:
                            role_mappings = config.get('role_mappings', {})
                            for mapped_role, role_info in role_mappings.items():
                                if mapped_role.lower() == role.lower() or mapped_role.lower() in role.lower():
                                    role_abbr = role_info.get('abbreviation', '').lower()
                                    break
                    except Exception:
                        pass
                    
                    # If still no match, create abbreviation from first letters
                    if role_abbr == "unknown_role":
                        role_abbr = ''.join(word[0].lower() for word in role.split() if word[0].isalpha())
            
            # Special handling for conversational stage which has STAR_ANSWER_FILE param
            if stage_name == 'conversational' and 'STAR_ANSWER_FILE' in parameters:
                # Extract information from the STAR answer filename
                star_file = parameters['STAR_ANSWER_FILE']
                logger.info(f"DEBUGGING - STAR_ANSWER_FILE value: {star_file}")
                
                # Common patterns for STAR answer filenames
                patterns = [
                    r'([a-z]+)_q(\d+)_([a-z]+)_\d+_star',  # tdm_q1_fin_1_star.json
                    r'([a-z]+)_q?(\d+)_([a-z]+)\w*\.json',  # any variation with role, q, industry 
                    r'([a-z]{2,5}).*?([0-9]+).*?([a-z]{2,5})'   # fallback - extract any likely abbr+number+abbr pattern
                ]
                
                match = None
                for pattern in patterns:
                    match = re.search(pattern, star_file.lower())
                    if match:
                        logger.info(f"DEBUGGING - Matched pattern: {pattern}")
                        break
                        
                if match:
                    role_abbr = match.group(1)  # e.g., 'tdm'
                    question_id = f"q{match.group(2)}"  # e.g., 'q1'
                    industry_abbr = match.group(3)  # e.g., 'fin'
                    logger.info(f"DEBUGGING - Extracted role_abbr={role_abbr}, question_id={question_id}, industry_abbr={industry_abbr} from {star_file}")
                else:
                    logger.warning(f"DEBUGGING - Failed to extract metadata from STAR_ANSWER_FILE: {star_file}")
                    
            # Handle question ID for non-conversational stages or if extraction failed
            elif 'CORE_INTERVIEW_QUESTION' in parameters:
                question = parameters['CORE_INTERVIEW_QUESTION']
                # Look for Q followed by a number in the question or parameters
                match = re.search(r'Q(\d+)', question)
                if match:
                    question_id = f"q{match.group(1)}"
                elif 'PROMPT_ID' in parameters and re.search(r'Q\d+', parameters['PROMPT_ID']):
                    # Try to extract from PROMPT_ID if available
                    match = re.search(r'Q(\d+)', parameters['PROMPT_ID'])
                    question_id = f"q{match.group(1)}"
                else:
                    question_id = "q1"  # Default to q1 if no pattern found
            
            # Handle industry abbreviation
            if 'TARGET_INDUSTRY' in parameters:
                industry = parameters['TARGET_INDUSTRY']
                # Try to get abbreviation from config
                try:
                    if config and 'industry_mappings' in config:
                        industry_mappings = config.get('industry_mappings', {})
                        for mapped_industry, industry_info in industry_mappings.items():
                            if mapped_industry.lower() == industry.lower() or mapped_industry.lower() in industry.lower():
                                if isinstance(industry_info, dict):
                                    industry_abbr = industry_info.get('abbreviation', '').lower()
                                else:
                                    industry_abbr = str(industry_info).lower()
                                break
                except Exception:
                    pass
                
                # If no match found, create a simple abbreviation
                if industry_abbr == "unknown_ind":
                    industry_abbr = industry.split('/')[0].strip().lower().replace(' ', '_')[:3]
        
        # Create filename using the same format as other files in the system
        filename = f"{role_abbr}_{question_id}_{industry_abbr}_{stage_name}_prompt.txt"
        file_path = os.path.join(prompt_logs_dir, filename)
        
        # Write prompt to file
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write metadata
            f.write("===== PROMPT METADATA =====\n")
            f.write(f"Stage: {stage_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            
            # Write parameters if available
            if parameters:
                f.write("\n===== PARAMETERS =====\n")
                # Only write key parameters to avoid very large files
                key_params = [
                    'TARGET_ROLE', 'TARGET_INDUSTRY', 'CORE_INTERVIEW_QUESTION', 
                    'SKILL_FOCUS', 'SOFT_SKILL_HIGHLIGHT', 'SCENARIO_THEME_HINT',
                    'PROMPT_ID'
                ]
                for key in key_params:
                    if key in parameters:
                        f.write(f"{key}: {parameters[key]}\n")
            
            # Write the full prompt
            f.write("\n===== FULL PROMPT =====\n")
            f.write(prompt_text)
        
        logger.info(f"Saved full prompt to: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving full prompt: {e}")
        return None

def substitute_parameters(template, parameters, stage_name=None, config=None):
    """
    Substitute parameters in a template.
    
    Args:
        template (str): The template string with placeholders
        parameters (dict): Dictionary of parameter names and values
        stage_name (str, optional): The name of the stage for logging
        config (dict, optional): Configuration dictionary
        
    Returns:
        str: The template with parameters substituted
    """
    # Automatically determine stage name if not provided
    if not stage_name and parameters:
        # Try to guess stage name from parameters
        if 'NUM_PROMPTS_TO_GENERATE' in parameters:
            stage_name = 'subprompt'
        elif 'SKILL_FOCUS' in parameters and 'SUB_PROMPT' in parameters:
            stage_name = 'star_answer'
        elif 'STAR_ANSWER' in parameters:
            stage_name = 'conversational'
    result = template
    
    # Process special parameters that require function calls
    if 'TARGET_ROLE' in parameters and 'TARGET_ROLE_SKILLS' not in parameters:
        parameters['TARGET_ROLE_SKILLS'] = load_role_skills(parameters['TARGET_ROLE'])
    
    # Substitute all parameters
    for param_name, param_value in parameters.items():
        # Handle [PARAM_NAME] format (used in stage1 and stage2)
        placeholder = f"[{param_name}]"
        result = result.replace(placeholder, str(param_value))
        
        # Handle {{PARAM_NAME}} format (used in stage3 - conversational)
        placeholder = f"{{{{{param_name}}}}}"
        result = result.replace(placeholder, str(param_value))
    
    # Add debug logging to help diagnose substitution issues
    logger.debug(f"Parameter substitution completed. Template starts with: {result[:200]}...")
    print(f"Parameter substitution completed. First 100 chars: {result[:100]}...")
    
    # Save the full prompt if stage_name is provided
    if stage_name:
        save_full_prompt(result, stage_name, parameters, config)
    
    return result

def generate_sub_prompt(meta_prompt_template, parameters, config=None):
    """
    Generate a sub-prompt by substituting parameters in the meta-prompt template.
    
    Args:
        meta_prompt_template (str): The meta-prompt template
        parameters (dict): Dictionary of parameter names and values
        config (dict, optional): Configuration dictionary
        
    Returns:
        str: The generated sub-prompt
    """
    return substitute_parameters(meta_prompt_template, parameters, 'subprompt', config)

def generate_main_context(main_context_template, parameters, config=None):
    """
    Generate the main context by substituting parameters in the template.
    
    Args:
        main_context_template (str): The main context template
        parameters (dict): Dictionary of parameter names and values
        config (dict, optional): Configuration dictionary
        
    Returns:
        str: The generated main context
    """
    return substitute_parameters(main_context_template, parameters, 'star_answer', config)

def generate_conversation_prompt(conversation_template, parameters, config=None):
    """
    Generate a conversation prompt by substituting parameters in the template.
    
    Args:
        conversation_template (str): The conversation prompt template
        parameters (dict): Dictionary of parameter names and values
        config (dict, optional): Configuration dictionary
        
    Returns:
        str: The generated conversation prompt
    """
    return substitute_parameters(conversation_template, parameters, 'conversational', config)

if __name__ == "__main__":
    # Example usage
    from logger_setup import setup_logging
    
    # Set up logging
    setup_logging(log_level="DEBUG")
    
    # Load a template
    template = load_prompt_template("prompt_templates/stage1_subprompt_generator.md")
    
    if template:
        # Define parameters
        params = {
            "TARGET_ROLE": "Technical Delivery Manager (TDM)",
            "TARGET_INDUSTRY": "Finance / Financial Services",
            "TARGET_QUESTION": "Describe a situation where you had to manage a complex project with multiple stakeholders."
        }
        
        # Generate a sub-prompt
        sub_prompt = generate_sub_prompt(template, params)
        
        # Print the first 500 characters of the result
        logger.info(f"Generated sub-prompt (first 500 chars):\n{sub_prompt[:500]}...")
