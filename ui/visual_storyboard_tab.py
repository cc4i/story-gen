
import gradio as gr
from handlers.ui_handlers import play_audio, update_storyboard_visibility

def visual_storyboard_tab(sl_number_of_scenes):
    with gr.Tab("3. Visual Storyboard >>"):
        max_scenes = 12
        storyboard_rows = []
        scene_images = []
        scene_texts = []
        scene_audios_dropdown = []
        scene_audios = []
        max_scripts = 3
        script_rows = []
        character_list = []

        for i in range(max_scenes):
            with gr.Row(visible=(i < sl_number_of_scenes.value)) as row:
                storyboard_rows.append(row)
                scene_images.append(gr.Image(label=f"Scene #{i+1}", type="filepath", scale=1))
                with gr.Column(scale=2):
                    scene_texts.append(gr.TextArea(label=f"Prompt #{i+1}", interactive=True))
                    with gr.Row():
                        with gr.Column():
                            rows = []
                            for j in range(max_scripts):
                                with gr.Row(visible=False) as row:
                                    ta_char = gr.TextArea(label=f"Character #{j+1}", interactive=True)
                                    ta_script = gr.TextArea(label=f"Script #{j+1}", interactive=True)
                                    num_start_time = gr.Number(label=f"Start Time #{j+1}", minimum=0, maximum=7, step=1, interactive=True)
                                    rows.append([row, ta_char, ta_script, num_start_time])
                            script_rows.append(rows)

                    with gr.Row():
                         audio_file_path = gr.Dropdown(label=f"Audio #{i+1}", scale=3, allow_custom_value=True, interactive=True)
                         audio_file_player = gr.Audio(type="filepath", interactive=False, scale=1)
                         audio_file_path.change(play_audio, inputs=[audio_file_path], outputs=[audio_file_player])

                         scene_audios_dropdown.append(audio_file_path)
                         scene_audios.append(audio_file_player)

        sl_number_of_scenes.change(
            fn=update_storyboard_visibility,
            inputs=[sl_number_of_scenes],
            outputs=storyboard_rows,
            queue=False
        )

        with gr.Row():
            veo_model_id = gr.Dropdown(
                label="Model for generating videos",
                choices=["veo-3.0-generate-preview", "veo-3.0-fast-generate-preview", "veo-3.0-generate-001", "veo-2.0-generate-001"],
                value="veo-3.0-generate-preview",
                interactive=True
            )
            cb_generate_audio = gr.Dropdown(
                label="Generate audio (Only for Veo3)",
                choices=["true", "false"],
                value="true",
                interactive=True
            )
        with gr.Row():
            btn_generate_videos = gr.Button("Generate videos")
            btn_generate_audios = gr.Button("Generate audios(Optional)")
            btn_merge_audios = gr.Button("Merge audios(Optional)")
            
    return scene_images, scene_texts, scene_audios_dropdown, scene_audios, script_rows, character_list, veo_model_id, cb_generate_audio, btn_generate_videos, btn_generate_audios, btn_merge_audios, storyboard_rows

