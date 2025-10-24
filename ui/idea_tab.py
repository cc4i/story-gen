
import gradio as gr

def idea_tab():
    with gr.Tab("✨ The Spark"):
        with gr.Row():
            ta_idea = gr.TextArea(label="What's the Idea", lines=8,
                value="""
                    The Path Engine is built from the ground up around a central, all-powerful AI. It's a perfect fit! We could also weave a powerful AI into the other concepts, but the story of a system designed for "perfect" lives feels like the strongest starting point.
                """)
        with gr.Row():
            dd_style = gr.Dropdown(choices=["Studio Ghibli", "Anime", "Photorealistic", "Pencil Sketch", "Oil Painting", "Matte Painting"], label="Style", interactive=True, value="Studio Ghibli")
        with gr.Row():
            cb_use_agent = gr.Checkbox(
                label="🤖 Use AI Agent (Self-Critique & Refinement)",
                value=True,
                info="Enable automatic story improvement through iterative refinement"
            )
        with gr.Row():
            cb_use_adk = gr.Checkbox(
                label="🚀 Use Google ADK Agent (Advanced Multi-Agent System)",
                value=True,
                info="Enable ADK-based LoopAgent with specialized sub-agents for higher quality results"
            )
        with gr.Row():
            btn_random_idea = gr.Button("Genarate random idea")
            btn_generate_story = gr.Button("Generate story")
    return ta_idea, dd_style, cb_use_agent, cb_use_adk, btn_random_idea, btn_generate_story
