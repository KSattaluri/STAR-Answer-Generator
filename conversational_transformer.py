"""
Conversational Transformer

This module handles Phase 4 of the STAR Answer Generation System:
1. Loads STAR answers generated in Phase 3
2. Uses the conversational prompt template to transform them into natural dialogue
3. Saves the generated conversational responses to files

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
from prompt_processor import load_prompt_template, substitute_parameters

# Print statements alongside logger calls for critical operations
print("Initializing Conversational Transformer module")
logger.info("Initializing Conversational Transformer module")

def load_star_answer(star_answer_file_path: str) -> Dict[str, Any]:
    """
    Load a STAR answer from a JSON file.
    
    Args:
        star_answer_file_path (str): Path to the STAR answer JSON file
        
    Returns:
        Dict[str, Any]: The STAR answer with metadata, or empty dict if loading failed
    """
    try:
        with open(star_answer_file_path, 'r', encoding='utf-8') as f:
            star_answer = json.load(f)
        
        print(f"Loaded STAR answer from {star_answer_file_path}")
        logger.info(f"Loaded STAR answer from {star_answer_file_path}")
        return star_answer
    except FileNotFoundError:
        print(f"STAR answer file not found: {star_answer_file_path}")
        logger.error(f"STAR answer file not found: {star_answer_file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing STAR answer file {star_answer_file_path}: {e}")
        logger.error(f"Error parsing STAR answer file {star_answer_file_path}: {e}")
        return {}
    except Exception as e:
        print(f"Error loading STAR answer from {star_answer_file_path}: {e}")
        logger.error(f"Error loading STAR answer from {star_answer_file_path}: {e}")
        return {}

def generate_conversational_parameters(star_answer: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate parameters for the conversational prompt template.
    
    Args:
        star_answer (Dict[str, Any]): The STAR answer with metadata
        
    Returns:
        Dict[str, str]: Parameters for the prompt template
    """
    # Extract metadata
    metadata = star_answer.get('metadata', {})
    role_name = metadata.get('role', 'Unknown Role')
    industry = metadata.get('industry', 'Unknown Industry')
    question = metadata.get('question', 'Unknown Question')
    
    # Extract STAR sections
    answer = star_answer.get('answer', {})
    situation = answer.get('situation', '')
    task = answer.get('task', '')
    action = answer.get('action', '')
    result = answer.get('result', '')
    
    # Create parameters dictionary with placeholders that match the template
    params = {
        "ROLE": role_name,
        "INDUSTRY": industry,
        "QUESTION": question,
        "STAR_ANSWER": answer.get('full_answer', '')
    }
    
    # Add debug logging
    print(f"Generated parameters for conversational prompt:") 
    print(f"  ROLE: {role_name[:30]}...")
    print(f"  INDUSTRY: {industry}")
    print(f"  QUESTION: {question}")
    print(f"  STAR_ANSWER length: {len(answer.get('full_answer', ''))} characters")
    logger.info(f"Generated parameters for conversational prompt: ROLE={role_name}, INDUSTRY={industry}, QUESTION={question}")
    
    return params

