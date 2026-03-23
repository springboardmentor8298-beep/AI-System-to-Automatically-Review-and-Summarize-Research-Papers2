import gradio as gr
# Import the backend pipeline (Milestone 3), establishing a clear separation 
# of concerns between the frontend UI and the backend processing logic.
import milestone3

def generate_systematic_review(topic, count):
    """
    Controller/Wrapper function to connect Gradio frontend inputs to the backend pipeline.
    This ensures that any backend crashes or API timeouts are caught gracefully 
    without crashing the web server or the user interface.
    """
    # Input Validation: Prevent unnecessary API calls if the user leaves the field blank.
    if not topic.strip():
        return "###  Error ###: Please enter a valid research topic."
    
    try:
        # Trigger the end-to-end processing pipeline (M1: Search -> M2: Extract -> M3: Synthesize).
        # We cast 'count' to an integer to ensure strict type safety before passing to the backend.
        final_report = milestone3.run_milestone_3_pipeline(topic, int(count))
        return final_report
        
    # Exception Handling Strategy: 
    # Catch specific known errors (like missing files) to give the user actionable feedback.
    except FileNotFoundError:
        return "### Error ###: No papers could be processed.\nThis usually means Semantic Scholar couldn't find accessible PDFs for this topic. Try a broader search term."
        
    # Catch-all for unexpected backend failures (e.g., API rate limits, network drops)
    except Exception as e:
        return f"###  An unexpected error occurred:\n\n{str(e)}"

# --- UI DESIGN & LAYOUT ---
# Initialize the Gradio Blocks architecture, which allows for custom, flexible web layouts.
# FIX 1: Removed the theme argument from Blocks (moved to launch method for Gradio 6.0+ compatibility)
with gr.Blocks(title="AI Review Generator") as demo:
    
    # Header Section: Clearly define the tool's purpose for the end-user
    gr.Markdown("#  AI Systematic Review Generator")
    gr.Markdown("This tool automates **Paper Retrieval**, **Text Extraction**, and **Cross-Paper Synthesis** to generate structured academic drafts.")
    
    # Input Section: Group related inputs horizontally using gr.Row() for a cleaner UX
    with gr.Row():
        # Textbox for the search query, scaled to take up more horizontal space (scale=3)
        topic_input = gr.Textbox(
            label="Research Topic", 
            placeholder="e.g., Quantum Machine Learning", 
            scale=3
        )
        # Slider to enforce strict bounds on the number of papers, preventing API quota exhaustion
        count_input = gr.Slider(
            minimum=1, 
            maximum=10, 
            value=3, 
            step=1, 
            label="Maximum Papers to Analyze", 
            scale=1
        )
        
    # Primary action button to trigger the workflow
    generate_btn = gr.Button("-> Generate Systematic Review", variant="primary")
    
    # Visual separator for clean UI design
    gr.Markdown("---")
    
    # Output Section: A placeholder Markdown block that will dynamically update 
    # once the backend returns the synthesized report.
    # FIX 2: Removed show_copy_button=True to prevent the TypeError in current Gradio version
    output_display = gr.Markdown(
        value="*Your generated review will appear here. Please note that processing takes a few minutes as it downloads, reads, and synthesizes the papers.*",
        label="Generated Draft"
    )
    
    # Event Handler: Binds the button click to the wrapper function.
    # It maps the UI inputs (topic_input, count_input) to the function arguments
    # and routes the function's return value to the output_display component.
    generate_btn.click(
        fn=generate_systematic_review,
        inputs=[topic_input, count_input],
        outputs=output_display
    )

# Application Entry Point
if __name__ == "__main__":
    print("[INFO] Launching the AI Systematic Review Web Interface...")
    # Deploy the local web server. 
    # FIX 1 (Continued): Moved the theme argument into the launch method to comply with Gradio 6.0 API.
    demo.launch(theme=gr.themes.Soft())