"""
Prompt templates for pipeline steps and evaluation.

Defines:
- Extraction prompts
- Classification prompts
- Summarization prompts
- Evaluation/Judge prompts
"""

from typing import Dict


# ============================================================================
# PIPELINE STEP PROMPTS
# ============================================================================

EXTRACTION_PROMPT = """
Analyze the following document and extract key entities and information.

Document:
{document}

Extract and structure:
1. Main entities (people, places, organizations, etc.)
2. Key facts and dates
3. Important relationships
4. Any specific claims or assertions

Return structured extraction as JSON with:
- "entities": list of extracted entities with type and context
- "facts": list of key facts
- "relationships": list of entity relationships
- "assertions": list of claims made
- "confidence": overall extraction confidence (0-1)
"""

CLASSIFICATION_PROMPT = """
Classify the following document.

Document:
{document}

Classify by:
1. Document type (e.g., article, report, email, etc.)
2. Topic/category
3. Sentiment (if applicable)
4. Relevance to: {context}

Return classification as JSON with:
- "type": document type
- "category": main category
- "subcategories": related categories (list)
- "sentiment": sentiment label
- "relevance_score": relevance to context (0-1)
- "confidence": classification confidence (0-1)
"""

SUMMARIZATION_PROMPT = """
Summarize the following document concisely.

Document:
{document}

Provide:
1. Executive summary (2-3 sentences)
2. Key findings
3. Main conclusions
4. Action items if any

Return summary as JSON with:
- "executive_summary": brief overview
- "key_findings": list of main findings
- "conclusions": main conclusions
- "action_items": list of any actions needed
- "completeness": how complete is this summary (0-1)
"""

# ============================================================================
# EVALUATION/JUDGE PROMPTS
# ============================================================================

JUDGE_PROMPT = """
Evaluate the quality of the following output from a document processing pipeline.

Input:
{input}

Output to evaluate:
{output}

Step type: {step_type}
Step name: {step_name}

Evaluate on:
1. Correctness: Is the output factually correct given the input?
2. Hallucination: Does the output contain information not in the input?
3. Completeness: Does the output cover all relevant information?
4. Consistency: Is the output internally consistent and coherent?
5. Relevance: Is the output relevant to the task?

For each criterion, provide:
- score (0.0 to 1.0, where 1.0 is perfect)
- explanation

Also provide:
- overall_score (weighted average, 0.0 to 1.0)
- pass (bool, true if overall_score >= 0.7)
- critical_issues (list of serious problems, if any)

Return as JSON with structure:
{{
    "correctness": {{"score": <float>, "explanation": "<string>"}},
    "hallucination": {{"score": <float>, "explanation": "<string>"}},
    "completeness": {{"score": <float>, "explanation": "<string>"}},
    "consistency": {{"score": <float>, "explanation": "<string>"}},
    "relevance": {{"score": <float>, "explanation": "<string>"}},
    "overall_score": <float>,
    "pass": <bool>,
    "critical_issues": ["<issue>", ...]
}}
"""

PROPAGATION_JUDGE_PROMPT = """
Evaluate how much this output error affects downstream processing.

Original correct output:
{correct_output}

Actual output (with error):
{actual_output}

The downstream step needs to process this output.

Rate the propagation impact (0.0 = error is absorbed/corrected, 1.0 = error severely impacts downstream):

Return as JSON:
{{
    "propagation_score": <float 0-1>,
    "will_be_corrected": <bool>,
    "degradation_severity": "none" | "minor" | "moderate" | "severe",
    "explanation": "<why this error propagates>"
}}
"""

# ============================================================================
# PROMPT DICTIONARY
# ============================================================================

PROMPTS: Dict[str, str] = {
    "extraction": EXTRACTION_PROMPT,
    "classification": CLASSIFICATION_PROMPT,
    "summarization": SUMMARIZATION_PROMPT,
    "judge": JUDGE_PROMPT,
    "propagation_judge": PROPAGATION_JUDGE_PROMPT,
}


def get_prompt(prompt_type: str) -> str:
    """Get prompt template by type."""
    if prompt_type not in PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    return PROMPTS[prompt_type]


def format_prompt(prompt_type: str, **kwargs) -> str:
    """
    Get and format prompt template.
    
    Args:
        prompt_type: Type of prompt to get
        **kwargs: Variables to substitute in template
        
    Returns:
        Formatted prompt string
    """
    prompt = get_prompt(prompt_type)
    return prompt.format(**kwargs)