def parse_conversational_response(response_text: str) -> Dict[str, str]:
    """
    Parse the conversational response from the LLM.
    
    Args:
        response_text (str): The raw response from the LLM
        
    Returns:
        Dict[str, str]: Parsed conversational response
    """
    # Initialize the result dictionary
    result = {
        "interviewer_question": "",
        "candidate_answer": "",
        "follow_up_question": "",
        "follow_up_answer": "",
        "full_conversation": response_text
    }
    
    # Try to extract the conversation parts
    try:
        # Look for Interviewer and Candidate parts
        lines = response_text.split('\n')
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for speaker changes
            if line.startswith("Interviewer:"):
                # If we were collecting text for a previous speaker, save it
                if current_speaker == "Interviewer" and current_text:
                    if not result["interviewer_question"]:
                        result["interviewer_question"] = "\n".join(current_text)
                    elif not result["follow_up_question"]:
                        result["follow_up_question"] = "\n".join(current_text)
                
                # Start collecting for the interviewer
                current_speaker = "Interviewer"
                current_text = [line[len("Interviewer:"):].strip()]
            
            elif line.startswith("Candidate:"):
                # If we were collecting text for a previous speaker, save it
                if current_speaker == "Candidate" and current_text:
                    if not result["candidate_answer"]:
                        result["candidate_answer"] = "\n".join(current_text)
                    elif not result["follow_up_answer"]:
                        result["follow_up_answer"] = "\n".join(current_text)
                
                # Start collecting for the candidate
                current_speaker = "Candidate"
                current_text = [line[len("Candidate:"):].strip()]
            
            else:
                # Continue collecting for the current speaker
                if current_speaker:
                    current_text.append(line)
        
        # Save any remaining text
        if current_speaker == "Interviewer" and current_text:
            if not result["interviewer_question"]:
                result["interviewer_question"] = "\n".join(current_text)
            elif not result["follow_up_question"]:
                result["follow_up_question"] = "\n".join(current_text)
        
        elif current_speaker == "Candidate" and current_text:
            if not result["candidate_answer"]:
                result["candidate_answer"] = "\n".join(current_text)
            elif not result["follow_up_answer"]:
                result["follow_up_answer"] = "\n".join(current_text)
    
    except Exception as e:
        print(f"Error parsing conversational response: {e}")
        logger.error(f"Error parsing conversational response: {e}")
    
    return result

