
import gradio as gr

def big_thing_tab():
    with gr.Tab("🎊 Premiere Night"):
        with gr.Row():
            merged_video = gr.Video(label="Merged video", show_label=False, elem_id="video", height="auto")
    return merged_video
