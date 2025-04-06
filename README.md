# STAR Answer Generator

A comprehensive system for generating structured STAR (Situation, Task, Action, Result) format answers for interview preparation, and transforming them into natural conversational dialogue.

## 🚀 Advanced Prompt Engineering Showcase

This project demonstrates sophisticated prompt engineering techniques at scale, including:

- **Multi-Stage Prompting Pipeline**: Orchestrates complex prompt chains across sub-prompt generation, STAR answer creation, and conversational transformation stages
- **Dynamic Parameter Injection**: Seamlessly substitutes role, industry, and question parameters into custom-designed prompt templates
- **Meta-Prompting Framework**: Leverages outputs from earlier LLM calls as refined inputs to subsequent prompt stages
- **Context-Aware Generation**: Incorporates role-specific skills and industry context for highly relevant and domain-appropriate responses
- **Modular Template Architecture**: Implements a flexible template system with strategic placeholders for dynamic content injection
- **Structured Output Generation**: Uses carefully crafted prompting patterns to guide LLMs toward producing consistently formatted responses
- **Resilient Processing**: Implements intelligent fallback mechanisms and retry logic for handling API limitations

The system serves as a comprehensive case study in advanced LLM prompt design, demonstrating how to effectively maintain context and coherence across multiple chained generations.

## Overview

The STAR Answer Generator is designed to help users prepare for job interviews by generating high-quality, structured responses to common interview questions. The system follows a multi-phase pipeline:

1. **Configuration and Setup (Phase 1)**: Loads configuration from YAML, sets up logging, and initializes state management
2. **Sub-Prompt Generation (Phase 2)**: Creates tailored sub-prompts for specific roles, questions, and industries
3. **STAR Answer Generation (Phase 3)**: Generates structured STAR format answers based on the sub-prompts
4. **Conversational Transformation (Phase 4)**: Transforms STAR answers into natural conversational dialogue

## Features

- **Role-Specific Answers**: Generates answers tailored to specific roles (e.g., Technical Delivery Manager, Product Owner)
- **Industry Contextualization**: Adapts answers to different industries (e.g., Finance, Healthcare, Retail)
- **Structured STAR Format**: Ensures answers follow the Situation, Task, Action, Result framework
- **Natural Dialogue**: Transforms structured answers into conversational format
- **Resilient Processing**: Supports resuming interrupted processes
- **Flexible Configuration**: Easily configurable through YAML configuration file
- **State-of-the-Art LLM Support**: Leverages Google's Gemini 2.5 Pro (gemini-2.5-pro-exp-03-25) and Anthropic's Claude 3.7 Sonnet (claude-3-7-sonnet-20250219) models, with intelligent fallback mechanism
- **Centralized Role Mappings**: Standardized abbreviations and skills file paths in the config
- **Consistent File Naming**: Files named using role/industry abbreviations and question IDs

## Prerequisites

- Python 3.8 or higher
- API keys for Gemini and/or Claude (at least one is required)
- Required Python packages (see Installation section)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/KSattaluri/STAR-Answer-Generator.git
   cd STAR-Answer-Generator
   ```

2. Install required packages:
   ```bash
   pip install google-generativeai anthropic pyyaml python-dotenv
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ANTHROPIC_API_KEY=your_claude_api_key_here
   ```

## Configuration

The system is configured through the `config.yaml` file in the project root. Key configuration options include:

- **Output Settings**: Directories for generated files
- **LLM API Settings**: API keys, models, and retry parameters
- **Role Mappings**: Centralized mapping of roles to abbreviations and skills files
- **Industry Mappings**: Standard industry abbreviations for consistent file naming
- **Target Roles and Questions**: Roles with interview questions in a streamlined format
- **Prompt Templates**: Paths to prompt templates for each phase

### Common Configuration Changes

When working with the system, you'll typically only need to modify these sections of the config file:

- **API Keys**: Update your LLM API keys in the `.env` file
- **Role Mappings**: Add new roles with their abbreviations and skills file paths
- **Industry Mappings**: Add new industries with their abbreviations
- **Target Roles and Questions**: Update the interview questions for each role

Other settings like prompt templates, output directories, and token limits generally don't need to be changed unless you're customizing the system behavior.

### Role and Industry Mappings

The system uses a centralized approach for role and industry abbreviations:

```yaml
# Example role mappings with abbreviations and skills file paths
role_mappings:
  "Technical Delivery Manager": 
    abbr: "tdm"
    skills_file: "prompt_templates/role_skills/TDM-Skills.md"

# Example industry mappings with standardized abbreviations
industry_mappings:
  "Finance / Financial Services": "fin"
