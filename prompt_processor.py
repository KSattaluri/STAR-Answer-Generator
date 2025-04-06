"""
Prompt Processor Module

This module handles loading, processing, and parameter substitution for prompt templates.
It includes functions for loading role-specific skills and other dynamic content.
"""

import os
import re
from pathlib import Path
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

def substitute_parameters(template, parameters):
    """
    Substitute parameters in a template.
    
    Args:
        template (str): The template string with placeholders
        parameters (dict): Dictionary of parameter names and values
        
    Returns:
        str: The template with parameters substituted
    """
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
    
    return result

def generate_sub_prompt(meta_prompt_template, parameters):
    """
    Generate a sub-prompt by substituting parameters in the meta-prompt template.
    
    Args:
        meta_prompt_template (str): The meta-prompt template
        parameters (dict): Dictionary of parameter names and values
        
    Returns:
        str: The generated sub-prompt
    """
    return substitute_parameters(meta_prompt_template, parameters)

def generate_main_context(main_context_template, parameters):
    """
    Generate the main context by substituting parameters in the template.
    
    Args:
        main_context_template (str): The main context template
        parameters (dict): Dictionary of parameter names and values
        
    Returns:
        str: The generated main context
    """
    return substitute_parameters(main_context_template, parameters)

def generate_conversation_prompt(conversation_template, parameters):
    """
    Generate a conversation prompt by substituting parameters in the template.
    
    Args:
        conversation_template (str): The conversation prompt template
        parameters (dict): Dictionary of parameter names and values
        
    Returns:
        str: The generated conversation prompt
    """
    return substitute_parameters(conversation_template, parameters)

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
