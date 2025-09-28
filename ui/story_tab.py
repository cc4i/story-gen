
import gradio as gr

def story_tab():
    with gr.Tab("2. Story >>"):
        with gr.Row():
            ta_characters = gr.TextArea(label="Characters", lines=4, value="""Dr. Elara Vance: (20s) a mid-level Data Ecologist, her job is to study the "waste data" from the AI.""")
        with gr.Row():
            ta_setting = gr.TextArea(label="Setting", lines=2, value="""When she runs it through a deep-level simulation, she's horrified by what she discovers.""")
        with gr.Row():
            ta_plot = gr.TextArea(label="Plot", lines=5, value="""Elara then discovers more of these "ghosts" in the data waste—the digital echoes of humanity's greatest suppressed minds.""")
        with gr.Row():
            sl_number_of_scenes = gr.Slider(label="Number of Scenes", minimum=1, maximum=12, step=1, interactive=True, value=3)
            sl_duration_per_scene = gr.Slider(label="Duration per Scene", minimum=5, maximum=8, step=1, interactive=True, value=8)
            dd_style = gr.Dropdown(choices=["Studio Ghibli", "Anime", "Photorealistic", "Pencil Sketch", "Oil Painting", "Matte Painting"], label="Style", interactive=True, value="Studio Ghibli") 
        with gr.Row():
            btn_developing = gr.Button("Developing")
        with gr.Row():
            tb_developed_story = gr.TextArea(label="Developed story")
    return ta_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style, btn_developing, tb_developed_story
