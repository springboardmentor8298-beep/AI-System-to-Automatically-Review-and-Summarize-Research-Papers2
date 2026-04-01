import gradio as gr
from main import run_pipeline
from generation.reviewer import evaluate_content, revise_content
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_system(topic):
    output = run_pipeline(topic)
    return output


def critique_and_revise(content):
    evaluation = evaluate_content(content)
    revised = revise_content(content)
    return evaluation, revised


with gr.Blocks() as app:
    gr.Markdown("# 🧠 AI Research Paper Generator")
    gr.Markdown("Generate structured research summaries using AI")

    with gr.Row():
        topic_input = gr.Textbox(label="Enter Research Topic", scale=3)
        generate_btn = gr.Button("🚀 Generate", scale=1)

    output_box = gr.Textbox(
        label="📄 Generated Research Paper",
        lines=20
    )

    with gr.Row():
        critique_btn = gr.Button("🔍 Critique")
        revise_btn = gr.Button("🛠 Revise")

    evaluation_box = gr.Textbox(label="📊 Evaluation", lines=8)
    revised_box = gr.Textbox(label="✨ Revised Output", lines=20)

    # Actions
    generate_btn.click(run_system, inputs=topic_input, outputs=output_box)

    critique_btn.click(
        lambda x: evaluate_content(x),
        inputs=output_box,
        outputs=evaluation_box
    )

    revise_btn.click(
        lambda x: revise_content(x),
        inputs=output_box,
        outputs=revised_box
    )

app.launch()