
import gradio as gr

def short_ingredients_tab():
    with gr.Tab("4. Short ingredients >>"):
        with gr.Row():
            short_ingredients=gr.Gallery(label="Generated videos", type="filepath", show_label=False, elem_id="gallery", columns=[3], rows=[4], object_fit="contain", height="auto")
        with gr.Row():
            num_scene = gr.Number(label="Scene number", visible=False, value=1, minimum=1, maximum=12, interactive=True)
            upload_btn = gr.UploadButton(label="Replace scene", visible=False, file_count="single", file_types=["mp4"], interactive=True)
        with gr.Row():
            btn_merge_videos = gr.Button("Merge videos")
    return short_ingredients, btn_merge_videos, num_scene, upload_btn
