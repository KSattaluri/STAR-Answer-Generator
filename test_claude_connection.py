"""
Claude API Connection Test Script

This script tests the connection to Anthropic's Claude AI model using the API key
from the .env file and mimics the payload structure used in main.py to ensure the
Claude fallback will work correctly.
"""

import os
from dotenv import load_dotenv
import anthropic
import sys
import asyncio
import time
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clean_text_for_console(text):
    """Clean text of any characters that might cause display issues in Windows console."""
    if not text:
        return ""
    
    # Replace specific problematic Unicode characters with ASCII equivalents
    replacements = {
        '✓': '[PASS]',
        '✗': '[FAIL]',
        '⚠': '[WARNING]',
        '→': '->',
        '…': '...',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '–': '-',
        '—': '--'
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Then filter out any remaining non-ASCII characters
    # Only keep characters within the standard ASCII range (codes 32-126)
    return ''.join(c if 32 <= ord(c) <= 126 else '?' for c in text)

def mask_api_key(key):
    """Mask the API key for safe display."""
    if not key:
        return "None"
    if len(key) <= 12:
        return "***" 
    return key[:6] + "..." + key[-4:]  # Show first 6 and last 4 chars

async def test_claude_connection():
    """Test the connection to Claude API and verify the API key works for both Step 1 and Step 2 of our process."""
    try:
        # Load API key from .env file
        load_dotenv()
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not found in .env file")
            return False
        
        # Display masked key for troubleshooting    
        print(f"Using API key (masked): {mask_api_key(api_key)}")
        print(f"API key length: {len(api_key)} characters")
        
        # Initialize the Anthropic client using AsyncAnthropic just like in main.py
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        # Try to use a different model - one that's widely available
        model_name = "claude-3-7-sonnet-20250219"  # Using the model specified by the user
        max_tokens_step1 = 4000  # Same as in main.py config default
        max_tokens_step2 = 4000  # Same as in main.py config default
        temperature = 0.7        # Same as in main.py config default
        
        print(f"Testing connection to model: {model_name}")
        
        # -------------------------------
        # Test 1: Basic Connection Test
        # -------------------------------
        print("\n--- Test 1: Basic Connection ---")
        print("Sending simple test message to Claude API...")
        start_time = time.time()
        
        try:
            # Use async call with await, just like in main.py
            message = await client.messages.create(
                model=model_name,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": "Hello, Claude. Please confirm the connection is working with a brief response. Please don't use emojis in your response."}
                ]
            )
            
            elapsed_time = time.time() - start_time
            
            # Check if we received a response
            if message and message.content:
                # Clean the text for console display
                response_text = ""
                for content_block in message.content:
                    if content_block.type == "text":
                        response_text += content_block.text
                
                safe_text = clean_text_for_console(response_text)
                
                print(f"Connection test successful! Response received in {elapsed_time:.2f} seconds:")
                print("-" * 50)
                print(safe_text)
                print("-" * 50)
                
                # Additional API test info
                if hasattr(message, 'usage') and message.usage:
                    print(f"Input tokens: {message.usage.input_tokens}")
                    print(f"Output tokens: {message.usage.output_tokens}")
                    print(f"Total tokens: {message.usage.input_tokens + message.usage.output_tokens}")
            else:
                print("Error: No response content received from the API")
                return False
                
        except anthropic.APIError as api_error:
            print(f"Claude API Error: {str(api_error)}")
            # Detailed error handling omitted for brevity
            return False
        
        # -----------------------------------------
        # Test 2: Main.py Step 1 - Sub-prompt Generation
        # -----------------------------------------
        print("\n--- Test 2: Step 1 (Sub-prompt Generation) Payload Test ---")
        print("Testing sub-prompt generation payload (Step 1 from main.py)...")
        
        # Sample Step 1 prompt from main.py
        role = "Product Manager"
        question = "Tell me about a situation where you had to make product decisions with incomplete information"
        industry = "Finance / Financial Services"
        
        # Create a simplified version of the Step 1 prompt
        system_instruction = "You are tasked with creating JSON sub-prompts for STAR-format interview answers. Respond only with a valid JSON array containing creative and varied sub-prompts."
        step1_prompt = f"""
        I need to generate 10 varied STAR-format interview answer sub-prompts for:
        - Role: {role}
        - Question: "{question}" 
        - Industry/Context: {industry}
        
        Return a JSON array where each element has these fields:
        - "situation_context": Brief context for the Situation part
        - "specific_task": The specific task or challenge faced
        - "action_approach": Key actions taken to address the challenge
        - "key_results": The outcomes and results achieved
        
        Keep each field concise (1-2 sentences). Ensure diversity across the prompts.
        """
        
        full_prompt = f"{system_instruction}\n\n{step1_prompt}"
        
        try:
            print(f"Sending Step 1 (sub-prompt generation) test request...")
            start_time = time.time()
            
            # Use async call with await, just like in main.py
            response = await client.messages.create(
                model=model_name,
                max_tokens=max_tokens_step1,
                temperature=temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            elapsed_time = time.time() - start_time
            
            # Process response
            if response and response.content:
                json_response = response.content[0].text
                
                print(f"Step 1 test successful! Response received in {elapsed_time:.2f} seconds.")
                print("First 500 chars of response:")
                print("-" * 50)
                print(clean_text_for_console(json_response[:500]) + "...")
                print("-" * 50)
                
                # Validate JSON - most important test
                try:
                    # Clean up JSON if needed, mimicking main.py logic
                    if json_response.strip().startswith("```json"):
                        json_response = json_response.split("```json")[1].split("```")[0].strip()
                    elif json_response.strip().startswith("```"):
                        json_response = json_response.split("```")[1].split("```")[0].strip()
                        
                    sub_prompts = json.loads(json_response)
                    print(f"[PASS] Successfully parsed JSON. Found {len(sub_prompts)} sub-prompts.")
                    print("First sub-prompt sample:")
                    try:
                        # Use safe output for the sample
                        sample_json = json.dumps(sub_prompts[0], indent=2)
                        print(clean_text_for_console(sample_json))
                    except:
                        print("<First sample available but cannot be displayed>")
                except json.JSONDecodeError as e:
                    print(f"[FAIL] Failed to parse JSON from Claude's response: {e}")
                    print("This will cause problems in main.py's Step 1 processing!")
                    return False
            else:
                print("Error: No response content received from the API for Step 1 test")
                return False
        
        except Exception as e:
            print(f"Error during Step 1 test: {str(e)}")
            print("Exception type:", type(e).__name__)
            return False
        
        # -----------------------------------------
        # Test 3: Main.py Step 2 - STAR Answer Generation
        # -----------------------------------------
        print("\n--- Test 3: Step 2 (STAR Answer Generation) Payload Test ---")
        print("Testing STAR answer generation payload (Step 2 from main.py)...")
        
        # Example sub-prompt to use (simplified sample)
        sub_prompt = {
            "situation_context": "As a Product Manager at a financial technology startup, I only had preliminary market research and early customer feedback.",
            "specific_task": "I needed to decide on the core feature set for our tax optimization service for freelancers with limited quantitative data.",
            "action_approach": "I conducted targeted interviews with potential users, analyzed proxy data from similar markets, and used a low-fidelity MVP to validate assumptions.",
            "key_results": "The launched product achieved 35% above-target user adoption in the first quarter and stronger retention than competing products."
        }
        
        # Construct a Step 2 prompt similar to main.py
        system_instruction = "You are a senior professional with extensive interview experience. Create detailed, authentic STAR format answers based on the given context."
        step2_prompt = f"""
        Create a comprehensive STAR format interview answer for:
        - Role: {role}
        - Question: "{question}" 
        - Industry/Context: {industry}
        
        Use exactly this sub-prompt as your basis:
        
        SITUATION CONTEXT: {sub_prompt["situation_context"]}
        SPECIFIC TASK: {sub_prompt["specific_task"]}
        ACTION APPROACH: {sub_prompt["action_approach"]}
        KEY RESULTS: {sub_prompt["key_results"]}
        
        Format the answer with clear **Situation:**, **Task:**, **Action:**, and **Result:** sections.
        The answer should be highly detailed, highlighting specific strategies, metrics, and technical concepts.
        Write 350-600 words with realistic, industry-specific language and examples.
        """
        
        full_prompt = f"{system_instruction}\n\n{step2_prompt}"
        
        try:
            print(f"Sending Step 2 (STAR answer generation) test request...")
            start_time = time.time()
            
            # Use async call with await, just like in main.py
            response = await client.messages.create(
                model=model_name,
                max_tokens=max_tokens_step2,
                temperature=temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            elapsed_time = time.time() - start_time
            
            # Process response
            if response and response.content:
                star_answer = response.content[0].text
                
                print(f"Step 2 test successful! Response received in {elapsed_time:.2f} seconds.")
                print("First 500 chars of response:")
                print("-" * 50)
                print(clean_text_for_console(star_answer[:500]) + "...")
                print("-" * 50)
                
                # Simple validation - check if it has STAR structure
                validation_keywords = ["situation", "task", "action", "result"]
                found_keywords = [kw for kw in validation_keywords if kw.lower() in star_answer.lower()]
                if len(found_keywords) >= 3:  # At least 3 of the 4 STAR components should be present
                    print(f"[PASS] Response follows STAR format structure.")
                else:
                    print(f"[WARNING] Response may not follow STAR format. Found only {len(found_keywords)}/{len(validation_keywords)} components.")
                    print(f"Missing: {[kw for kw in validation_keywords if kw not in found_keywords]}")
            else:
                print("Error: No response content received from the API for Step 2 test")
                return False
                
        except Exception as e:
            print(f"Error during Step 2 test: {str(e)}")
            print("Exception type:", type(e).__name__)
            return False
            
        return True
                
    except Exception as e:
        print(f"Error in connection testing process: {str(e)}")
        print("Exception type:", type(e).__name__)
        return False

if __name__ == "__main__":
    print("Testing connection to Claude API with payload structures from main.py...")
    
    # Use asyncio.run() to handle the async test function
    test_result = asyncio.run(test_claude_connection())
    
    if test_result:
        print("\nAll tests completed successfully. Your Claude API connection is working properly as a fallback for main.py.")
        sys.exit(0)
    else:
        print("\nConnection test failed. Claude may not work correctly as a fallback in main.py.")
        sys.exit(1)
