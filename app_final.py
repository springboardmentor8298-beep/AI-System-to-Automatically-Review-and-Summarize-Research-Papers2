import gradio as gr
import milestone3
import milestone4
import os
import json

# --- 1. STATE MANAGEMENT ---
# The SessionState class acts as the "memory" of your app.
# Because web apps are often "stateless," we need this to store data 
# between clicking "Start Research" and "Critique & Revise."
class SessionState:
    def __init__(self):
        self.topic = ""           # Stores the current research topic
        self.current_report = ""  # Stores the latest generated draft
        self.raw_data = None      # Stores the research context (from M2) for M4 to use

# Initialize a single global instance of the state
session = SessionState()

# --- 2. BACKEND LOGIC FUNCTIONS ---

def run_research_phase(topic, count):
    """
    Triggers the end-to-end pipeline from Milestone 1 through Milestone 3.
    It downloads papers, extracts text, and generates an initial draft.
    """
    if not topic.strip():
        return "⚠️ Please enter a topic.", gr.update(visible=False), "Ready"
    
    try:
        # Step A: Run the M3 pipeline (which internally calls M1 and M2)
        report = milestone3.run_milestone_3_pipeline(topic, int(count))
        
        # Step B: Update the global session state so M4 can access this data later
        session.topic = topic
        session.current_report = report
        
        # Step C: Retrieve the processed data file created by Milestone 2
        # This file contains the raw findings needed for accurate AI revisions.
        safe_topic = milestone3.milestone2.milestone1.sanitize_filename(topic)
        data_path = os.path.join(milestone3.milestone2.PROCESSED_DIR, safe_topic, "processed_data.json")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            session.raw_data = json.load(f)
            
        # Return: 1. The report text | 2. Make the revision section visible | 3. Update status label
        return report, gr.update(visible=True), "✅ Initial Draft Generated"
    except Exception as e:
        return f"### 🛑 Error:\n{str(e)}", gr.update(visible=False), "Error"

def run_revision_cycle():
    """
    Triggers the Milestone 4 Review Phase: Critique -> Revise -> Evaluate.
    """
    if not session.current_report:
        return "No report to revise.", "", "Error"
    
    try:
        # Step A: Use M4 to critique the existing report for weaknesses
        critique = milestone4.critique_draft("Full Review", session.current_report)
        
        # Step B: Use M4 to rewrite the report based on the critique and source data
        revised = milestone4.revise_draft("Full Review", session.current_report, critique, session.raw_data)
        
        # Step C: Use M4 to give the final document an academic quality score
        quality = milestone4.evaluate_quality(revised)
        
        # Step D: Update the session with the new, improved report
        session.current_report = revised
        
        # Return: 1. Final Report + Score | 2. The Critique suggestions | 3. Update status label
        return f"{revised}\n\n---\n### 📊 Quality Eval\n{quality}", f"**Critique:**\n{critique}", "✅ Milestone 4 Complete"
    except Exception as e:
        return f"### 🛑 Revision Error:\n{str(e)}", "", "Error"

# --- 3. UI LAYOUT CONSTRUCTION ---

# gr.Blocks allows for complex, custom layouts beyond simple inputs and outputs.
with gr.Blocks(title="AI Systematic Reviewer v4.0") as demo:
    gr.Markdown("# 🎓 AI Systematic Reviewer (Milestone 4)")
    
    # Input Row: Collects the user's research parameters
    with gr.Row():
        topic_in = gr.Textbox(label="Topic", placeholder="e.g. GANs in Healthcare")
        count_in = gr.Slider(1, 5, value=2, step=1, label="Number of Papers")
    
    # Primary Trigger Button
    start_btn = gr.Button("🚀 Start Research", variant="primary")
    
    # Milestone 4 UI Section: Starts as 'hidden' (visible=False)
    # It only appears once the initial research draft is ready.
    with gr.Column(visible=False) as m4_ui:
        gr.Markdown("---")
        critique_display = gr.Markdown() # Shows the AI reviewer's feedback
        revise_btn = gr.Button("🔄 Critique & Revise (M4)", variant="secondary")
    
    # Final Output Display
    output_display = gr.Markdown() # Shows the final systematic review report
    status = gr.Label(value="Ready") # Visual feedback for the user

    # EVENT HANDLING: Connecting the UI buttons to the backend Python functions.
    # .click defines (function to run, inputs to take, UI elements to update)
    start_btn.click(
        run_research_phase, 
        inputs=[topic_in, count_in], 
        outputs=[output_display, m4_ui, status]
    )
    
    revise_btn.click(
        run_revision_cycle, 
        outputs=[output_display, critique_display, status]
    )

# --- 4. SERVER LAUNCH ---
if __name__ == "__main__":
    print("⚡ Starting Gradio... Please use the public link if local fails.")
    
    # Launch Settings Explained:
    # - server_name="127.0.0.1": Forces local hosting
    # - share=True: Creates a temporary public URL (.gradio.live) so you can access it anywhere
    # - debug=True: Prints all errors and AI activity directly into your terminal
    # - theme=gr.themes.Soft(): Applies a modern, rounded visual style to the interface
    demo.launch(
        server_name="127.0.0.1", 
        share=True, 
        debug=True,
        theme=gr.themes.Soft()
    )