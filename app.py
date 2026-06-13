"""
Gradio query interface for the BU/NEU Unofficial Student Guide RAG system.

Run with:
    python app.py
Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from rag import query


def handle_query(question: str) -> tuple[str, str]:
    if not question.strip():
        return "Please enter a question.", ""

    answer, sources = query(question)
    sources_text = "\n".join(f"* {s}" for s in sources)
    return answer, sources_text


with gr.Blocks(title="BU & NEU Unofficial Student Guide") as demo:
    gr.Markdown("""
    # BU & NEU Unofficial Student Guide
    Ask anything about **Boston University** or **Northeastern University** —
    dining, housing, courses, co-op, transit, and campus life.
    Answers are grounded in student-written documents only.
    """)

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                label="Your question",
                placeholder="e.g. What is the best dining hall at BU?",
                lines=2,
            )
            btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(label="Answer", lines=10, interactive=False)
        with gr.Column(scale=1):
            sources_box = gr.Textbox(label="Retrieved from", lines=10, interactive=False)

    gr.Examples(
        examples=[
            "What is the best dining hall at Boston University?",
            "How does Northeastern's co-op program work?",
            "Which MBTA line serves Northeastern University?",
            "What neighborhoods do BU students live off-campus?",
            "What makes the malloc lab in CS 3650 at Northeastern so difficult?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
