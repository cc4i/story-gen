
import gradio as gr
from handlers.ui_handlers import play_audio, update_storyboard_visibility

def visual_storyboard_v31_tab(sl_number_of_scenes):
    with gr.Tab("🎬 The Shoot (v3.1)"):
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

        # Quality Validation Controls
        with gr.Row():
            cb_enable_quality_validation = gr.Checkbox(
                label="🔍 Enable Video Quality Validation (AI Quality Agent)",
                value=True,
                info="Automatically validate and retry low-quality videos using 4-validator system. Adds 30-50% time but dramatically improves quality."
            )
            sl_quality_threshold = gr.Slider(
                label="Quality Threshold",
                minimum=6.0,
                maximum=9.5,
                value=8.0,
                step=0.5,
                info="Videos scoring below this will be retried (max 2 attempts)"
            )

        # Quality Report Display
        with gr.Row():
            quality_report = gr.DataFrame(
                label="📊 Video Quality Report",
                headers=["Scene", "Anatomy", "Consistency", "Technical", "Overall", "Status", "Retries"],
                datatype=["number", "str", "str", "str", "str", "str", "number"],
                interactive=False,
                visible=False  # Hidden until validation runs
            )

        with gr.Row():
            btn_generate_videos_v31 = gr.Button("Generate Videos", variant="primary")

    return (scene_images_v31, scene_texts_v31, veo_model_id_v31, cb_generate_audio_v31,
            cb_enable_quality_validation, sl_quality_threshold, quality_report,
            btn_generate_videos_v31, storyboard_rows_v31)

