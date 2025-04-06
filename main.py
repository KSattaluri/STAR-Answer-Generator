"""
STAR Answer Generation System - Main Application

This is the main entry point for the STAR Answer Generation System, which orchestrates
the entire process of generating STAR-format answers and converting them to conversational format.
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Import project modules
from config import load_config
from logger_setup import setup_logging, logger
from state_manager import StateManager
from llm_client import LLMClient

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='STAR Answer Generation System')
    
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    
    parser.add_argument('--stage', type=str, choices=['all', 'sub_prompts', 'star_answers', 'conversational'],
                        default='all', help='Processing stage to run')
    
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last successful point')
    
    parser.add_argument('--role', type=str,
                        help='Process only a specific role')
    
    parser.add_argument('--question', type=str,
                        help='Process only a specific question')
    
    parser.add_argument('--industry', type=str,
                        help='Process only a specific industry')
    
    parser.add_argument('--log-level', type=str, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set logging level')
    
    return parser.parse_args()

def setup_directories(config):
    """Create necessary directories for output files."""
    # Base output directory
    base_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    os.makedirs(base_dir, exist_ok=True)
    
    # Sub-prompts directory
    subprompts_dir = os.path.join(base_dir, config.get('subprompts_dir', 'sub_prompts'))
    os.makedirs(subprompts_dir, exist_ok=True)
    
    # Star answers directory
    star_answers_dir = os.path.join(base_dir, config.get('star_answers_dir', 'star_answers'))
    os.makedirs(star_answers_dir, exist_ok=True)
    
    # Conversational directory creation has been removed as it's not being used
    # conversational_dir = os.path.join(base_dir, config.get('conversational_dir', 'conversational'))
    # os.makedirs(conversational_dir, exist_ok=True)
    
    # Logs directory
    os.makedirs('logs', exist_ok=True)

def initialize_system(args):
    """Initialize the system components based on configuration."""
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.critical("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Override log level if specified in command line
    log_level = args.log_level or config.get('log_level', 'INFO')
    
    # Set up logging
    setup_logging(
        log_level=log_level,
        log_dir=os.path.dirname(config.get('log_file_path', 'logs/star_generator.log')),
        log_to_console=True,
        log_to_file=config.get('log_to_file', True)
    )
    
    # Create necessary directories
    setup_directories(config)
    
    # Initialize state manager
    db_path = os.path.join(
        config.get('output', {}).get('base_dir', 'generated_answers'),
        config.get('output', {}).get('state_db', 'processing_state.db')
    )
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    return config, state_manager, llm_client

def process_sub_prompts(config, state_manager, llm_client, args):
    """
    Process Stage 1: Generate sub-prompts for each role/question/industry combination.
    """
    print("Stage 1: Sub-prompt generation")
    
    # Import the subprompt_generator module
    from subprompt_generator import generate_subprompts
    
    # Generate sub-prompts
    success = generate_subprompts(config, state_manager, llm_client, args)
    
    return success

def process_star_answers(config, state_manager, llm_client, args):
    """
    Process Stage 2: Generate STAR-format answers based on sub-prompts.
    """
    print("Stage 2: STAR answer generation")
    
    # Import the star_answer_generator module
    from star_answer_generator import process_star_answers as generate_answers
    
    # Generate STAR answers
    success = generate_answers(config, state_manager, llm_client, args)
    
    # Check if any STAR answers were successfully generated
    if success.get('processed', 0) > 0:
        return True
    elif success.get('total', 0) > 0:
        logger.warning(f"Failed to generate any STAR answers. {success.get('failed', 0)} failed, {success.get('skipped', 0)} skipped.")
        return False
    else:
        logger.info("No STAR answers to generate.")
        return True

def process_conversational(config, state_manager, llm_client, args):
    """
    Process Stage 3: Transform STAR answers into conversational format.
    """
    print("Stage 3: Conversational transformation")
    
    # Import the conversational_transformer module
    from conversational_transformer import process_conversations as transform_conversations
    
    # Transform STAR answers to conversational format
    success = transform_conversations(config)
    
    # Check if any conversational responses were successfully generated
    if success.get('processed', 0) > 0:
        return True
    elif success.get('total', 0) > 0:
        logger.warning(f"Failed to generate any conversational responses. {success.get('failed', 0)} failed, {success.get('skipped', 0)} skipped.")
        return False
    else:
        logger.info("No STAR answers to transform.")
        return True

def main():
    """Main application entry point."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration first
    config = load_config(args.config)
    if not config:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)
        
    # Set up logging early
    log_level = args.log_level or config.get('log_level', 'INFO')
    setup_logging(
        log_level=log_level,
        log_dir=os.path.dirname(config.get('log_file_path', 'logs/star_generator.log')),
        log_to_console=True,
        log_to_file=config.get('log_to_file', True)
    )
    
    # Create necessary directories
    setup_directories(config)
    
    # Initialize state manager
    db_path = os.path.join(
        config.get('output', {}).get('base_dir', 'generated_answers'),
        config.get('output', {}).get('state_db', 'processing_state.db')
    )
    state_manager = StateManager(db_path)
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Display initialization information
    print("STAR Answer Generation System initialized")
    print(f"Running stage: {args.stage}")
    if args.resume:
        print("Resuming from last successful point")
    
    # Apply filters if specified
    filters = []
    if args.role:
        filters.append(f"role={args.role}")
    if args.question:
        filters.append(f"question={args.question}")
    if args.industry:
        filters.append(f"industry={args.industry}")
    
    if filters:
        print(f"Applying filters: {', '.join(filters)}")
    
    try:
        # Process stages based on command-line argument
        start_time = time.time()
        
        # Track success of each stage
        stage_success = True
        
        if args.stage in ['all', 'sub_prompts']:
            sub_prompts_success = process_sub_prompts(config, state_manager, llm_client, args)
            stage_success = stage_success and sub_prompts_success
            
            # If processing all stages and sub_prompts failed, don't proceed to next stages
            if args.stage == 'all' and not sub_prompts_success:
                logger.warning("Skipping subsequent stages due to errors in sub-prompt generation")
                stage_success = False
            
        if stage_success and args.stage in ['all', 'star_answers']:
            star_answers_success = process_star_answers(config, state_manager, llm_client, args)
            stage_success = stage_success and star_answers_success
            
            # If processing all stages and star_answers failed, don't proceed to next stage
            if args.stage == 'all' and not star_answers_success:
                logger.warning("Skipping conversational stage due to errors in STAR answer generation")
                stage_success = False
        
        if stage_success and args.stage in ['all', 'conversational']:
            conversational_success = process_conversational(config, state_manager, llm_client, args)
        
        # Display completion information
        elapsed_time = time.time() - start_time
        print(f"Processing completed in {elapsed_time:.2f} seconds")
        
        # Display processing summary
        if args.stage == 'all':
            print("Overall processing summary:")
            summary = state_manager.get_summary()
            if summary:
                for status, count in summary.items():
                    if status != 'total':
                        print(f"  {status}: {count}")
                print(f"  Total: {summary.get('total', 0)}")
        
    except KeyboardInterrupt:
        print("Processing interrupted by user")
    except Exception as e:
        print(f"An error occurred during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up resources
        state_manager.close()
        print("STAR Answer Generation System shutdown complete")

if __name__ == "__main__":
    main()
