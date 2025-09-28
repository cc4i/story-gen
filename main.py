
import gradio as gr

from ui.idea_tab import idea_tab
from ui.story_tab import story_tab
from ui.visual_storyboard_tab import visual_storyboard_tab
from ui.short_ingredients_tab import short_ingredients_tab
from ui.big_thing_tab import big_thing_tab

from handlers.story_handlers import generate_story, develope_story
from handlers.video_handlers import generate_video, show_generated_videos, show_merged_videos
from handlers.audio_handlers import generate_audio, show_generated_audios, merge_audios
from handlers.ui_handlers import show_images_and_prompts, play_audio
from utils.video_ts import merge_videos_moviepy

with gr.Blocks(theme=gr.themes.Glass(), title="Story GeN/Video ") as demo:
    with gr.Row():
        with gr.Column(scale=20):
            gr.Markdown("""
                # Story GeN/Video
                Tell me a story and give back a video ... powered by <b>CC</b>
            """)
        with gr.Column(scale=1):
            gr.Textbox(value="", interactive=False, visible=False)
            gr.Button("Logout", link="/logout", scale=1)

    ta_idea, btn_random_idea, btn_generate_story = idea_tab()
    ta_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style, btn_developing, tb_developed_story = story_tab()
    scene_images, scene_texts, scene_audios_dropdown, scene_audios, veo_model_id, cb_generate_audio, btn_generate_videos, btn_generate_audios, btn_merge_audios, storyboard_rows = visual_storyboard_tab(sl_number_of_scenes)
    short_ingredients, btn_merge_videos, btn_merge_videos_with_audios = short_ingredients_tab()
    merged_video = big_thing_tab()

    # Load the existed images and prompts if any
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])

    step1 = btn_developing.click(develope_story, 
            inputs=[ta_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style], 
            outputs=[tb_developed_story])
    step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)

    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    btn_generate_story.click(generate_story, inputs=[ta_idea], outputs=[ta_characters, ta_setting, ta_plot])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
