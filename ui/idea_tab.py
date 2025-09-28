
import gradio as gr

def idea_tab():
    with gr.Tab("1. Idea >>"):
        with gr.Row():
            ta_idea = gr.TextArea(label="What's the Idea", lines=4, 
                value="""
                    The Path Engine is built from the ground up around a central, all-powerful AI. It's a perfect fit! We could also weave a powerful AI into the other concepts, but the story of a system designed for "perfect" lives feels like the strongest starting point.
                """)
        with gr.Row():
            btn_random_idea = gr.Button("Genarate random idea")
            btn_generate_story = gr.Button("Generate story")
    return ta_idea, btn_random_idea, btn_generate_story
