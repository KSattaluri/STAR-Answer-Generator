# STAR Answer Generation System Requirements

## Project Overview

This system generates realistic, detailed STAR-format interview answers for various professional roles and industries, and transforms them into natural conversational responses. The system is designed with resilience at each stage to handle interruptions and failures gracefully.

## System Requirements

### 1. Configuration & Setup

- **Configuration Loading**: Load settings from config.yaml including target roles, industries, questions, and LLM parameters
- **LLM Client Initialization**: Configure API clients for Gemini and Claude with proper authentication
- **Logging Setup**: Implement comprehensive logging for tracking system operation
- **State Management**: Initialize state tracking database for resilience

### 2. Sub-Prompt Generation (Stage 1)

- **Meta-Prompt Processing**: Use meta_prompt.md to generate multiple unique JSON sub-prompts for each role/question/industry combination
- **Variation Requirements**: Each sub-prompt must specify different scenarios, skill focuses, and contexts to ensure diverse answers
- **Resilience Mechanism**: Save sub-prompts to disk (JSON format) to enable resumption if processing is interrupted
- **LLM Fallback**: Implement fallback between providers if primary LLM fails to generate valid sub-prompts

### 3. STAR Answer Generation (Stage 2)

- **Context Integration**: Use main_context_prompt.md as the foundation for generating detailed STAR-format answers
- **Sub-Prompt Application**: Apply each sub-prompt to create a unique STAR answer for the specified role/question/industry
- **Structured Output**: Generate answers with clear Situation, Task, Action, and Result sections
- **File Organization**: Save answers in a structured directory hierarchy (role/question/industry)
- **State Tracking**: Record processing state in database to enable resumption if interrupted
- **Error Handling**: Implement retry mechanisms for failed generations

### 4. Conversational Transformation (Stage 3)

- **Answer Scanning**: Locate and process all generated STAR-format answers
- **Conversational Styling**: Use conversation_prompt_fixed.txt to transform formal STAR answers into natural conversational language
- **Metadata Extraction**: Generate metadata about each answer (keywords, skills, challenges, etc.)
- **Output Storage**: Save conversational versions alongside original STAR answers
- **Continued State Tracking**: Update processing state to enable resumption if interrupted

## Resilience Requirements

- **Persistent State**: Track processing state in SQLite database
- **Checkpointing**: Save outputs at each stage to disk
- **LLM Provider Fallback**: Switch between LLM providers if one fails
- **Retry Logic**: Implement exponential backoff for failed operations
- **Graceful Shutdown**: Handle interruptions without corrupting data
- **Resumption Capability**: Ability to continue processing from last successful point

## Quality Requirements

- **Answer Diversity**: Generate varied scenarios and examples across answers
- **Industry Relevance**: Ensure answers are contextually appropriate for the specified industry
- **Role Accuracy**: Demonstrate skills and knowledge appropriate for the target role
- **Natural Language**: Conversational versions should sound authentic and interview-ready
- **Technical Accuracy**: Include realistic technical details and terminology
