"""
Test script for prompt logging functionality

This script tests the prompt logging functionality we implemented in prompt_processor.py
by directly calling the functions with the proper parameters.
"""

import os
from pathlib import Path
from logger_setup import setup_logging, logger
from config import load_config
from prompt_processor import (
    load_prompt_template, 
    substitute_parameters,
    generate_sub_prompt,
    generate_main_context,
    generate_conversation_prompt
)

def test_prompt_logging():
    """Test the prompt logging functionality."""
    print("Testing prompt logging functionality...")
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    # Load configuration
    config = load_config('config.yaml')
    if not config:
        print("Failed to load configuration. Exiting.")
        return
    
    # Make sure prompt logging is enabled in config
    if not config.get('save_full_prompts', False):
        print("Prompt logging is not enabled in config. Setting it to True for this test.")
        config['save_full_prompts'] = True
    
    # Create output directory if it doesn't exist
    base_dir = config.get('output_base_dir', 'generated_answers')
    prompt_logs_dir = os.path.join(base_dir, config.get('prompt_logs_dir', 'prompt_logs'))
    os.makedirs(prompt_logs_dir, exist_ok=True)
    
    # Load template for subprompt generation
    template_path = config.get('meta_prompt_path', 'prompt_templates/stage1_subprompt_generator.md')
    template = load_prompt_template(template_path)
    if not template:
        print(f"Failed to load template from {template_path}")
        return
    
    # Define test parameters
    params = {
        "NUM_PROMPTS_TO_GENERATE": "1",
        "TARGET_ROLE": "Technical Delivery Manager (TDM)",
        "TARGET_INDUSTRY": "Finance / Financial Services",
        "CORE_INTERVIEW_QUESTION": "Describe a situation where you had to manage a complex project with multiple stakeholders."
    }
    
    # Test sub-prompt generation with explicit config parameter
    print("\nTesting sub-prompt generation...")
    sub_prompt = generate_sub_prompt(template, params, config)
    print(f"Sub-prompt generation completed. Check {prompt_logs_dir} for logs.")
    
    # Load template for STAR answer generation
    template_path = config.get('main_context_prompt_path', 'prompt_templates/stage2_star_answer_generator.md')
    template = load_prompt_template(template_path)
    if not template:
        print(f"Failed to load template from {template_path}")
        return
    
    # Define test parameters for STAR answer generation
    params = {
        "TARGET_ROLE": "Technical Delivery Manager (TDM)",
        "TARGET_INDUSTRY": "Finance / Financial Services",
        "CORE_INTERVIEW_QUESTION": "Describe a situation where you had to manage a complex project with multiple stakeholders.",
        "SKILL_FOCUS": "Project Management, Stakeholder Management",
        "SOFT_SKILL_HIGHLIGHT": "Communication, Leadership",
        "SCENARIO_THEME_HINT": "Cross-functional project with competing priorities",
        "SUB_PROMPT": "Generate a detailed STAR answer for a Technical Delivery Manager role...",
        "PROMPT_ID": "TDM-Q1-1"
    }
    
    # Test STAR answer generation with explicit config parameter
    print("\nTesting STAR answer generation...")
    star_answer = generate_main_context(template, params, config)
    print(f"STAR answer generation completed. Check {prompt_logs_dir} for logs.")
    
    # Load template for conversational transformation
    template_path = config.get('conversation_prompt_path', 'prompt_templates/stage3_conversational_transformer.md')
    template = load_prompt_template(template_path)
    if not template:
        print(f"Failed to load template from {template_path}")
        return
    
    # Define test parameters for conversational transformation
    params = {
        "TARGET_ROLE": "Technical Delivery Manager (TDM)",
        "TARGET_INDUSTRY": "Finance / Financial Services",
        "CORE_INTERVIEW_QUESTION": "Describe a situation where you had to manage a complex project with multiple stakeholders.",
        "STAR_ANSWER": "Situation: I led a complex project... Task: I needed to... Action: I implemented... Result: The project was completed..."
    }
    
    # Test conversational transformation with explicit config parameter
    print("\nTesting conversational transformation...")
    conv_answer = generate_conversation_prompt(template, params, config)
    print(f"Conversational transformation completed. Check {prompt_logs_dir} for logs.")
    
    print("\nAll prompt logging tests completed. Check the following directory for logs:")
    print(prompt_logs_dir)
    
    # List generated log files
    log_files = list(Path(prompt_logs_dir).glob("*.txt"))
    if log_files:
        print(f"\nGenerated {len(log_files)} log files:")
        for file in log_files:
            print(f"  - {file.name}")
    else:
        print("No log files were generated. Check the log_level and implementation.")

if __name__ == "__main__":
    test_prompt_logging()