```

Refer to the full `config.yaml` for the complete list of roles and industries, and for examples on how to set up new values.

### File Naming Convention

Output files follow a consistent naming pattern:
```
{role_abbr}_{question_id}_{industry_abbr}_{prompt_number}_star.json
```

Example: `tdm_q1_fin_1_star.json` for a Technical Delivery Manager's response to question 1 in Financial Services.

See `config.yaml` for all available options and their descriptions.

## Usage

### Running the Complete Pipeline

To run the complete pipeline for all roles, questions, and industries defined in the configuration:

```bash
python main.py
```

### Running with Filters

You can filter by role, question, or industry:

```bash
python main.py --role "Technical Delivery Manager"
python main.py --question "Describe a situation where you had to manage a complex project"
python main.py --industry "Finance / Financial Services"
```

### Resuming Interrupted Processing

If the process is interrupted, you can resume from where it left off:

```bash
python main.py --resume
```

### Running Specific Phases

You can run specific phases of the pipeline:

```bash
python main.py --phase sub_prompts
python main.py --phase star_answers
python main.py --phase conversational
```

### Cleaning Generated Files

To completely reset the system (remove all generated files, reset the state database, and remove output directories):

```bash
python cleanup.py --all --reset_db --remove_dirs
```

For partial cleanup options:

```bash
# Clean all generated files without resetting database
python cleanup.py --all

# Reset only the state database
python cleanup.py --reset_db

# Clean specific phases
python cleanup.py --sub_prompts
python cleanup.py --star_answers
python cleanup.py --conversational
```

These cleanup options are particularly useful when testing changes to the system configuration or when starting a fresh run after making changes to the code.

## Testing

The project includes comprehensive test scripts for each phase and end-to-end testing. See the [tests/README.md](tests/README.md) file for detailed information on running tests.

Quick examples:

```bash
# End-to-end test
python tests/test_end_to_end.py --clean

# Phase-specific tests
python tests/test_subprompt_generation_phase2.py --clean
python tests/test_star_answer_generation_phase3.py --clean
python tests/test_conversational_transformation_phase4.py --clean
```

## Project Structure

```
PromptEngineering_STAR_Answers/
├── config.yaml                  # Main configuration file
├── main.py                      # Main entry point
├── cleanup.py                   # Script to clean generated files
├── config.py                    # Configuration loading module
├── logger_setup.py              # Logging configuration
├── state_manager.py             # State management with SQLite
├── llm_client.py                # LLM API client (Gemini/Claude)
├── subprompt_generator.py       # Phase 2: Sub-prompt generation
├── star_answer_generator.py     # Phase 3: STAR answer generation
├── conversational_transformer.py # Phase 4: Conversational transformation
├── prompt_processor.py          # Prompt template processing
├── prompt_templates/            # Prompt templates for each phase
│   ├── stage1_subprompt_generator.md
│   ├── stage2_star_answer_generator.md
│   ├── stage3_conversational_transformer.md
│   └── role_skills/             # Role-specific skills
├── generated_answers/           # Generated outputs (gitignored)
│   ├── sub_prompts/             # Generated sub-prompts
│   ├── star_answers/            # Generated STAR answers
│   └── conversations/           # Generated conversational responses
├── tests/                       # Test scripts
│   ├── README.md                # Test documentation
│   ├── test_end_to_end.py       # End-to-end test
│   └── ...                      # Phase-specific tests
└── logs/                        # Log files (gitignored)
```

## Important Considerations

1. **API Keys**: Ensure your API keys are properly set in the `.env` file. The system will use Gemini by default and fall back to Claude if available.

2. **Rate Limits**: Be mindful of API rate limits. The system includes retry logic with exponential backoff, but excessive requests may still hit limits.

3. **Processing Time**: Generating answers for multiple roles, questions, and industries can take significant time. Use the `--resume` flag if the process is interrupted.

4. **Disk Space**: Generated files can accumulate over time. Use the `cleanup.py` script periodically to remove unnecessary files.

5. **Customization**: 
   - **Adding New Roles**:
     1. Add the role to `role_mappings` section with a unique abbreviation and skills file path
     2. Add the role to `target_roles` section with appropriate interview questions
     3. Create a skills file in the `prompt_templates/role_skills` directory
   - **Adding New Questions**:
     1. Update the role's `interview_questions` in the `target_roles` section using the format:
        ```yaml
        interview_questions:
          Q1: "Question text"
          Q2: "Another question"
        ```
   - **Adding New Industries**:
     1. Add the industry to `industry_mappings` with a unique abbreviation
     2. Add the industry to the `target_industries` list
   - **Modifying Templates**:
     - Edit the files in the `prompt_templates` directory
   - **Changing LLM Models**:
     - Update the `gemini_model` or `claude_model` settings in `config.yaml`

6. **Error Handling**: The system logs errors to the `logs` directory. Check these logs if you encounter issues.

7. **State Management**: The system uses a SQLite database (`processing_state.db`) to track the status of files. This enables resuming interrupted processes.

## Troubleshooting

1. **API Connection Issues**:
   - Verify your API keys in the `.env` file
   - Check your internet connection
   - Ensure you're not hitting API rate limits

2. **Missing Dependencies**:
   - Run `pip install -r requirements.txt` to install all required packages

3. **File Permission Errors**:
   - Ensure you have write permissions for the project directory

4. **Incomplete Outputs**:
   - Check the logs for error messages
   - Use the `--resume` flag to continue processing
   - Verify that your prompt templates are properly formatted

5. **Database Errors**:
   - If you encounter database errors, try resetting the state database with `python cleanup.py --reset_db`

## License

[MIT License](LICENSE)

## Acknowledgments

- This project uses the Gemini and Claude APIs for natural language processing
- The STAR format is a widely recognized framework for structured interview responses
