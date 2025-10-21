
import os
import gradio as gr
import json
import shutil
import glob

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

    ta_idea, dd_style, btn_random_idea, btn_generate_story = idea_tab()

    (sl_number_of_characters, character_rows, character_images, character_names,character_sexs, character_voices,
     character_descriptions, btn_generate_character_images, btn_update_story, ta_setting,
     ta_plot, sl_number_of_scenes, sl_duration_per_scene, btn_developing,
     tb_developed_story) = story_tab()

    (scene_images, scene_texts, scene_audios_dropdown, scene_audios, script_rows,
     character_list, veo_model_id, cb_generate_audio, btn_generate_videos,
     btn_generate_audios, btn_merge_audios, storyboard_rows) = visual_storyboard_tab(sl_number_of_scenes)
    
    short_ingredients, btn_merge_videos = short_ingredients_tab()

    merged_video = big_thing_tab()

    # Load the existed images and prompts if any
    demo.load(show_story, inputs=None, outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting] + [ta_plot])
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])


    # Generate character images
    btn_generate_character_images.click(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )

    def update_scripts(num_scenes, characters):
        character_names = [line.split(":")[0].strip()for line in characters.split("\n")]

        for i in range(num_scenes):
            with open(f"tmp/images/default/scene_script_{i+1}.txt", "r") as f:
                string_script = f.read()
                json_script = json.loads(string_script)

                # Update visibility and populate input fields with generated script
                for j in range(len(json_script)):
                    script_rows[i][j][0] = gr.update(visible=True)
                    script_rows[i][j][1] = gr.update(value=json_script[j]["character"])
                    script_rows[i][j][2] = gr.update(value=json_script[j]["dialogue"])
                    script_rows[i][j][3] = gr.update(value=float(json_script[j]["time"]))
        
        return [script_rows[i][j][k] for k in range(4) for j in range(3) for i in range(12)]


    # Story development - collect character data first
    # def develop_with_characters(*args):
    #     characters_text = collect_characters_text(*args[:13])
    #     setting = args[13]
    #     plot = args[14]
    #     num_scenes = args[15]
    #     duration = args[16]
    #     style = args[17]
    #     result = develope_story(characters_text, setting, plot, num_scenes, duration, style)
    #     return [result] + update_scripts(num_scenes, characters_text)

    step1 = btn_developing.click(
        developing_story,
        inputs=[sl_number_of_characters] + character_images + character_names + character_sexs + character_voices + character_descriptions +
               [ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style],
        outputs=[tb_developed_story] + [script_rows[i][j][k] for k in range(4) for j in range(3) for i in range(12)]
    )

    step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)

    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

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


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
