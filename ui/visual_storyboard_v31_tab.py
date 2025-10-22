
import gradio as gr
from handlers.ui_handlers import play_audio, update_storyboard_visibility

def visual_storyboard_v31_tab(sl_number_of_scenes):
    with gr.Tab("3. Visual Storyboard v31 >>"):
        max_scenes = 12
        storyboard_rows_v31 = []
        scene_images_v31 = []
        scene_texts_v31 = []

        for i in range(max_scenes):
            with gr.Row(visible=(i < sl_number_of_scenes.value)) as row:
                storyboard_rows_v31.append(row)
                scene_images_v31.append(gr.Gallery(label=f"Scene #{i+1}: references"))
                with gr.Column(scale=2):
                    scene_texts_v31.append(gr.TextArea(label=f"Prompt #{i+1}", lines=10, interactive=True))

        sl_number_of_scenes.change(
            fn=update_storyboard_visibility,
            inputs=[sl_number_of_scenes],
            outputs=storyboard_rows_v31,
            queue=False
        )

        with gr.Row():
            veo_model_id_v31 = gr.Dropdown(
                label="Model for generating videos",
                choices=["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"],
                value="veo-3.1-generate-preview",
                interactive=True
            )
            cb_generate_audio_v31 = gr.Dropdown(
                label="Generate audio",
                choices=["true", "false"],
                value="true",
                interactive=True
            )
        with gr.Row():
            btn_generate_videos_v31 = gr.Button("Generate videos")
            
    return scene_images_v31, scene_texts_v31, veo_model_id_v31, cb_generate_audio_v31, btn_generate_videos_v31, storyboard_rows_v31

