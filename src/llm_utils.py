import backoff
from litellm import completion
import json
import os

def run_query(llm_model: str, query: str, system_prompt: str, runs: int = 1) -> list[str]:
    """
    Run a query against an LLM model n times and return the results.
    Use the system prompt to guide the LLM.
    Will retry with exponential backoff on failures.
    """
    
    @backoff.on_exception(
        backoff.expo,  # Use exponential backoff
        Exception,     # Retry on any exception
        max_tries=5,   # Maximum number of attempts
        max_time=30    # Maximum total time to try in seconds
    )
    def _make_completion_call(model: str, messages: list):
        # Configure model mapping for Gemini
        if model.startswith("google/"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
            return completion(
                model=model,  # Model already includes google/ prefix
                messages=messages,
                temperature=0.7
            )
        else:
            return completion(
                model=model,
                messages=messages,
                temperature=0.7
            )
    
    results = []
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    for _ in range(runs):
        try:
            response = _make_completion_call(llm_model, messages)
            result = response.choices[0].message.content
            results.append(result)
        except Exception as e:
            results.append(f"Error: {str(e)}")
    
    return results


def identify_options(responses: list[str], question: str = None) -> list[tuple[str, list[str]]]:
    """
    From the list of responses and optional question, identify and map each response to its normalized entities.
    Args:
        responses: List of text responses from users
        question: Optional original question that was asked
    Returns:
        list[tuple[str, list[str]]]: List of tuples containing (original_response, list_of_normalized_entities)
    """
    function_schema = {
        "name": "extract_entities",
        "description": "Extract and map responses to their normalized entities",
        "parameters": {
            "type": "object",
            "properties": {
                "mappings": {
                    "type": "array",
                    "description": "List of response-to-entities mappings",
                    "items": {
                        "type": "object",
                        "properties": {
                            "response_index": {
                                "type": "integer",
                                "description": "Index of the original response"
                            },
                            "thoughts": {
                                "type": "string",
                                "description": "Reasoning process for identifying the entities"
                            },
                            "normalized_entities": {
                                "type": "array",
                                "description": "The normalized entities extracted from this response",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["response_index", "thoughts", "normalized_entities"]
                    }
                }
            },
            "required": ["mappings"]
        }
    }

    combined_text = "\n".join(f"Response {i}: {resp}" for i, resp in enumerate(responses))
    context = f"Question: {question}\n\n{combined_text}" if question else combined_text
    
    messages = [
        {"role": "system", "content": """You are an assistant that maps responses to their main entities.
For each response:
1. First analyze what type of choices/entities are being discussed
2. Consider all products, features, or variations mentioned
3. Identify all entities being recommended or discussed
4. Normalize the entities to standard forms by:
   - Consolidating specific products under parent brands
   - Using canonical names
   - Including 'Ambiguous' if no clear preferences
5. Document your thought process before making the final mapping

Examples of thought process:
- "This response compares AWS Lambda and GCP Cloud Functions, mentioning benefits of both. Main entities are AWS and GCP"
- "While they discuss React and Vue.js equally, with no clear preference, marking as ['React', 'Vue.js']"
- "The response discusses multiple options without favoring any, marking as ['Ambiguous']"
"""},
        {"role": "user", "content": f"For each response, think through and identify all main normalized entities in this context:\n\n{context}"}
    ]

    try:
        response = completion(
            model="gpt-4",
            messages=messages,
            functions=[function_schema],
            function_call={"name": "extract_entities"}
        )
        
        function_response = response.choices[0].message.function_call
        mappings = json.loads(function_response.arguments)["mappings"]
        
        # Create list of (response, entities) pairs, maintaining original response order
        result = []
        for mapping in mappings:
            response_idx = mapping["response_index"]
            # print(f"Thoughts for response {response_idx}: {mapping['thoughts']}")  # Uncomment for debugging
            entities = mapping["normalized_entities"]
            result.append((responses[response_idx], entities))
            
        return result
        
    except Exception as e:
        return [(response, [f"Error: {str(e)}"]) for response in responses]

MappedResponse = tuple[str, list[str]]
