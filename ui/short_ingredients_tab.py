
import gradio as gr

def short_ingredients_tab():
    with gr.Tab("4. Short ingredients >>"):
        with gr.Row():
            short_ingredients=gr.Gallery(label="Generated videos", type="filepath", show_label=False, elem_id="gallery", columns=[3], rows=[4], object_fit="contain", height="auto")
        with gr.Row():
            btn_merge_videos = gr.Button("Merge videos")
    return short_ingredients, btn_merge_videos
