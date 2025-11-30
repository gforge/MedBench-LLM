# Discharge Summary Prompts

This folder contains prompt templates for generating discharge summaries using Large Language Models (LLMs).

## Structure

Each language has two files:
- **`basic_system.md`** - Sets the role and key principles for the LLM
- **`basic_human.md`** - Provides the specific task and output format

## Available Languages

- **English** (`English/`)
- **Swedish** (`Swedish/`)

## How to Use

1. **Choose your language** - Select the appropriate folder
2. **Use both files together** - The system prompt sets the context, the human prompt gives the task
3. **Replace `{notes}`** - This placeholder should be replaced with actual clinical notes

## Maintaining the Prompts

### When updating prompts:

✓ **Keep structure consistent** across languages
✓ **Update both system and human files** if changing the overall approach
✓ **Test with sample data** after making changes
✓ **Maintain parallel sections** - if English has a section, Swedish should too

### Translation Tips:

- Keep examples culturally appropriate (e.g., Swedish names in Swedish version)
- Medical terminology should follow local standards
- ICD-10 codes are universal
- Date formats may differ by region

## Key Features

### Simple Format
- No XML tags - just plain Markdown headers
- Clear visual hierarchy with checkmarks (✓)
- Examples inline for easy reference

### Consistent Structure
Both languages follow the same format:
1. Main Diagnosis
2. Secondary Diagnosis
3. Procedures
4. Reason for Admission
5. Medical History
6. Social History
7. Hospital Course
8. Medication Changes
9. Plan

### Built-in Constraints
- Hospital Course limited to 3 paragraphs
- ICD-10 codes required
- Natural language for medication frequency
- "Not reported" for missing information

## For Non-Technical Users

You don't need to understand programming to maintain these prompts:

- **Headers** (lines starting with `#`) organize the content
- **Bullet points** (lines starting with `-` or `*`) create lists
- **Bold text** (wrapped in `**`) emphasizes important terms
- **Italic text** (wrapped in `*`) shows examples
- **Code blocks** (wrapped in ` ``` `) show where clinical notes go

Just edit the text while keeping the structure intact!

## Questions?

If you're unsure about changes:
1. Make a copy of the file first
2. Test your changes with sample data
3. Compare with the original to verify structure remains consistent
