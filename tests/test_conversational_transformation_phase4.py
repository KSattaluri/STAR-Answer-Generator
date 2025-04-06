"""
Test Script for Phase 4 (Conversational Transformation)

This script tests the conversational transformation functionality with minimal dependencies.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("\n" + "=" * 80)
    print("TESTING PHASE 4: CONVERSATIONAL TRANSFORMATION")
    print("=" * 80 + "\n")
    
    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    from config import load_config
    config = load_config('config.yaml')
    
    if not config:
        print("  ✗ Failed to load configuration. Exiting.")
        return
    
    print("  ✓ Configuration loaded successfully")
    
    # Step 2: Set up output directories
    print("\nStep 2: Setting up output directories...")
    output_dir = config.get('output', {}).get('base_dir', 'generated_answers')
    answers_dir = os.path.join(output_dir, config.get('answers_dir', 'star_answers'))
    conversations_dir = os.path.join(output_dir, config.get('conversations_dir', 'conversations'))
    
    os.makedirs(conversations_dir, exist_ok=True)
    print(f"  ✓ Created output directory: {conversations_dir}")
    
    # Step 3: Initialize state manager
    print("\nStep 3: Initializing state manager...")
    from state_manager import StateManager, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_FAILED
    
    db_path = os.path.join(output_dir, 'test_processing_state.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  ✓ Removed existing test database: {db_path}")
    
    state_manager = StateManager(db_path)
    print(f"  ✓ Initialized state manager with database: {db_path}")
    
    # Step 4: Initialize LLM client
    print("\nStep 4: Initializing LLM client...")
    from llm_client import LLMClient
    llm_client = LLMClient(config)
    print("  ✓ Initialized LLM client")
    
    # Step 5: Load STAR answers
    print("\nStep 5: Loading STAR answers...")
    
    # Find all STAR answer files
    star_answer_files = list(Path(answers_dir).glob("*.json"))
    
    if not star_answer_files:
        print("  ✗ No STAR answer files found. Please run Phase 3 first.")
        return
    
    print(f"  ✓ Found {len(star_answer_files)} STAR answer files")
    
    # Select the first STAR answer file for testing
    star_answer_file = star_answer_files[0]
    print(f"  ✓ Using STAR answer file: {star_answer_file}")
    
    # Load the STAR answer
    from conversational_transformer import load_star_answer
    star_answer = load_star_answer(star_answer_file)
    
    if not star_answer:
        print("  ✗ Failed to load STAR answer from file")
        return
    
    # Extract metadata for display
    metadata = star_answer.get('metadata', {})
    print(f"  ✓ Loaded STAR answer for role: {metadata.get('role', 'Unknown')}")
    print(f"  ✓ Industry: {metadata.get('industry', 'Unknown')}")
    print(f"  ✓ Question: {metadata.get('question', 'Unknown')}")
    
    # Step 6: Load the conversational prompt template
    print("\nStep 6: Loading conversational prompt template...")
    from prompt_processor import load_prompt_template
    
    template_path = config['prompts'].get('conversation_prompt', config.get('conversation_prompt_path', 'prompt_templates/stage3_conversational_transformer.md'))
    template = load_prompt_template(template_path)
    
    if not template:
        print(f"  ✗ Failed to load template from {template_path}")
        return
    
    print(f"  ✓ Loaded template from {template_path}")
    
    # Step 7: Generate a conversational response
    print("\nStep 7: Generating conversational response...")
    print("  This may take a moment...")
    
    # Import the generate_conversation function
    from conversational_transformer import generate_conversation
    
    start_time = time.time()
    
    # Generate the conversational response
    success, output_file = generate_conversation(
        llm_client=llm_client,
        state_manager=state_manager,
        template_path=template_path,
        star_answer_path=str(star_answer_file),
        output_dir=conversations_dir,
        config=config
    )
    
    elapsed_time = time.time() - start_time
    
    if success:
        print(f"  ✓ Successfully generated conversational response in {elapsed_time:.2f} seconds")
        print(f"  ✓ Saved to: {output_file}")
        
        # Step 8: Display the generated conversational response
        print("\nStep 8: Displaying generated conversational response...")
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # Display metadata
            metadata = conversation_data.get('metadata', {})
            print("\nMetadata:")
            print(f"  Role: {metadata.get('role', 'N/A')}")
            print(f"  Industry: {metadata.get('industry', 'N/A')}")
            print(f"  Question: {metadata.get('question', 'N/A')}")
            
            # Display conversation parts
            conversation = conversation_data.get('conversation', {})
            print("\nConversation:")
            print("\nInterviewer Question:")
            print(f"  {conversation.get('interviewer_question', 'N/A')[:200]}...")
            print("\nCandidate Answer:")
            print(f"  {conversation.get('candidate_answer', 'N/A')[:200]}...")
            
            if conversation.get('follow_up_question'):
                print("\nFollow-up Question:")
                print(f"  {conversation.get('follow_up_question', 'N/A')[:200]}...")
                print("\nFollow-up Answer:")
                print(f"  {conversation.get('follow_up_answer', 'N/A')[:200]}...")
            
        except Exception as e:
            print(f"  ✗ Error reading conversation file: {e}")
    else:
        print(f"  ✗ Failed to generate conversational response")
    
    # Step 9: Clean up
    print("\nStep 9: Cleaning up...")
    state_manager.close()
    print("  ✓ Closed state manager")
    
    print("\nTest completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
