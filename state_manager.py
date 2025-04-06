"""
State Manager Module

This module provides a SQLite-based state management system for tracking the processing
status of files throughout the STAR answer generation pipeline.
"""

import os
import sqlite3
import time
from pathlib import Path
from logger_setup import logger, setup_logging

# Define possible processing states
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_COMPLETE = 'complete'
STATUS_FAILED = 'failed'
STATUS_SKIPPED = 'skipped'

class StateManager:
    """
    Manages the state of file processing using a SQLite database.
    Provides functionality to track, update, and query the status of files
    being processed through the pipeline.
    """
    
    def __init__(self, db_path):
        """
        Initialize the StateManager with a database file path.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_table()
    
    def _connect(self):
        """Establishes connection to the SQLite database."""
        try:
            # Ensure the directory for the database exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            # Use print for initial connection since logger might not be initialized yet
            print(f"Connected to state database: {self.db_path}")
        except sqlite3.Error as e:
            # Use print for errors since logger might not be initialized yet
            print(f"Error connecting to database {self.db_path}: {e}")
            raise
    
    def _create_table(self):
        """Creates the processing_state table if it doesn't exist."""
        try:
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS processing_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,       -- Path to the original file
                status TEXT NOT NULL DEFAULT '{STATUS_PENDING}',     -- Current processing status
                processed_file_path TEXT,           -- Path to the generated file
                stage TEXT NOT NULL,                -- Processing stage (sub_prompt, star_answer, conversational)
                attempts INTEGER DEFAULT 0,           -- Number of processing attempts
                last_attempt_timestamp REAL,       -- Timestamp of the last attempt (Unix epoch)
                error_message TEXT,                 -- Details if status is 'failed'
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
            ''')
            # Add indexes for faster lookups
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON processing_state (status)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON processing_state (file_path)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage ON processing_state (stage)')
            self.conn.commit()
            # Use print since logger might not be initialized yet
            print("Table 'processing_state' ensured to exist with indexes.")
        except sqlite3.Error as e:
            # Use print since logger might not be initialized yet
            print(f"Error creating table or indexes: {e}")
            raise
    
    def add_file(self, file_path, stage):
        """
        Adds a file to the database with pending status if it doesn't exist.
        
        Args:
            file_path (str): Path to the file to add
            stage (str): Processing stage (sub_prompt, star_answer, conversational)
            
        Returns:
            int or None: ID of the added file, or None if operation failed
        """
        timestamp = time.time()
        try:
            self.cursor.execute('''
            INSERT OR IGNORE INTO processing_state (file_path, status, stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (file_path, STATUS_PENDING, stage, timestamp, timestamp))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                logger.debug(f"Added new file to state DB: {file_path} (stage: {stage})")
            return self.cursor.lastrowid or self.get_file_id(file_path)
        except sqlite3.Error as e:
            logger.error(f"Error adding file {file_path}: {e}")
            return None
    
    def get_file_status(self, file_path):
        """
        Gets the current status of a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str or None: Current status of the file, or None if not found
        """
        try:
            self.cursor.execute('SELECT status FROM processing_state WHERE file_path = ?', (file_path,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting status for file {file_path}: {e}")
            return None
    
    def get_file_id(self, file_path):
        """
        Gets the database ID of a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            int or None: ID of the file, or None if not found
        """
        try:
            self.cursor.execute('SELECT id FROM processing_state WHERE file_path = ?', (file_path,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting ID for file {file_path}: {e}")
            return None
    
    def update_status(self, file_path, status, processed_file_path=None, error_message=None, increment_attempt=True):
        """
        Updates the status and other details of a file.
        
        Args:
            file_path (str): Path to the file
            status (str): New status to set
            processed_file_path (str, optional): Path to the processed output file
            error_message (str, optional): Error message if status is failed
            increment_attempt (bool, optional): Whether to increment the attempt counter
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        timestamp = time.time()
        try:
            # Build the update query dynamically based on provided parameters
            update_fields = ['status = ?', 'updated_at = ?']
            params = [status, timestamp]
            
            if processed_file_path is not None:
                update_fields.append('processed_file_path = ?')
                params.append(processed_file_path)
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                params.append(error_message)
            
            if increment_attempt:
                update_fields.append('attempts = attempts + 1')
                update_fields.append('last_attempt_timestamp = ?')
                params.append(timestamp)
            
            # Complete the query and parameters
            query = f"UPDATE processing_state SET {', '.join(update_fields)} WHERE file_path = ?"
            params.append(file_path)
            
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.info(f"Updated status for {file_path} to {status}. Attempt incremented: {increment_attempt}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating status for {file_path} to {status}: {e}")
            return False
    
    def get_pending_files(self, stage=None, limit=None):
        """
        Gets a list of files with pending status, optionally filtered by stage.
        
        Args:
            stage (str, optional): Filter by processing stage
            limit (int, optional): Maximum number of files to return
            
        Returns:
            list: List of file paths with pending status
        """
        query = 'SELECT file_path FROM processing_state WHERE status = ?'
        params = [STATUS_PENDING]
        
        if stage:
            query += ' AND stage = ?'
            params.append(stage)
        
        query += ' ORDER BY created_at'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [row[0] for row in results]
        except sqlite3.Error as e:
            logger.error(f"Error fetching pending files: {e}")
            return []
    
    def get_files_to_retry(self, stage=None, max_attempts=3, limit=None):
        """
        Gets a list of failed files eligible for retry.
        
        Args:
            stage (str, optional): Filter by processing stage
            max_attempts (int, optional): Maximum number of attempts allowed
            limit (int, optional): Maximum number of files to return
            
        Returns:
            list: List of file paths eligible for retry
        """
        query = 'SELECT file_path FROM processing_state WHERE status = ? AND attempts < ?'
        params = [STATUS_FAILED, max_attempts]
        
        if stage:
            query += ' AND stage = ?'
            params.append(stage)
        
        query += ' ORDER BY last_attempt_timestamp'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [row[0] for row in results]
        except sqlite3.Error as e:
            logger.error(f"Error fetching files to retry: {e}")
            return []
    
    def get_summary(self, stage=None):
        """
        Returns a summary count of files by status.
        
        Args:
            stage (str, optional): Filter by processing stage
            
        Returns:
            dict: Dictionary with counts for each status
        """
        summary = {
            STATUS_PENDING: 0,
            STATUS_IN_PROGRESS: 0,
            STATUS_COMPLETE: 0,
            STATUS_FAILED: 0,
            STATUS_SKIPPED: 0
        }
        
        try:
            query = 'SELECT status, COUNT(*) FROM processing_state'
            params = []
            
            if stage:
                query += ' WHERE stage = ?'
                params.append(stage)
            
            query += ' GROUP BY status'
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            for status, count in results:
                if status in summary:
                    summary[status] = count
            
            summary['total'] = sum(summary.values())
            return summary
        except sqlite3.Error as e:
            logger.error(f"Error getting status summary: {e}")
            return None
    
    def get_processed_file_path(self, file_id):
        """
        Gets the processed file path for a given file ID.
        
        Args:
            file_id (str): The file ID to look up
            
        Returns:
            str or None: The processed file path, or None if not found
        """
        try:
            self.cursor.execute(
                'SELECT processed_file_path FROM processing_state WHERE file_path = ?',
                (file_id,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting processed file path for {file_id}: {e}")
            return None
    
    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            # Use print since logger might not be initialized yet
            print("State database connection closed.")

if __name__ == '__main__':
    # Set up logging
    setup_logging(log_level="DEBUG")
    
    # Example usage
    db_file = "test_state.db"
    state_manager = StateManager(db_file)
    
    # Add test files
    state_manager.add_file('/path/to/role1_q1.json', 'sub_prompt')
    state_manager.add_file('/path/to/role1_q2.json', 'sub_prompt')
    state_manager.add_file('/path/to/star_answer1.md', 'star_answer')
    
    # Update status
    state_manager.update_status('/path/to/role1_q1.json', STATUS_IN_PROGRESS)
    state_manager.update_status('/path/to/role1_q1.json', STATUS_COMPLETE, 
                               processed_file_path='/path/to/output1.json')
    
    state_manager.update_status('/path/to/role1_q2.json', STATUS_FAILED, 
                               error_message="API timeout")
    
    # Get pending files
    pending = state_manager.get_pending_files(stage='star_answer')
    logger.info(f"Pending star_answer files: {pending}")
    
    # Get files to retry
    retryable = state_manager.get_files_to_retry(max_attempts=3)
    logger.info(f"Retryable files (max 3 attempts): {retryable}")
    
    # Get summary
    summary = state_manager.get_summary()
    logger.info(f"Overall summary: {summary}")
    
    sub_prompt_summary = state_manager.get_summary(stage='sub_prompt')
    logger.info(f"Sub-prompt stage summary: {sub_prompt_summary}")
    
    # Close connection
    state_manager.close()
