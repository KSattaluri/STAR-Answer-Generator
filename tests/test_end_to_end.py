"""
End-to-End Test Script for STAR Answer Generator

This script tests the complete pipeline of the STAR Answer Generator system:
1. Phase 2: Sub-Prompt Generation
2. Phase 3: STAR Answer Generation
3. Phase 4: Conversational Transformation

The test uses a limited scope (single role, question, and industry) to minimize API costs
while still verifying that all components work together correctly.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from config import load_config
from logger_setup import setup_logging, logger
from state_manager import StateManager, STATUS_COMPLETE
from llm_client import LLMClient

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='End-to-End Test for STAR Answer Generator')
    
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    
    parser.add_argument('--role', type=str, default='Technical Delivery Manager',
                        help='Role to test with')
    
    parser.add_argument('--industry', type=str, default='Finance / Financial Services',
                        help='Industry to test with')
    
    parser.add_argument('--question', type=str, 
                        default='Talk about a time when you went above and beyond your role to accomplish a goal.',
                        help='Question to test with')
    
    parser.add_argument('--clean', action='store_true',
                        help='Clean existing output files before running')
    
    parser.add_argument('--log-level', type=str, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Set logging level')
    
    return parser.parse_args()

def setup_test_environment(config, args):
    """Set up the test environment."""
    print("\nSetting up test environment...")
    
    # Create output directories
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(output_dir, config.get('subprompts_dir', 'sub_prompts'))
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    conversations_dir = os.path.join(output_dir, config.get('conversations_dir', 'conversations'))
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(subprompts_dir, exist_ok=True)
    os.makedirs(answers_dir, exist_ok=True)
    os.makedirs(conversations_dir, exist_ok=True)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Set up logging
    setup_logging(
        log_level=args.log_level,
        log_dir='logs',
        log_to_console=True,
        log_to_file=True
    )
    
    # Initialize state manager
    db_path = os.path.join(output_dir, 'test_e2e_state.db')
    
    # Clean existing state database if requested
    if args.clean and os.path.exists(db_path):
        os.remove(db_path)
        print(f"  ✓ Removed existing state database: {db_path}")
    
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Clean existing output files if requested
    if args.clean:
        # Create file patterns based on role, industry, and question
        role_slug = args.role.replace(" ", "_").replace("(", "").replace(")", "").lower()
        industry_slug = args.industry.replace(" ", "_").replace("/", "_").lower()
        question_slug = "q1"  # We're only testing with one question
        
        # Clean sub-prompts
        subprompt_pattern = f"{role_slug}_{question_slug}_{industry_slug}_*.json"
        for file_path in Path(subprompts_dir).glob(subprompt_pattern):
            os.remove(file_path)
            print(f"  ✓ Removed existing sub-prompt file: {file_path}")
        
        # Clean STAR answers
        star_pattern = f"{role_slug}_{question_slug}_{industry_slug}_*.json"
        for file_path in Path(answers_dir).glob(star_pattern):
            os.remove(file_path)
            print(f"  ✓ Removed existing STAR answer file: {file_path}")
        
        # Clean conversations
        conv_pattern = f"{role_slug}_{question_slug}_{industry_slug}_*.json"
        for file_path in Path(conversations_dir).glob(conv_pattern):
            os.remove(file_path)
            print(f"  ✓ Removed existing conversation file: {file_path}")
    
    return state_manager, llm_client

def run_phase2(config, state_manager, llm_client, args):
    """Run Phase 2: Sub-Prompt Generation."""
    print("\n" + "=" * 80)
    print("PHASE 2: SUB-PROMPT GENERATION")
    print("=" * 80)
    
    # Import the subprompt_generator module
    from subprompt_generator import generate_subprompts
    
    # Create a test config with only the specified role, industry, and question
    test_config = config.copy()
    test_config['target_roles'] = [args.role]
    test_config['target_industries'] = [args.industry]
    test_config['target_questions'] = [args.question]
    test_config['num_prompts_per_combination'] = 1  # Just generate one sub-prompt for testing
    
    # Generate sub-prompts
    start_time = time.time()
    result = generate_subprompts(test_config, state_manager, llm_client, args)
    elapsed_time = time.time() - start_time
    
    print(f"\nPhase 2 completed in {elapsed_time:.2f} seconds")
    print(f"Result: {'Success' if result else 'Failure'}")
    
    # Return the first sub-prompt file
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(output_dir, config.get('subprompts_dir', 'sub_prompts'))
    
    role_slug = args.role.replace(" ", "_").replace("(", "").replace(")", "").lower()
    industry_slug = args.industry.replace(" ", "_").replace("/", "_").lower()
    question_slug = "q1"  # We're only testing with one question
    
    subprompt_file = os.path.join(
        subprompts_dir, 
        f"{role_slug}_{question_slug}_{industry_slug}_subprompts.json"
    )
    
    if os.path.exists(subprompt_file):
        print(f"  ✓ Sub-prompt file generated: {subprompt_file}")
        
        # Display the first sub-prompt
        try:
            with open(subprompt_file, 'r', encoding='utf-8') as f:
                subprompts = json.load(f)
            
            if subprompts:
                print("\nFirst sub-prompt:")
                print(f"  Prompt ID: {subprompts[0].get('prompt_id', 'N/A')}")
                print(f"  Skill focus: {subprompts[0].get('skill_focus', 'N/A')}")
                print(f"  Soft skill highlight: {subprompts[0].get('soft_skill_highlight', 'N/A')}")
                print(f"  Scenario theme: {subprompts[0].get('scenario_theme_hint', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Error reading sub-prompt file: {e}")
    else:
        print(f"  ✗ Sub-prompt file not generated: {subprompt_file}")
    
    return result, subprompt_file

def run_phase3(config, state_manager, llm_client, args, subprompt_file):
    """Run Phase 3: STAR Answer Generation."""
    print("\n" + "=" * 80)
    print("PHASE 3: STAR ANSWER GENERATION")
    print("=" * 80)
    
    # Import the star_answer_generator module
    from star_answer_generator import process_star_answers
    
    # Create a test config with only the specified role, industry, and question
    test_config = config.copy()
    test_config['target_roles'] = [args.role]
    test_config['target_industries'] = [args.industry]
    test_config['target_questions'] = [args.question]
    
    # Generate STAR answers
    start_time = time.time()
    result = process_star_answers(test_config)
    elapsed_time = time.time() - start_time
    
    print(f"\nPhase 3 completed in {elapsed_time:.2f} seconds")
    print(f"Result: {result}")
    
    # Find the generated STAR answer file
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    
    # List all STAR answer files
    star_answer_files = list(Path(answers_dir).glob("*.json"))
    
    if star_answer_files:
        print(f"  ✓ Found {len(star_answer_files)} STAR answer files")
        star_answer_file = star_answer_files[0]
        print(f"  ✓ Using STAR answer file: {star_answer_file}")
        
        # Display the STAR answer
        try:
            with open(star_answer_file, 'r', encoding='utf-8') as f:
                star_answer = json.load(f)
            
            metadata = star_answer.get('metadata', {})
            answer = star_answer.get('answer', {})
            
            print("\nSTAR Answer:")
            print(f"  Role: {metadata.get('role', 'N/A')}")
            print(f"  Industry: {metadata.get('industry', 'N/A')}")
            print(f"  Question: {metadata.get('question', 'N/A')}")
            print("\nSituation (excerpt):")
            print(f"  {answer.get('situation', 'N/A')[:150]}...")
        except Exception as e:
            print(f"  ✗ Error reading STAR answer file: {e}")
            star_answer_file = None
    else:
        print(f"  ✗ No STAR answer files found in {answers_dir}")
        star_answer_file = None
    
    return result.get('processed', 0) > 0, star_answer_file

def run_phase4(config, state_manager, llm_client, args, star_answer_file):
    """Run Phase 4: Conversational Transformation."""
    print("\n" + "=" * 80)
    print("PHASE 4: CONVERSATIONAL TRANSFORMATION")
    print("=" * 80)
    
    # Import the conversational_transformer module
    from conversational_transformer import process_conversations
    
    # Create a test config with only the specified role, industry, and question
    test_config = config.copy()
    test_config['target_roles'] = [args.role]
    test_config['target_industries'] = [args.industry]
    test_config['target_questions'] = [args.question]
    
    # Make sure the config has the correct key for the conversation prompt template
    if 'prompts' in test_config and 'conversation_prompt' not in test_config['prompts']:
        if 'conversation_prompt_path' in test_config:
            if 'prompts' not in test_config:
                test_config['prompts'] = {}
            test_config['prompts']['conversation_prompt'] = test_config['conversation_prompt_path']
    
    # Generate conversational responses
    start_time = time.time()
    result = process_conversations(test_config)
    elapsed_time = time.time() - start_time
    
    print(f"\nPhase 4 completed in {elapsed_time:.2f} seconds")
    print(f"Result: {result}")
    
    # Find the generated conversation file
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    conversations_dir = os.path.join(output_dir, config.get('conversations_dir', 'conversations'))
    
    # List all conversation files
    conversation_files = list(Path(conversations_dir).glob("*.json"))
    
    if conversation_files:
        print(f"  ✓ Found {len(conversation_files)} conversation files")
        conversation_file = conversation_files[0]
        print(f"  ✓ Using conversation file: {conversation_file}")
        
        # Display the conversation
        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            metadata = conversation_data.get('metadata', {})
            conversation = conversation_data.get('conversation', {})
            
            print("\nConversation:")
            print(f"  Role: {metadata.get('role', 'N/A')}")
            print(f"  Industry: {metadata.get('industry', 'N/A')}")
            print(f"  Question: {metadata.get('question', 'N/A')}")
            print("\nInterviewer Question (excerpt):")
            print(f"  {conversation.get('interviewer_question', 'N/A')[:150]}...")
            print("\nCandidate Answer (excerpt):")
            print(f"  {conversation.get('candidate_answer', 'N/A')[:150]}...")
        except Exception as e:
            print(f"  ✗ Error reading conversation file: {e}")
    else:
        print(f"  ✗ No conversation files found in {conversations_dir}")
    
    return result.get('processed', 0) > 0

def main():
    """Main entry point for the end-to-end test."""
    print("\n" + "=" * 80)
    print("END-TO-END TEST: STAR ANSWER GENERATOR")
    print("=" * 80)
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        print("Failed to load configuration. Exiting.")
        return 1
    
    print(f"Testing with:")
    print(f"  Role: {args.role}")
    print(f"  Industry: {args.industry}")
    print(f"  Question: {args.question}")
    
    # Set up test environment
    state_manager, llm_client = setup_test_environment(config, args)
    
    try:
        # Run Phase 2: Sub-Prompt Generation
        phase2_success, subprompt_file = run_phase2(config, state_manager, llm_client, args)
        
        # Run Phase 3: STAR Answer Generation (if Phase 2 succeeded)
        if phase2_success:
            phase3_success, star_answer_file = run_phase3(config, state_manager, llm_client, args, subprompt_file)
        else:
            print("\nSkipping Phase 3 due to Phase 2 failure")
            phase3_success = False
            star_answer_file = None
        
        # Run Phase 4: Conversational Transformation (if Phase 3 succeeded)
        if phase3_success:
            phase4_success = run_phase4(config, state_manager, llm_client, args, star_answer_file)
        else:
            print("\nSkipping Phase 4 due to Phase 3 failure")
            phase4_success = False
        
        # Print overall test results
        print("\n" + "=" * 80)
        print("END-TO-END TEST RESULTS")
        print("=" * 80)
        print(f"Phase 2 (Sub-Prompt Generation): {'✓ Success' if phase2_success else '✗ Failure'}")
        print(f"Phase 3 (STAR Answer Generation): {'✓ Success' if phase3_success else '✗ Failure'}")
        print(f"Phase 4 (Conversational Transformation): {'✓ Success' if phase4_success else '✗ Failure'}")
        print("\nOverall Test Result: {'✓ Success' if phase2_success and phase3_success and phase4_success else '✗ Failure'}")
        
        # Return success/failure
        return 0 if phase2_success and phase3_success and phase4_success else 1
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up resources
        state_manager.close()
        print("\nTest completed. Resources cleaned up.")

if __name__ == "__main__":
    sys.exit(main())
