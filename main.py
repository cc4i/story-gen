
import os
import gradio as gr


from ui.idea_tab import idea_tab
from ui.story_tab import story_tab
from ui.visual_storyboard_tab import visual_storyboard_tab
from ui.short_ingredients_tab import short_ingredients_tab
from ui.big_thing_tab import big_thing_tab

from handlers.story_handlers import generate_story, update_story, developing_story, generate_character_images
from handlers.video_handlers import generate_video, show_generated_videos, show_merged_videos
from handlers.audio_handlers import generate_audio, show_generated_audios, merge_audios
from handlers.ui_handlers import show_images_and_prompts, play_audio, update_character_visibility, show_story
from utils.video_ts import merge_videos_moviepy
from utils.config import VIDEOS_DIR

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
    # Tab 1: Idea Tab
    ta_idea, dd_style, btn_random_idea, btn_generate_story = idea_tab()

    # Tab 2: Story Tab
    (sl_number_of_characters, character_rows, character_images, character_names,character_sexs, character_voices,
     character_descriptions, btn_generate_character_images, btn_update_story, ta_setting,
     ta_plot, sl_number_of_scenes, sl_duration_per_scene, btn_developing,
     tb_developed_story) = story_tab()
    # Generate character images
    btn_generate_character_images.click(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )
    # Generate story now populates character fields
    def populate_characters(idea):
        MAX_CHARACTERS = 6
        character_list, setting, plot = generate_story(idea)
        return show_story()
    generate_story_step1 = btn_generate_story.click(
        populate_characters,
        inputs=[ta_idea],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot]
    )
    generate_story_step1.then(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )
    # Update the number of charaters and triggers to generating the new story
    def update_character_count(number_of_characters, idea):
        character_rows = update_character_visibility(number_of_characters)
        characters, setting, plot = generate_story(idea + f" Number of characters: {number_of_characters}")
        return show_story()

    sl_number_of_characters.release(
        fn=update_character_count,
        inputs=[sl_number_of_characters, ta_idea],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot],
        queue=False
    )

    # Tab 3: Visual Storyboard Tab
    (scene_images, scene_texts, scene_audios_dropdown, scene_audios,
     character_list, veo_model_id, cb_generate_audio, btn_generate_videos,
     btn_generate_audios, btn_merge_audios, storyboard_rows) = visual_storyboard_tab(sl_number_of_scenes)
    # Developing story
    developing_story_step1 = btn_developing.click(
        developing_story,
        inputs=[sl_number_of_characters] + character_images + character_names + character_sexs + character_voices + character_descriptions +
               [ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style],
        outputs=[tb_developed_story]
    )
    developing_story_step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)

    # Tab 4: Short Ingredients Tab
    short_ingredients, btn_merge_videos = short_ingredients_tab()
    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)

    # Tab 5: Merged Tab/BigThing
    merged_video = big_thing_tab()
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    # Load the existed images and prompts if any
    demo.load(show_story, inputs=None, outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting] + [ta_plot])
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])



# Main
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