def save_conversational_response(
    response: Dict[str, str], 
    output_path: str, 
    metadata: Dict[str, Any]
) -> bool:
    """
    Save the generated conversational response to a JSON file.
    
    Args:
        response (Dict[str, str]): The parsed conversational response
        output_path (str): Path to save the response
        metadata (Dict[str, Any]): Additional metadata to include
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Combine the response and metadata
        output_data = {
            "metadata": metadata,
            "conversation": response
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Saved conversational response to {output_path}")
        logger.info(f"Saved conversational response to {output_path}")
        return True
    
    except Exception as e:
        print(f"Error saving conversational response to {output_path}: {e}")
        logger.error(f"Error saving conversational response to {output_path}: {e}")
        return False

def generate_conversation(
    llm_client: LLMClient,
    state_manager: StateManager,
    template_path: str,
    star_answer_path: str,
    output_dir: str,
    config: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Generate a conversational response for a single STAR answer.
    
    Args:
        llm_client (LLMClient): The LLM client to use
        state_manager (StateManager): The state manager
        template_path (str): Path to the conversational prompt template
        star_answer_path (str): Path to the STAR answer JSON file
        output_dir (str): Directory to save the response
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Tuple[bool, Optional[str]]: Success flag and path to the saved response file
    """
    # Create a unique file ID for this conversation that matches the state database entry
    # Extract information from the filename to construct the same ID used in previous stages
    filename = os.path.basename(star_answer_path)
    file_base = os.path.splitext(filename)[0]  # Remove .json extension
    
    print(f"Processing STAR answer file: {filename}")
    logger.info(f"Processing STAR answer file: {filename}")
    
    # First, load the STAR answer to get the metadata
    try:
        with open(star_answer_path, 'r', encoding='utf-8') as f:
            star_data = json.load(f)
            
        metadata = star_data.get('metadata', {})
        role_name = metadata.get('role', '')
        industry = metadata.get('industry', '')
        question = metadata.get('question', 'Question 1')
        prompt_id = metadata.get('prompt_id', 'unknown')
        
        # Print metadata for debugging
        print(f"Metadata: Role={role_name}, Industry={industry}, Question={question}, Prompt ID={prompt_id}")
        logger.info(f"Metadata: Role={role_name}, Industry={industry}, Question={question}, Prompt ID={prompt_id}")
        
        # Extract key components directly from the filename since that's what we used in star_answer_generator.py
        # The filename format from star_answer_generator is: role_slug_q{question_number}_{prompt_number}.json
        
        # Create the conversation file ID by appending "_conv" to the star answer file ID
        # This ensures a unique ID while maintaining the relationship to the source file
        conversation_id = f"{file_base}_conv"
        
        print(f"Using conversation ID: {conversation_id}")
        logger.info(f"Using conversation ID: {conversation_id}")
    except Exception as e:
        # Fallback to using the filename if there's an error
        print(f"Error reading STAR answer metadata: {e}, using filename instead")
        logger.error(f"Error reading STAR answer metadata: {e}, using filename instead")
        conversation_id = f"{file_base}_conv"
    
    # Check if this file has already been processed
    status = state_manager.get_file_status(conversation_id)
    print(f"Status for {conversation_id}: {status}")
    logger.info(f"Status for {conversation_id}: {status}")
    
    # Add more detailed logging about the state check
    print(f"===== STATUS CHECK: Looking for conversation ID '{conversation_id}' in database =====")
    
    # Only force reprocessing if explicitly configured
    # Default to not reprocessing files that are already marked as complete
    force_processing = False
    
    if status == STATUS_COMPLETE and not force_processing:
        print(f"Conversational response for {conversation_id} already generated, skipping")
        logger.info(f"Conversational response for {conversation_id} already generated, skipping")
        return True, state_manager.get_processed_file_path(conversation_id)
    
    # Add to state manager with in-progress status
    state_manager.add_file(conversation_id, 'conversation')
    state_manager.update_status(conversation_id, STATUS_IN_PROGRESS)
    
    # Load the STAR answer
    star_answer = load_star_answer(star_answer_path)
    if not star_answer:
        print(f"Failed to load STAR answer from {star_answer_path}")
        logger.error(f"Failed to load STAR answer from {star_answer_path}")
        state_manager.update_status(conversation_id, STATUS_FAILED, error_message=f"Failed to load STAR answer from {star_answer_path}")
        return False, None
    
    # Load the conversational prompt template
    template = load_prompt_template(template_path)
    if not template:
        print(f"Failed to load template from {template_path}")
        logger.error(f"Failed to load template from {template_path}")
        state_manager.update_status(conversation_id, STATUS_FAILED, error_message=f"Failed to load template from {template_path}")
        return False, None
    
    # Generate parameters for this STAR answer
    params = generate_conversational_parameters(star_answer)
    
    # Add STAR_ANSWER_FILE parameter explicitly to help with prompt logging
    params['STAR_ANSWER_FILE'] = os.path.basename(star_answer_path)
    
    # Generate the prompt by substituting parameters with config for logging
    prompt = substitute_parameters(template, params, stage_name='conversational', config=config)
    
    # Call the LLM to generate the conversational response
    try:
        print(f"Generating conversational response for {conversation_id}...")
        logger.info(f"Generating conversational response for {conversation_id}...")
        
        response = llm_client.generate_response(
            prompt=prompt,
            max_tokens=config.get('step3_max_tokens', 4000),
            temperature=0.7
        )
        
        if not response:
            print(f"Failed to get response from LLM for {conversation_id}")
            logger.error(f"Failed to get response from LLM for {conversation_id}")
            state_manager.update_status(conversation_id, STATUS_FAILED, error_message="No response from LLM")
            return False, None
        
        # Parse the conversational response
        conversation = parse_conversational_response(response['text'])
        
        # Create metadata
        metadata = star_answer.get('metadata', {}).copy()
        metadata.update({
            "conversation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_llm_provider": response.get('provider', 'unknown')
        })
        
        # Create the output file path with a clear folder structure
        filename = os.path.basename(star_answer_path)
        filename_no_ext = os.path.splitext(filename)[0]
        
        # Create a more organized folder structure
        role_dir = metadata.get('role', 'unknown').split(' ')[0].lower()  # Just use first word of role
        industry_dir = metadata.get('industry', 'unknown').replace(' ', '_').replace('/', '_').lower()
        
        # Create subdirectories for better organization
        output_subdir = os.path.join(output_dir, role_dir, industry_dir)
        os.makedirs(output_subdir, exist_ok=True)
        
        # Use same base filename but in the conversational directory
        output_file = os.path.join(output_subdir, f"{filename_no_ext}_conversation.json")
        
        print(f"Will save conversation to: {output_file}")
        logger.info(f"Will save conversation to: {output_file}")
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Also create a markdown file for direct viewing
        markdown_file = os.path.join(
            os.path.dirname(output_file),
            f"{os.path.splitext(os.path.basename(output_file))[0]}.md"
        )
        
        # Save the raw conversation to a .md file for easy viewing
        try:
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(conversation['full_conversation'])
            logger.info(f"Saved markdown conversation to {markdown_file}")
            print(f"Saved markdown conversation to {markdown_file}")
        except Exception as e:
            logger.warning(f"Failed to save markdown conversation: {e}")
            print(f"Failed to save markdown conversation: {e}")
        
        # Save the conversational response
        if save_conversational_response(conversation, output_file, metadata):
            state_manager.update_status(conversation_id, STATUS_COMPLETE, processed_file_path=output_file)
            print(f"Successfully saved conversation to {output_file}")
            logger.info(f"Successfully saved conversation to {output_file}")
            return True, output_file
        else:
            state_manager.update_status(conversation_id, STATUS_FAILED, error_message=f"Failed to save conversational response to {output_file}")
            print(f"Failed to save conversation to {output_file}")
            logger.error(f"Failed to save conversation to {output_file}")
            return False, None
        
    except Exception as e:
        print(f"Error generating conversational response for {conversation_id}: {e}")
        logger.error(f"Error generating conversational response for {conversation_id}: {e}")
        state_manager.update_status(conversation_id, STATUS_FAILED, error_message=str(e))
        return False, None

