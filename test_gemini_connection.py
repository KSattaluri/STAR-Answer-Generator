"""
Gemini API Connection Test Script

This script tests the connection to Google's Gemini AI model using the API key
from the .env file.
"""

import os
from dotenv import load_dotenv
import asyncio
from google import genai
import sys
import unicodedata

def clean_text_for_console(text):
    """Clean text of any characters that might cause display issues in Windows console."""
    if not text:
        return ""
    # Replace emojis and other problematic characters with their description or remove them
    return ''.join(c for c in text if c <= '\uFFFF')

async def test_gemini_connection():
    """Test the connection to Gemini API and verify the API key works."""
    try:
        # Load API key from .env file
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            print("Error: GEMINI_API_KEY not found in .env file")
            return False
            
        # Initialize the GenAI client
        client = genai.Client(api_key=api_key)
        
        # Create an async chat instance
        model_name = "gemini-2.5-pro-exp-03-25"
        print(f"Testing connection to model: {model_name}")
        
        chat = client.aio.chats.create(
            model=model_name
        )
        
        # Send a simple test message
        print("Sending test message to Gemini API...")
        response = await chat.send_message("Hello, can you confirm the connection is working? Please don't use emojis in your response.")
        
        # Check if we received a response
        if response and response.text:
            # Clean the text for console display
            safe_text = clean_text_for_console(response.text)
            
            print("\nConnection test successful! Response received:")
            print("-" * 50)
            print(safe_text)
            print("-" * 50)
            
            # Additional API test - token counting
            try:
                tokens = client.count_tokens(
                    model=model_name,
                    contents="This is a test of the token counting functionality."
                )
                print(f"\nToken counting test successful:")
                print(f"Token count: {tokens.character_count} characters, {tokens.token_count} tokens")
            except Exception as e:
                print(f"\nToken counting test failed: {str(e)}")
            
            return True
        else:
            print("Error: No response received from the API")
            return False
            
    except Exception as e:
        print(f"Error connecting to Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing connection to Gemini API...")
    
    # Run the async test function
    test_result = asyncio.run(test_gemini_connection())
    
    if test_result:
        print("\nAll tests completed successfully. Your Gemini API connection is working properly.")
        sys.exit(0)
    else:
        print("\nConnection test failed.")
        sys.exit(1)
