


from collections import defaultdict


def calculate_options_shares(mappings: list[tuple[str, list[str]]]) -> dict[str, float]:
    """Calculate the share of each option in the mappings"""
    option_counts = defaultdict(int)
    for _, entities in mappings:
        for entity in entities:
            option_counts[entity] += 1
    
    total_responses = len(mappings)
    return {option: count / total_responses for option, count in option_counts.items()}