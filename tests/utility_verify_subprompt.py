"""
Verify Sub-Prompt Generation

This script verifies that sub-prompts are being generated correctly and displays the results.
"""

import os
import json
from pathlib import Path

def main():
    # Define the output directory
    output_dir = "generated_answers"
    subprompts_dir = os.path.join(output_dir, "sub_prompts")
    
    # Check if the directory exists
    if not os.path.exists(subprompts_dir):
        print(f"Sub-prompts directory not found: {subprompts_dir}")
        return
    
    # Find all JSON files in the directory
    json_files = list(Path(subprompts_dir).glob("*.json"))
    
    if not json_files:
        print(f"No sub-prompt files found in {subprompts_dir}")
        return
    
    print(f"Found {len(json_files)} sub-prompt files:")
    
    # Display information about each file
    for i, file_path in enumerate(json_files, 1):
        print(f"\n{i}. {file_path.name}")
        
        try:
            # Load the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                subprompts = json.load(f)
            
            # Display information about the sub-prompts
            print(f"   Contains {len(subprompts)} sub-prompts")
            
            # Display details of the first sub-prompt
            if subprompts:
                first = subprompts[0]
                print("\n   First sub-prompt details:")
                print(f"   - Prompt ID: {first.get('prompt_id', 'N/A')}")
                print(f"   - Skill focus: {first.get('skill_focus', 'N/A')}")
                print(f"   - Soft skill highlight: {first.get('soft_skill_highlight', 'N/A')}")
                print(f"   - Scenario theme: {first.get('scenario_theme_hint', 'N/A')}")
                
                # Display the actual prompt
                print("\n   Prompt content:")
                print(f"   {first.get('prompt', 'N/A')[:200]}...")
                
        except Exception as e:
            print(f"   Error reading file: {e}")

if __name__ == "__main__":
    main()
