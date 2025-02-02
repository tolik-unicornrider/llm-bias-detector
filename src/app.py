import streamlit as st
from main import get_responses, process_options, analyze_shares
import uuid

def main():
    st.title("LLM Response Analyzer")
    
    # Generate unique ID at the start
    if 'unique_id' not in st.session_state:
        st.session_state.unique_id = str(uuid.uuid4())[:6]
    
    st.info(f"Session ID: {st.session_state.unique_id}")
    
    # First row with system prompt and model selection
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # System prompt
        default_prompt = "You are a helpful expert. Provide balanced, objective comparisons based on facts."
        system_prompt = st.text_area(
            "System Prompt",
            value=default_prompt,
            help="Instructions for the LLM"
        )
    
    with col2:
        # Model multiselect
        models = st.multiselect(
            "Select Models",
            ["gpt-3.5-turbo", "gpt-4o-mini", "o1-mini", "o3-mini", "gemini/gemini-pro", "gemini/gemini-2.0-flash-exp", 
             "gemini/gemini-2.0-flash-thinking-exp", "gemini/gemini-1.5-flash"],
            default=["gpt-3.5-turbo"],
            help="Choose one or more LLM models to use"
        )
        
        # Number of runs
        runs = st.selectbox(
            "Number of Runs per Model",
            [1, 3, 5, 10, 25, 100],
            index=0,  # Default to 1 run
            help="How many times to run the query for each model"
        )
    
    # Query input on second row
    default_query = "Pick your favorite letter from the alphabet (maximum 2 letters) and briefly explain why you chose it."
    query = st.text_area(
        "Your Query",
        value=default_query,
        help="The question you want to analyze"
    )
    
    # Process button
    if st.button("Analyze", disabled=not query.strip() or not models):
        if not query.strip():
            st.error("Please enter a query")
            return
        if not models:
            st.error("Please select at least one model")
            return
        
        # Create placeholders for each model
        progress = st.empty()
        results_container = st.container()
        
        # Process each model
        for model in models:
            with results_container.expander(f"Results for {model}", expanded=True):
                try:
                    # Step 1: Getting responses
                    progress.info(f"🤖 Getting responses from {model}...")
                    response_progress = st.progress(0)
                    
                    def update_progress(current: int, total: int):
                        response_progress.progress(current / total)
                        progress.info(f"🤖 Getting responses from {model}... ({current}/{total})")
                    
                    responses = get_responses(
                        unique_id=st.session_state.unique_id,
                        model=model,
                        query=query,
                        system_prompt=system_prompt,
                        runs=runs,
                        progress_callback=update_progress
                    )
                    
                    response_progress.empty()
                    
                    # Step 2: Processing options
                    progress.info(f"🔍 Identifying options for {model}...")
                    mappings = process_options(
                        unique_id=st.session_state.unique_id,
                        model=model,
                        responses=responses,
                        query=query
                    )
                    
                    # Step 3: Analyzing shares
                    progress.info(f"📊 Calculating results for {model}...")
                    shares = analyze_shares(
                        unique_id=st.session_state.unique_id,
                        model=model,
                        mappings=mappings
                    )
                    
                    # Display results for this model
                    st.subheader("Results Distribution")
                    
                    # Sort shares by value and convert to percentage
                    sorted_shares = sorted(
                        shares.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    # Display as simple text ranking
                    for i, (option, share) in enumerate(sorted_shares, 1):
                        percentage = share * 100
                        st.write(f"{i}. {option}: {percentage:.1f}%")
                    
                except Exception as e:
                    st.error(f"Error analyzing with {model}: {str(e)}")
        
        progress.success("✅ Analysis complete!")

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="LLM Response Analyzer",
        page_icon="🤖",
        layout="wide"
    )
    main() 