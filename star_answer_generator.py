"""
STAR Answer Generator

This module handles Phase 3 of the STAR Answer Generation System:
1. Loads sub-prompts generated in Phase 2
2. Uses the main context prompt template to generate STAR answers
3. Saves the generated answers to files

The module follows the same resilient design principles as the rest of the system:
- Persistent state tracking
- Proper error handling
- Support for resuming interrupted processing
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from logger_setup import logger
from state_manager import StateManager, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_FAILED
from llm_client import LLMClient
from prompt_processor import load_prompt_template, substitute_parameters, load_role_skills

# Print statements alongside logger calls for critical operations
print("Initializing STAR Answer Generator module")
logger.info("Initializing STAR Answer Generator module")

def load_subprompts(subprompt_file_path: str) -> List[Dict[str, Any]]:
    """
    Load sub-prompts from a JSON file.
    
    Args:
        subprompt_file_path (str): Path to the sub-prompt JSON file
        
    Returns:
        List[Dict[str, Any]]: List of sub-prompts, or empty list if loading failed
    """
    try:
        with open(subprompt_file_path, 'r', encoding='utf-8') as f:
            subprompts = json.load(f)
        
        print(f"Loaded {len(subprompts)} sub-prompts from {subprompt_file_path}")
        logger.info(f"Loaded {len(subprompts)} sub-prompts from {subprompt_file_path}")
        return subprompts
    except FileNotFoundError:
        print(f"Sub-prompt file not found: {subprompt_file_path}")
        logger.error(f"Sub-prompt file not found: {subprompt_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing sub-prompt file {subprompt_file_path}: {e}")
        logger.error(f"Error parsing sub-prompt file {subprompt_file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error loading sub-prompts from {subprompt_file_path}: {e}")
        logger.error(f"Error loading sub-prompts from {subprompt_file_path}: {e}")
        return []

def generate_star_answer_parameters(
    subprompt: Dict[str, Any], 
    role_name: str, 
    industry: str, 
    question: str
) -> Dict[str, str]:
    """
    Generate parameters for the STAR answer prompt template.
    
    Args:
        subprompt (Dict[str, Any]): The sub-prompt to use
        role_name (str): The target role
        industry (str): The target industry
        question (str): The interview question
        
    Returns:
        Dict[str, str]: Parameters for the prompt template
    """
    # Extract values from the sub-prompt
    prompt_id = subprompt.get('prompt_id', 'unknown')
    skill_focus = subprompt.get('skill_focus', 'unknown')
    soft_skill = subprompt.get('soft_skill_highlight', 'unknown')
    scenario_theme = subprompt.get('scenario_theme_hint', 'unknown')
    
    # Create parameters dictionary
    params = {
        "TARGET_ROLE": role_name,
        "TARGET_INDUSTRY": industry,
        "CORE_INTERVIEW_QUESTION": question,
        "SKILL_FOCUS": skill_focus,
        "SOFT_SKILL_HIGHLIGHT": soft_skill,
        "SCENARIO_THEME_HINT": scenario_theme,
        "SUB_PROMPT": subprompt.get('prompt', ''),
        "PROMPT_ID": prompt_id
    }
    
    return params

def parse_star_answer(response_text: str) -> Dict[str, str]:
    """
    Parse the STAR answer from the LLM response.
    
    Args:
        response_text (str): The raw response from the LLM
        
    Returns:
        Dict[str, str]: Parsed STAR answer with sections
    """
    # Initialize the result dictionary with default values
    result = {
        "situation": "",
        "task": "",
        "action": "",
        "result": "",
        "full_answer": response_text
    }
    
    # Try to extract the STAR sections
    try:
        # Look for Situation section
        situation_start = response_text.lower().find("situation:")
        task_start = response_text.lower().find("task:")
        
        if situation_start != -1 and task_start != -1:
            result["situation"] = response_text[situation_start + 10:task_start].strip()
        
        # Look for Task section
        action_start = response_text.lower().find("action:")
        
        if task_start != -1 and action_start != -1:
            result["task"] = response_text[task_start + 5:action_start].strip()
        
        # Look for Action section
        result_start = response_text.lower().find("result:")
        
        if action_start != -1 and result_start != -1:
            result["action"] = response_text[action_start + 7:result_start].strip()
        
        # Look for Result section
        if result_start != -1:
            result["result"] = response_text[result_start + 7:].strip()
    
    except Exception as e:
        print(f"Error parsing STAR answer: {e}")
        logger.error(f"Error parsing STAR answer: {e}")
    
    return result

def save_star_answer(
    answer: Dict[str, str], 
    output_path: str, 
    metadata: Dict[str, Any]
) -> bool:
    """
    Save the generated STAR answer to a JSON file.
    
    Args:
        answer (Dict[str, str]): The parsed STAR answer
        output_path (str): Path to save the answer
        metadata (Dict[str, Any]): Additional metadata to include
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Combine the answer and metadata
        output_data = {
            "metadata": metadata,
            "answer": answer
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Saved STAR answer to {output_path}")
        logger.info(f"Saved STAR answer to {output_path}")
        return True
    
    except Exception as e:
        print(f"Error saving STAR answer to {output_path}: {e}")
        logger.error(f"Error saving STAR answer to {output_path}: {e}")
        return False

def generate_star_answer(
    llm_client: LLMClient,
    state_manager: StateManager,
    template_path: str,
    subprompt: Dict[str, Any],
    role_name: str,
    industry: str,
    question: str,
    output_dir: str,
    config: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Generate a STAR answer for a single sub-prompt.
    
    Args:
        llm_client (LLMClient): The LLM client to use
        state_manager (StateManager): The state manager
        template_path (str): Path to the main context prompt template
        subprompt (Dict[str, Any]): The sub-prompt to use
        role_name (str): The target role
        industry (str): The target industry
        question (str): The interview question
        output_dir (str): Directory to save the answer
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Tuple[bool, Optional[str]]: Success flag and path to the saved answer file
    """
    # Create a unique file ID for this answer
    prompt_id = subprompt.get('prompt_id', 'unknown')
    file_id = f"{role_name.replace(' ', '_')}_{prompt_id}_{industry.replace(' ', '_')}"
    
    # Check if this file has already been processed
    status = state_manager.get_file_status(file_id)
    if status == STATUS_COMPLETE:
        print(f"STAR answer for {file_id} already generated, skipping")
        logger.info(f"STAR answer for {file_id} already generated, skipping")
        return True, state_manager.get_processed_file_path(file_id)
    
    # Add to state manager with in-progress status
    state_manager.add_file(file_id, 'star_answer')
    state_manager.update_status(file_id, STATUS_IN_PROGRESS)
    
    # Load the main context prompt template
    template = load_prompt_template(template_path)
    if not template:
        print(f"Failed to load template from {template_path}")
        logger.error(f"Failed to load template from {template_path}")
        state_manager.update_status(file_id, STATUS_FAILED, error_message=f"Failed to load template from {template_path}")
        return False, None
    
    # Load role-specific skills
    role_skills = load_role_skills(role_name)
    
    # Generate parameters for this combination
    params = generate_star_answer_parameters(subprompt, role_name, industry, question)
    
    # Add role skills to parameters
    params["TARGET_ROLE_SKILLS"] = role_skills
    
    # Generate the original prompt by substituting parameters
    template_prompt = substitute_parameters(template, params)
    
    # Create a more direct and explicit prompt structure
    # This approach is based on the successful MyTest_BA_Only implementation
    explicit_prompt = f"""
    You are an experienced {role_name} with deep expertise in the {industry} industry.
    
    Create a detailed STAR (Situation, Task, Action, Result) answer for the following interview question:
    
    QUESTION: {question}
    
    ADDITIONAL GUIDANCE: 
    {subprompt.get('scenario_theme_hint', '')}
    {subprompt.get('tech_context_hint', '')}
    {subprompt.get('stakeholder_interaction_hint', '')}
    {subprompt.get('org_context_hint', '')}
    {subprompt.get('additional_considerations', '')}
    
    Your answer MUST:
    1. Follow the STAR format exactly with clear Markdown headings (# Situation, # Task, # Action, # Result)
    2. Be specific to the {role_name} position in the {industry} industry
    3. Demonstrate relevant technical knowledge and soft skills
    4. Include realistic details about teams, systems, and processes
    5. Be detailed and comprehensive (at least 400-600 words)
    6. Be formatted in Markdown with proper structure and organization
    7. Focus on skills: {subprompt.get('skill_focus', '')}
    8. Highlight soft skill: {subprompt.get('soft_skill_highlight', '')}
    
    Do not provide any explanations or notes - respond ONLY with the STAR answer in proper Markdown format.
    """
    
    # Use this explicit prompt instead of the template-based one
    prompt = explicit_prompt
    
    # Call the LLM to generate the STAR answer
    try:
        print(f"Generating STAR answer for {file_id}...")
        logger.info(f"Generating STAR answer for {file_id}...")
        
        response = llm_client.generate_response(
            prompt=prompt,
            max_tokens=config.get('step2_max_tokens', 4000),
            temperature=0.7
        )
        
        if not response:
            print(f"Failed to get response from LLM for {file_id}")
            logger.error(f"Failed to get response from LLM for {file_id}")
            state_manager.update_status(file_id, STATUS_FAILED, error_message="No response from LLM")
            return False, None
        
        # Skip parsing the STAR answer and just use the raw text
        answer = {
            "full_answer": response['text']
        }
        
        # Log a sample of the response to help with debugging
        logger.info(f"Response sample (first 200 chars): {response['text'][:200]}")
        
        # Create metadata
        metadata = {
            "role": role_name,
            "industry": industry,
            "question": question,
            "prompt_id": prompt_id,
            "skill_focus": subprompt.get('skill_focus', 'unknown'),
            "soft_skill_highlight": subprompt.get('soft_skill_highlight', 'unknown'),
            "scenario_theme_hint": subprompt.get('scenario_theme_hint', 'unknown'),
            "llm_provider": response.get('provider', 'unknown'),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Get role abbreviation from config
        role_base = role_name.split('(')[0].strip()
        role_abbr = None
        
        # Look up role abbreviation
        role_mappings = config.get('role_mappings', {})
        for mapped_role, role_info in role_mappings.items():
            if role_base == mapped_role:
                role_abbr = role_info.get('abbreviation')
                break
                
        if not role_abbr:
            # Fallback to simplified role name if no abbreviation found
            role_abbr = role_name.split(' ')[0].lower()  # Just take the first word of the role
        else:
            role_abbr = role_abbr.lower()  # Ensure lowercase for filenames
        
        # Get industry abbreviation from config
        industry_abbr = None
        industry_mappings = config.get('industry_mappings', {})
        if industry in industry_mappings:
            industry_abbr = industry_mappings[industry].get('abbreviation')
            
        if not industry_abbr:
            # Fallback to cleaned industry name if no abbreviation found
            industry_abbr = industry.replace(' / ', '_').replace(' ', '_').lower()
        else:
            industry_abbr = industry_abbr.lower()  # Ensure lowercase for filenames
        
        # Get question ID from config
        question_id = "q1"  # Default format
        for role_config in config.get('target_roles', []):
            if role_config.get('name') == role_base:
                # Check for new interview_questions format first
                interview_questions = role_config.get('interview_questions', {})
                if interview_questions:
                    # Look for a matching question text in the new format
                    for q_id, q_text in interview_questions.items():
                        if question.lower() in q_text.lower():
                            question_id = q_id.lower()
                            break
                else:
                    # Fallback to old questions format
                    questions = role_config.get('questions', [])
                    # Find the right question by matching text
                    for i, q in enumerate(questions):
                        q_text = q.get('text', '') if isinstance(q, dict) else q
                        if question.lower() in q_text.lower():
                            if isinstance(q, dict) and 'id' in q:
                                question_id = q['id'].lower()
                            else:
                                question_id = f"q{i+1}"
                            break
        
        # Extract prompt number
        prompt_number = subprompt.get('prompt_number', 1)  # Get prompt number or default to 1
        
        # Create filename using the standardized abbreviations with _star suffix
        output_file = os.path.join(
            output_dir, 
            f"{role_abbr}_{question_id}_{industry_abbr}_{prompt_number}_star.json"
        )
        
        # Also create a markdown file for direct viewing
        markdown_file = os.path.join(
            output_dir, 
            f"{role_abbr}_{question_id}_{industry_abbr}_{prompt_number}_star.md"
        )
        
        # Save the raw markdown answer to a .md file for easy viewing
        os.makedirs(os.path.dirname(markdown_file), exist_ok=True)
        try:
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(response['text'])
            logger.info(f"Saved markdown answer to {markdown_file}")
        except Exception as e:
            logger.warning(f"Failed to save markdown file: {e}")
        
        # Save the STAR answer
        if save_star_answer(answer, output_file, metadata):
            state_manager.update_status(file_id, STATUS_COMPLETE, processed_file_path=output_file)
            return True, output_file
        else:
            state_manager.update_status(file_id, STATUS_FAILED, error_message=f"Failed to save STAR answer to {output_file}")
            return False, None
        
    except Exception as e:
        print(f"Error generating STAR answer for {file_id}: {e}")
        logger.error(f"Error generating STAR answer for {file_id}: {e}")
        state_manager.update_status(file_id, STATUS_FAILED, error_message=str(e))
        return False, None

def process_star_answers(config: Dict[str, Any], state_manager: StateManager = None, llm_client: LLMClient = None, args = None) -> Dict[str, int]:
    """
    Process all sub-prompts to generate STAR answers.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        state_manager (StateManager, optional): State manager instance
        llm_client (LLMClient, optional): LLM client instance
        args (argparse.Namespace, optional): Command-line arguments
        
    Returns:
        Dict[str, int]: Statistics about the processing
    """
    print("\n" + "=" * 80)
    print("PHASE 3: STAR ANSWER GENERATION")
    print("=" * 80 + "\n")
    
    # Initialize statistics
    stats = {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0
    }
    
    # Get configuration values
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(output_dir, config.get('subprompts_dir', 'sub_prompts'))
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    
    # Create output directory
    os.makedirs(answers_dir, exist_ok=True)
    
    # Initialize state manager if not provided
    if state_manager is None:
        db_path = os.path.join(output_dir, 'processing_state.db')
        state_manager = StateManager(db_path)
    
    # Initialize LLM client if not provided
    if llm_client is None:
        llm_client = LLMClient(config)
        
    # Check if we're in resume mode
    resume_mode = args.resume if args and hasattr(args, 'resume') else False
    if resume_mode:
        print("Running in resume mode - will skip already completed files")
        logger.info("Running in resume mode - will skip already completed files")
    
    # Get the main context prompt template path
    template_path = config['prompts']['main_context']
    
    # Apply filters from both args and config if specified
    role_filter = args.role if args and hasattr(args, 'role') and args.role else config.get('role_filter', None)
    industry_filter = args.industry if args and hasattr(args, 'industry') and args.industry else config.get('industry_filter', None) 
    question_filter = args.question if args and hasattr(args, 'question') and args.question else config.get('question_filter', None)
    
    # Get all sub-prompts from state manager and manually filter for completed ones
    # This approach is needed because we need to access all files, not just pending ones
    try:
        query = "SELECT file_path, processed_file_path FROM processing_state WHERE stage = ? AND status = ?"
        state_manager.cursor.execute(query, ('sub_prompt', STATUS_COMPLETE))
        results = state_manager.cursor.fetchall()
        
        # Convert results to a list of tuples (file_id, processed_file_path)
        completed_subprompts = []
        for file_id, processed_file_path in results:
            if processed_file_path and os.path.exists(processed_file_path):
                completed_subprompts.append((file_id, processed_file_path))
            else:
                logger.warning(f"Completed sub-prompt {file_id} has no valid file path or file doesn't exist: {processed_file_path}")
                
        print(f"Found {len(completed_subprompts)} completed sub-prompts with valid files")
        logger.info(f"Found {len(completed_subprompts)} completed sub-prompts with valid files")
    except Exception as e:
        logger.error(f"Error querying database for completed sub-prompts: {e}")
        completed_subprompts = []
    
    print(f"Found {len(completed_subprompts)} completed sub-prompts to potentially process")
    logger.info(f"Found {len(completed_subprompts)} completed sub-prompts to potentially process")
    
    if not completed_subprompts:
        print("No completed sub-prompts found to process. Please generate sub-prompts first.")
        return stats
    
    # Get target roles, industries, and questions from config for reference
    target_roles = config.get('target_roles', [])
    target_industries = config.get('target_industries', [])
    target_questions = config.get('target_questions', [])
    
    # Process each completed sub-prompt
    for file_id, subprompt_file in completed_subprompts:
        # Apply filters if specified
        if role_filter and role_filter.lower() not in file_id.lower():
            logger.debug(f"Skipping {file_id} due to role filter: {role_filter}")
            continue
            
        if question_filter:
            question_part = next((part for part in file_id.split('_') if part.startswith('q') and part[1:].isdigit()), None)
            if not question_part or question_filter.lower() not in question_part.lower():
                logger.debug(f"Skipping {file_id} due to question filter: {question_filter}")
                continue
                
        if industry_filter and industry_filter.lower() not in file_id.lower():
            logger.debug(f"Skipping {file_id} due to industry filter: {industry_filter}")
            continue
        
        # Check if this file has already been processed in the star_answer stage
        if resume_mode:
            # Using direct SQL query to check if this file_id exists with stage='star_answer' and status='complete'
            try:
                query = "SELECT status FROM processing_state WHERE file_path = ? AND stage = ?"
                state_manager.cursor.execute(query, (file_id, 'star_answer'))
                result = state_manager.cursor.fetchone()
                star_answer_status = result[0] if result else None
                
                if star_answer_status == STATUS_COMPLETE:
                    logger.info(f"Skipping already completed STAR answer for {file_id} (resume mode)")
                    print(f"Skipping already completed STAR answer for {file_id} (resume mode)")
                    stats["skipped"] += 1
                    continue
            except Exception as e:
                logger.error(f"Error checking if {file_id} is already processed: {e}")
                star_answer_status = None
        
        # Parse file_id to extract role, question, and industry
        # Assuming format like "role_q1_industry"
        file_parts = file_id.split('_')
        
        # Find the question part (starts with q followed by digit)
        q_part_index = next((i for i, part in enumerate(file_parts) if part.startswith('q') and part[1:].isdigit()), -1)
        
        if q_part_index == -1:
            logger.warning(f"Could not parse question index from file_id: {file_id}, skipping")
            stats["skipped"] += 1
            continue
            
        # Extract role (everything before q*)
        role_slug = '_'.join(file_parts[:q_part_index])
        
        # Convert slug to title case for comparison with config
        base_role_parts = role_slug.split('_')
        
        # Remove potential abbreviation if it's at the end (e.g., 'product_manager_pdm')
        potential_abbr = None
        if len(base_role_parts) >= 2 and len(base_role_parts[-1]) <= 5 and base_role_parts[-1].isalpha():
            potential_abbr = base_role_parts[-1]
            base_role_parts = base_role_parts[:-1]
        
        # Convert to title case for matching with config keys
        base_role = ' '.join(part.title() for part in base_role_parts)
        
        # Look up in role_mappings from config
        role_mappings = config.get('role_mappings', {})
        role_name = None
        
        # Try to find an exact match first
        if base_role in role_mappings:
            role_info = role_mappings[base_role]
            abbr = role_info.get('abbreviation')
            role_name = f"{base_role} ({abbr})"
            logger.debug(f"Found exact role mapping match: {base_role} -> {abbr}")
        else:
            # Try partial matches
            for mapped_role, role_info in role_mappings.items():
                if base_role.startswith(mapped_role) or mapped_role.startswith(base_role):
                    abbr = role_info.get('abbreviation')
                    role_name = f"{mapped_role} ({abbr})"
                    logger.debug(f"Found partial role mapping match: {base_role} via {mapped_role} -> {abbr}")
                    break
        
        # If no match in mappings, use fallback logic
        if not role_name:
            if potential_abbr:
                role_name = f"{base_role} ({potential_abbr.upper()})"
            else:
                role_name = role_slug.replace('_', ' ').title()
        
        # Extract question number and get the actual question text
        question_part = file_parts[q_part_index]
        question_index = int(question_part[1:]) if question_part[1:].isdigit() else 1
        
        # Get the question text from config if possible
        try:
            question = target_questions[question_index-1] if target_questions else f"Question {question_index}"
        except IndexError:
            question = f"Question {question_index}"
        
        # Extract industry (everything after q*)
        industry_slug = '_'.join(file_parts[q_part_index+1:]) if q_part_index < len(file_parts) - 1 else "general"
        
        # Try to find the industry name from config if possible
        industry = None
        for ind in target_industries:
            ind_slug = ind.replace(" ", "_").replace("/", "_").lower()
            if ind_slug in industry_slug:
                industry = ind
                break
        
        if not industry:
            industry = industry_slug.replace('_', ' ').title()
        
        # Load the sub-prompts file
        subprompts = load_subprompts(subprompt_file)
        if not subprompts:
            logger.warning(f"No valid sub-prompts found in {subprompt_file}, skipping")
            print(f"No valid sub-prompts found in {subprompt_file}, skipping")
            stats["skipped"] += 1
            continue
        
        # Add entry to the state manager for the star_answer stage if not already there
        star_file_id = f"{file_id}:star_answer"  # Create compound ID with stage
        state_manager.add_file(star_file_id, 'star_answer')
        state_manager.update_status(star_file_id, STATUS_IN_PROGRESS)
        
        stats["total"] += len(subprompts)
        logger.info(f"Processing {len(subprompts)} sub-prompts for {role_name}, Question {question_index}, {industry}")
        print(f"Processing {len(subprompts)} sub-prompts for {role_name}, Question {question_index}, {industry}")
        
        # Process each sub-prompt in the file
        successes = 0
        for i, subprompt in enumerate(subprompts):
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
            
            if success:
                successes += 1
                stats["processed"] += 1
            else:
                stats["failed"] += 1
        
        # Update the status based on results
        output_dir = os.path.join(answers_dir, role_slug, question_part, industry_slug)
        if successes == len(subprompts):
            # All sub-prompts processed successfully
            star_file_id = f"{file_id}:star_answer"  # Create compound ID with stage
            state_manager.update_status(star_file_id, STATUS_COMPLETE, 
                                     processed_file_path=output_dir)
            print(f"Successfully processed all {len(subprompts)} sub-prompts for {file_id}")
        elif successes > 0:
            # Some sub-prompts processed successfully
            star_file_id = f"{file_id}:star_answer"  # Create compound ID with stage
            state_manager.update_status(star_file_id, STATUS_COMPLETE, 
                                     processed_file_path=output_dir,
                                     error_message=f"Partially successful: {successes}/{len(subprompts)} generated")
            print(f"Partially processed {successes}/{len(subprompts)} sub-prompts for {file_id}")
        else:
            # No sub-prompts processed successfully
            star_file_id = f"{file_id}:star_answer"  # Create compound ID with stage
            state_manager.update_status(star_file_id, STATUS_FAILED,
                                      error_message="Failed to generate any STAR answers")
            print(f"Failed to process any sub-prompts for {file_id}")
    
    # Print statistics
    print("\nSTAR Answer Generation Statistics:")
    print(f"Total sub-prompts: {stats['total']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    
    return stats

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    from config import load_config
    
    # Load configuration
    config = load_config('config.yaml')
    
    if config:
        # Process STAR answers
        process_star_answers(config)
    else:
        print("Failed to load configuration")
