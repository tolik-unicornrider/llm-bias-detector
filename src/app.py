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
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # System prompt
        default_prompt = "You are a helpful expert. Provide balanced, objective comparisons based on facts."
        system_prompt = st.text_area(
            "System Prompt",
            value=default_prompt,
            help="Instructions for the LLM"
        )
    
    with col2:
        # Model selection
        model = st.selectbox(
            "Select Model",
            ["gpt-3.5-turbo", "gpt-4-mini"],
            help="Choose the LLM model to use"
        )
    
    with col3:
        # Number of runs
        runs = st.selectbox(
            "Number of Runs",
            [3, 10, 25, 100],
            index=0,  # Default to 3 runs
            help="How many times to run the query"
        )
    
    # Query input on second row
    default_query = "Pick your favorite letter from the alphabet (maximum 2 letters) and briefly explain why you chose it."
    query = st.text_area(
        "Your Query",
        value=default_query,
        help="The question you want to analyze"
    )
    
    # Process button
    if st.button("Analyze", disabled=not query.strip()):
        if not query.strip():
            st.error("Please enter a query")
            return
        
        # Create placeholders
        progress = st.empty()
        samples = st.empty()
        results = st.empty()
        
        try:
            # Step 1: Getting responses
            progress.info("🤖 Getting responses from LLM...")
            response_progress = st.progress(0)
            
            def update_progress(current: int, total: int):
                response_progress.progress(current / total)
                progress.info(f"🤖 Getting responses from LLM... ({current}/{total})")
            
            responses = get_responses(
                unique_id=st.session_state.unique_id,
                model=model,
                query=query,
                system_prompt=system_prompt,
                runs=runs,
                progress_callback=update_progress
            )
            
            response_progress.empty()
            
            # Show samples right after getting responses
            with samples.expander("Samples", expanded=True):
                st.write("First 10 responses:")
                for i, response in enumerate(responses[:10], 1):
                    st.markdown(f"**Response {i}:**")
                    st.text(response[:500] + ("..." if len(response) > 500 else ""))
                    st.markdown("---")
            
            # Step 2: Processing options
            progress.info("🔍 Identifying options...")
            mappings = process_options(
                unique_id=st.session_state.unique_id,
                responses=responses,
                query=query
            )
            
            # Update samples with identified options
            with samples.expander("Samples", expanded=True):
                st.write("First 10 responses with identified options:")
                for i, (response, entities) in enumerate(mappings[:10], 1):
                    st.markdown(f"**Response {i}:**")
                    st.text(response[:500] + ("..." if len(response) > 500 else ""))
                    st.markdown(f"*Identified options: {', '.join(entities)}*")
                    st.markdown("---")
            
            # Step 3: Analyzing shares
            progress.info("📊 Calculating results...")
            shares = analyze_shares(
                unique_id=st.session_state.unique_id,
                mappings=mappings
            )
            
            # Display results
            progress.success("✅ Analysis complete!")
            
            with results.container():
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
            progress.empty()
            st.error(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="LLM Response Analyzer",
        page_icon="🤖",
        layout="wide"
    )
    main() 