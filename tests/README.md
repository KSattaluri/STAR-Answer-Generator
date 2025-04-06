# STAR Answer Generator - Test Suite

This directory contains test scripts and utilities for the STAR Answer Generator system. These scripts allow you to test individual phases of the system as well as run end-to-end tests.

## Test Scripts Overview

### Phase-Specific Tests

These scripts test specific phases of the STAR Answer Generator pipeline:

1. **test_subprompt_generation_phase2.py** - Tests Phase 2 (Sub-Prompt Generation)
   - Generates sub-prompts based on roles, questions, and industries
   - Verifies the structure and content of the generated sub-prompts
   - Usage: `python tests/test_subprompt_generation_phase2.py [--clean] [--role ROLE] [--industry INDUSTRY] [--question QUESTION]`

2. **test_star_answer_generation_phase3.py** - Tests Phase 3 (STAR Answer Generation)
   - Generates STAR format answers from sub-prompts
   - Verifies the structure of the generated STAR answers
   - Usage: `python tests/test_star_answer_generation_phase3.py [--clean] [--role ROLE] [--industry INDUSTRY] [--question QUESTION]`

3. **test_conversational_transformation_phase4.py** - Tests Phase 4 (Conversational Transformation)
   - Transforms STAR answers into natural conversational dialogue
   - Verifies the structure of the generated conversations
   - Usage: `python tests/test_conversational_transformation_phase4.py [--clean] [--role ROLE] [--industry INDUSTRY] [--question QUESTION]`

### End-to-End Test

1. **test_end_to_end.py** - Tests the complete pipeline from sub-prompt generation to conversational transformation
   - Runs all phases in sequence
   - Verifies the output of each phase
   - Usage: `python tests/test_end_to_end.py [--clean] [--role ROLE] [--industry INDUSTRY] [--question QUESTION]`

### Utility Scripts

These scripts provide additional functionality for testing and debugging:

1. **utility_check_subprompt_content.py** - Examines the content of generated sub-prompts
   - Displays the content of sub-prompts in a readable format
   - Usage: `python tests/utility_check_subprompt_content.py [--file FILE_PATH]`

2. **utility_reset_test_state.py** - Resets the state database for testing
   - Clears the state database to allow for fresh test runs
   - Usage: `python tests/utility_reset_test_state.py`

3. **utility_simple_test.py** - Simple test script for quick verification
   - Basic test to verify the system setup
   - Usage: `python tests/utility_simple_test.py`

4. **utility_verify_subprompt.py** - Verifies the structure of sub-prompts
   - Validates that sub-prompts conform to the expected format
   - Usage: `python tests/utility_verify_subprompt.py [--file FILE_PATH]`

5. **test_subprompt_generation.py** - Legacy test script for sub-prompt generation
   - Older version of the Phase 2 test
   - Usage: `python tests/test_subprompt_generation.py [--clean]`

## Common Command-Line Arguments

Most test scripts support the following command-line arguments:

- `--clean`: Clean up generated files and reset the state database before running the test
- `--role ROLE`: Specify a role to test (e.g., "Technical Delivery Manager")
- `--industry INDUSTRY`: Specify an industry to test (e.g., "Finance / Financial Services")
- `--question QUESTION`: Specify a question to test
- `--config CONFIG`: Specify an alternative configuration file (default: config.yaml)
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set the logging level

## Examples

### Running a Phase-Specific Test

```bash
# Test Phase 2 (Sub-Prompt Generation) with a specific role and industry
python tests/test_subprompt_generation_phase2.py --clean --role "Technical Delivery Manager" --industry "Finance / Financial Services"

# Test Phase 3 (STAR Answer Generation) with a specific role
python tests/test_star_answer_generation_phase3.py --clean --role "Product Owner"

# Test Phase 4 (Conversational Transformation) with a specific question
python tests/test_conversational_transformation_phase4.py --clean --question "Describe a situation where you had to prioritize features for a product release."
```

### Running an End-to-End Test

```bash
# Run the complete pipeline with default settings
python tests/test_end_to_end.py --clean

# Run the complete pipeline with a specific role, industry, and question
python tests/test_end_to_end.py --clean --role "Scrum Master" --industry "Healthcare / Insurance" --question "Talk about a time when you helped a team overcome obstacles to deliver successfully."
```

### Using Utility Scripts

```bash
# Check the content of a specific sub-prompt file
python tests/utility_check_subprompt_content.py --file "generated_answers/sub_prompts/technical_delivery_manager_q1_finance___financial_services_subprompts.json"

# Reset the test state database
python tests/utility_reset_test_state.py
```

## Troubleshooting

If you encounter issues with the tests:

1. Use the `--clean` flag to start with a fresh state
2. Check the log files in the `logs` directory for detailed error messages
3. Use the utility scripts to examine the generated files
4. Make sure the required environment variables are set in the `.env` file

For more information, refer to the project documentation in the root directory.