def process_conversations(config: Dict[str, Any]) -> Dict[str, int]:
    """
    Process all STAR answers to generate conversational responses.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, int]: Statistics about the processing
    """
    print("\n" + "=" * 80)
    print("PHASE 4: CONVERSATIONAL TRANSFORMATION")
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
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    conversations_dir = os.path.join(output_dir, config.get('conversations_dir', 'conversations'))
    
    # Create output directory
    os.makedirs(conversations_dir, exist_ok=True)
    
    # Initialize state manager
    db_path = os.path.join(output_dir, 'processing_state.db')
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Get the conversational prompt template path
    template_path = config['prompts'].get('conversation_prompt', config.get('conversation_prompt_path', 'prompt_templates/stage3_conversational_transformer.md'))
    
    # Apply filters if specified
    role_filter = config.get('role_filter', None)
    industry_filter = config.get('industry_filter', None)
    question_filter = config.get('question_filter', None)
    
    # Find all STAR answer files
    star_answer_files = list(Path(answers_dir).glob("*.json"))
    
    # Filter files if needed
    if role_filter or industry_filter or question_filter:
        filtered_files = []
        
        for file_path in star_answer_files:
            # Load the file to check metadata
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                role = metadata.get('role', '')
                industry = metadata.get('industry', '')
                question = metadata.get('question', '')
                
                # Apply filters
                if role_filter and role_filter.lower() not in role.lower():
                    continue
                    
                if industry_filter and industry_filter.lower() not in industry.lower():
                    continue
                    
                if question_filter and question_filter.lower() not in question.lower():
                    continue
                
                # All filters passed
                filtered_files.append(file_path)
                
            except Exception as e:
                print(f"Error reading file {file_path} for filtering: {e}")
                logger.error(f"Error reading file {file_path} for filtering: {e}")
        
        star_answer_files = filtered_files
        
        print(f"Applied filters: {len(star_answer_files)} files remaining")
    
    # Process each STAR answer file
    for star_answer_path in star_answer_files:
        stats["total"] += 1
        
        # Generate the conversational response
        success, output_file = generate_conversation(
            llm_client=llm_client,
            state_manager=state_manager,
            template_path=template_path,
            star_answer_path=str(star_answer_path),
            output_dir=conversations_dir,
            config=config
        )
        
        if success:
            stats["processed"] += 1
        else:
            stats["failed"] += 1
    
    # Don't close the state manager here, it will be closed by the main script
    # state_manager.close()
    
    # Print statistics
    print("\nConversational Transformation Statistics:")
    print(f"Total STAR answers: {stats['total']}")
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
        # Process conversational transformations
        process_conversations(config)
    else:
        print("Failed to load configuration")
