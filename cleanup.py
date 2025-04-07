"""
Cleanup Script for STAR Answer Generator

This script cleans up generated files and resets the state database
to allow for fresh test runs.
"""

import os
import shutil
import sqlite3
import argparse
from pathlib import Path

from logger_setup import setup_logging, logger
from config import load_config

def cleanup_generated_files(config, args):
    """
    Clean up generated files based on the configuration.
    
    Args:
        config (dict): Configuration dictionary
        args (argparse.Namespace): Command-line arguments
    """
    # Get output directories from config
    base_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    subprompts_dir = os.path.join(base_dir, config.get('subprompts_dir', 'sub_prompts'))
    star_answers_dir = os.path.join(base_dir, config.get('star_answers_dir', 'star_answers'))
    conversations_dir = os.path.join(base_dir, config.get('conversations_dir', 'conversations'))
    prompt_logs_dir = os.path.join(base_dir, config.get('prompt_logs_dir', 'prompt_logs'))
    test_dir = os.path.join(base_dir, 'test')
    
    dirs_to_clean = []
    
    # Determine which directories to clean based on args
    if args.all or args.sub_prompts:
        dirs_to_clean.append(subprompts_dir)
    
    if args.all or args.star_answers:
        dirs_to_clean.append(star_answers_dir)
    
    if args.all or args.conversational:
        dirs_to_clean.append(conversations_dir)
    
    # Always clean the test directory and prompt logs if --all is specified
    if args.all:
        dirs_to_clean.append(test_dir)
        dirs_to_clean.append(prompt_logs_dir)
    
    # Clean each directory
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            logger.info(f"Cleaning directory: {directory}")
            try:
                # Remove all files in the directory
                for file_path in Path(directory).glob('*'):
                    if file_path.is_file():
                        os.remove(file_path)
                        logger.debug(f"Removed file: {file_path}")
                
                # Optionally remove the directory itself
                if args.remove_dirs:
                    shutil.rmtree(directory)
                    logger.info(f"Removed directory: {directory}")
            except Exception as e:
                logger.error(f"Error cleaning directory {directory}: {e}")
        else:
            logger.info(f"Directory does not exist, skipping: {directory}")

def reset_state_database(config, args):
    """
    Reset the state database.
    
    Args:
        config (dict): Configuration dictionary
        args (argparse.Namespace): Command-line arguments
    """
    if not args.reset_db:
        return
    
    # Get database path
    base_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    db_path = os.path.join(base_dir, 'processing_state.db')
    
    if os.path.exists(db_path):
        logger.info(f"Resetting state database: {db_path}")
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Delete all rows from each table
            for table in tables:
                table_name = table[0]
                if args.all:
                    # Delete all rows
                    cursor.execute(f"DELETE FROM {table_name};")
                    logger.debug(f"Deleted all rows from table: {table_name}")
                else:
                    # Delete rows based on stage filter
                    if args.sub_prompts:
                        cursor.execute(f"DELETE FROM {table_name} WHERE file_type = 'sub_prompt';")
                        logger.debug(f"Deleted sub_prompt rows from table: {table_name}")
                    
                    if args.star_answers:
                        cursor.execute(f"DELETE FROM {table_name} WHERE file_type = 'star_answer';")
                        logger.debug(f"Deleted star_answer rows from table: {table_name}")
                    
                    if args.conversational:
                        cursor.execute(f"DELETE FROM {table_name} WHERE file_type = 'conversations';")
                        logger.debug(f"Deleted conversations rows from table: {table_name}")
            
            # Commit changes
            conn.commit()
            conn.close()
            logger.info("State database reset successfully")
            
            # Optionally remove the database file
            if args.remove_db:
                os.remove(db_path)
                logger.info(f"Removed database file: {db_path}")
                
        except Exception as e:
            logger.error(f"Error resetting state database: {e}")
    else:
        logger.info(f"Database does not exist, skipping: {db_path}")

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Cleanup generated files and reset state')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--all', action='store_true', help='Clean all generated files and reset all state')
    parser.add_argument('--sub_prompts', action='store_true', help='Clean sub-prompts files and state')
    parser.add_argument('--star_answers', action='store_true', help='Clean STAR answers files and state')
    parser.add_argument('--conversational', action='store_true', help='Clean conversations files and state')
    parser.add_argument('--reset_db', action='store_true', help='Reset the state database')
    parser.add_argument('--remove_db', action='store_true', help='Remove the database file')
    parser.add_argument('--remove_dirs', action='store_true', help='Remove directories, not just files')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Load configuration
    config = load_config(args.config)
    
    if not config:
        logger.critical("Failed to load configuration. Exiting.")
        exit(1)
    
    # Clean up generated files
    cleanup_generated_files(config, args)
    
    # Reset state database
    reset_state_database(config, args)
    
    logger.info("Cleanup completed successfully")

if __name__ == "__main__":
    main()
