"""
Check Sub-Prompt Content

This script checks the content of generated sub-prompts and displays them in a readable format.
"""

import os
import json
import pprint

def main():
    # Define the output directory
    output_dir = "generated_answers"
    subprompts_dir = os.path.join(output_dir, "sub_prompts")
    
    print("\n" + "=" * 80)
    print("SUB-PROMPT VERIFICATION")
    print("=" * 80 + "\n")
    
    # Check if the directory exists
    if not os.path.exists(subprompts_dir):
        print(f"Sub-prompts directory not found: {subprompts_dir}")
        return
    
    # Find all JSON files in the directory
    json_files = [f for f in os.listdir(subprompts_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"No sub-prompt files found in {subprompts_dir}")
        return
    
    print(f"Found {len(json_files)} sub-prompt files:\n")
    
    # Display information about each file
    for i, filename in enumerate(json_files, 1):
        file_path = os.path.join(subprompts_dir, filename)
        print(f"{i}. {filename}")
        
        try:
            # Load the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                subprompts = json.load(f)
            
            print(f"   Contains {len(subprompts)} sub-prompts\n")
            
            # Display details of each sub-prompt
            for j, subprompt in enumerate(subprompts, 1):
                print(f"   Sub-prompt #{j}:")
                print(f"   - Prompt ID: {subprompt.get('prompt_id', 'N/A')}")
                print(f"   - Skill focus: {subprompt.get('skill_focus', 'N/A')}")
                print(f"   - Soft skill highlight: {subprompt.get('soft_skill_highlight', 'N/A')}")
                print(f"   - Scenario theme: {subprompt.get('scenario_theme_hint', 'N/A')}")
                
                # Display a truncated version of the prompt
                prompt = subprompt.get('prompt', 'N/A')
                if len(prompt) > 100:
                    print(f"   - Prompt (truncated): {prompt[:100]}...")
                else:
                    print(f"   - Prompt: {prompt}")
                print()
                
        except Exception as e:
            print(f"   Error reading file: {e}\n")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
