from dotenv import load_dotenv
from llm_utils import run_query, identify_options
from analysis_tools import calculate_options_shares
import json
import os
from pathlib import Path
import uuid

def ensure_data_dir(unique_id: str) -> Path:
    """Create and return data directory for the given unique_id"""
    data_dir = Path('data') / unique_id
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_model_filename(base_name: str, model: str) -> str:
    """Generate filename with model name"""
    # Clean up model name for filename
    model_name = model.replace('/', '-').replace('.', '-')
    return f"{base_name}_{model_name}.json"

def get_responses(
    unique_id: str,
    model: str,
    query: str,
    system_prompt: str,
    runs: int = 1,
    progress_callback: callable = None
) -> list[str]:
    """
    Get responses from LLM and save to file
    Args:
        unique_id: Session identifier
        model: LLM model to use
        query: User query
        system_prompt: System instructions
        runs: Number of responses to get
        progress_callback: Optional callback function(current_run, total_runs)
    Returns: List of responses
    """
    load_dotenv()
    
    results = []
    for i in range(runs):
        result = run_query(model, query, system_prompt)
        # Ensure result is a list, if not, wrap it in a list
        if isinstance(result, str):
            results.extend([result])
        else:
            results.extend(result)
        if progress_callback:
            progress_callback(i + 1, runs)
    
    # Save results and query to file
    data_dir = ensure_data_dir(unique_id)
    responses_file = get_model_filename('responses', model)
    with open(data_dir / responses_file, 'w') as f:
        json.dump({
            'model': model,
            'query': query,
            'responses': results
        }, f, indent=2)
    
    return results

def process_options(
    unique_id: str,
    model: str,
    responses: list[str] = None,
    query: str = None
) -> list[tuple[str, list[str]]]:
    """
    Process responses to identify options
    If responses not provided, load from file
    Returns: List of (response, entities) tuples
    """
    data_dir = ensure_data_dir(unique_id)
    responses_file = get_model_filename('responses', model)
    
    # Load responses if not provided
    if responses is None or query is None:
        with open(data_dir / responses_file, 'r') as f:
            data = json.load(f)
            responses = data['responses']
            query = data['query']
    
    # Get response-to-entities mappings
    mappings = identify_options(responses, query)
    
    # Extract all unique options
    all_options = set()
    for _, entities in mappings:
        all_options.update(entities)
    
    # Save mappings and options
    options_file = get_model_filename('options', model)
    with open(data_dir / options_file, 'w') as f:
        json.dump({
            'model': model,
            'query': query,
            'options': sorted(list(all_options)),
            'mappings': [(resp, ents) for resp, ents in mappings]
        }, f, indent=2)
    
    return mappings

def analyze_shares(
    unique_id: str,
    model: str,
    mappings: list[tuple[str, list[str]]] = None
) -> dict[str, float]:
    """
    Analyze option shares in responses
    If mappings not provided, load from file
    Returns: Dictionary of option shares
    """
    data_dir = ensure_data_dir(unique_id)
    options_file = get_model_filename('options', model)
    
    # Load mappings if not provided
    if mappings is None:
        with open(data_dir / options_file, 'r') as f:
            data = json.load(f)
            mappings = [(resp, ents) for resp, ents in data['mappings']]
    
    # Calculate shares
    shares = calculate_options_shares(mappings)
    
    # Save analysis results
    analysis_file = get_model_filename('analysis', model)
    with open(data_dir / analysis_file, 'w') as f:
        json.dump({
            'model': model,
            'shares': shares
        }, f, indent=2)
    
    return shares

def process_query(
    model: str,
    query: str,
    system_prompt: str,
    runs: int = 1
) -> tuple[str, dict[str, float]]:
    """
    Process query through all steps and return analysis
    Returns: Tuple of (unique_id, option_shares)
    """
    unique_id = str(uuid.uuid4())[:6]  # First 6 chars of UUID
    
    responses = get_responses(unique_id, model, query, system_prompt, runs)
    mappings = process_options(unique_id, model, responses, query)
    shares = analyze_shares(unique_id, model, mappings)
    return unique_id, shares

# Example usage:
if __name__ == "__main__":
    # Example configuration
    config = {
        'model': 'gpt-3.5-turbo',
        'query': 'What programming language should I learn? Pick one. explain why is that',
        'system_prompt': 'You are a helpful expert. Provide balanced, objective comparisons based on facts.',
        'runs': 10
    }
    
    # Run full process
    unique_id, shares = process_query(**config)
    print(f"Unique ID: {unique_id}")
    print(f"Option Shares: {shares}")