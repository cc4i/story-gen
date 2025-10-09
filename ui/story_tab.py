
import gradio as gr
from handlers.ui_handlers import update_character_visibility

def story_tab():
    with gr.Tab("2. Story >>"):
        # Character section
        with gr.Row():
            gr.Markdown("### Characters")
        with gr.Row():
            sl_number_of_characters = gr.Slider(label="Number of Characters", minimum=1, maximum=6, step=1, interactive=True, value=1)

        max_characters = 6
        character_rows = []
        character_images = []
        character_names = []
        character_descriptions = []

        for i in range(max_characters):
            with gr.Row(visible=(i < 1)) as row:
                character_rows.append(row)
                with gr.Column(scale=1):
                    img = gr.Image(label=f"Character #{i+1}", type="filepath", height=200)
                    character_images.append(img)
                with gr.Column(scale=3):
                    name = gr.Textbox(label=f"Name", placeholder=f"Character {i+1} name", interactive=True)
                    desc = gr.TextArea(label=f"Description", placeholder=f"Character {i+1} description", lines=3, interactive=True)
                    character_names.append(name)
                    character_descriptions.append(desc)

        sl_number_of_characters.change(
            fn=update_character_visibility,
            inputs=[sl_number_of_characters],
            outputs=character_rows,
            queue=False
        )

        with gr.Row():
            btn_generate_characters = gr.Button("Generate Character Images")

        # Setting and Plot sections
        with gr.Row():
            ta_setting = gr.TextArea(label="Setting", lines=2, value="""When she runs it through a deep-level simulation, she's horrified by what she discovers.""")
        with gr.Row():
            ta_plot = gr.TextArea(label="Plot", lines=5, value="""Elara then discovers more of these "ghosts" in the data waste—the digital echoes of humanity's greatest suppressed minds.""")

        # Scene configuration
        with gr.Row():
            sl_number_of_scenes = gr.Slider(label="Number of Scenes", minimum=1, maximum=12, step=1, interactive=True, value=3)
            sl_duration_per_scene = gr.Slider(label="Duration per Scene", minimum=5, maximum=8, step=1, interactive=True, value=8)

        with gr.Row():
            btn_developing = gr.Button("Developing")
        with gr.Row():
            tb_developed_story = gr.TextArea(label="Developed story")

    return (sl_number_of_characters, character_images, character_names, character_descriptions,
            btn_generate_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene,
            btn_developing, tb_developed_story)
