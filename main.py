
import gradio as gr

from ui.idea_tab import idea_tab
from ui.story_tab import story_tab
from ui.visual_storyboard_tab import visual_storyboard_tab
from ui.short_ingredients_tab import short_ingredients_tab
from ui.big_thing_tab import big_thing_tab

from handlers.story_handlers import generate_story, develope_story, generate_character_images
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
    (sl_number_of_characters, character_images, character_names, character_descriptions,
     btn_generate_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene,
     dd_style, btn_developing, tb_developed_story) = story_tab()
    scene_images, scene_texts, scene_audios_dropdown, scene_audios, veo_model_id, cb_generate_audio, btn_generate_videos, btn_generate_audios, btn_merge_audios, storyboard_rows = visual_storyboard_tab(sl_number_of_scenes)
    short_ingredients, btn_merge_videos, btn_merge_videos_with_audios = short_ingredients_tab()
    merged_video = big_thing_tab()

    # Load the existed images and prompts if any
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])

    # Helper function to collect characters into text format for story development
    def collect_characters_text(*args):
        num_chars = int(args[0])
        names = args[1:7]  # Next 6 args are names
        descs = args[7:13]  # Next 6 args are descriptions

        characters_text = ""
        for i in range(num_chars):
            if names[i] and descs[i]:
                characters_text += f"{names[i]}: {descs[i]}\n"
        return characters_text

    # Generate character images
    btn_generate_characters.click(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_descriptions + [dd_style],
        outputs=character_images
    )

    # Story development - collect character data first
    def develop_with_characters(*args):
        characters_text = collect_characters_text(*args[:13])
        setting = args[13]
        plot = args[14]
        num_scenes = args[15]
        duration = args[16]
        style = args[17]
        return develope_story(characters_text, setting, plot, num_scenes, duration, style)

    step1 = btn_developing.click(
        develop_with_characters,
        inputs=[sl_number_of_characters] + character_names + character_descriptions +
               [ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style],
        outputs=[tb_developed_story]
    )
    step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)

    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    # Generate story now populates character fields
    def populate_characters(idea):
        chars, setting, plot = generate_story(idea)
        # Parse characters text and populate first character
        char_lines = [line.strip() for line in chars.split('\n') if line.strip()]
        if char_lines:
            # Split first character into name and description
            first_char = char_lines[0]
            if ':' in first_char:
                name, desc = first_char.split(':', 1)
                # Return: num_chars, 6 names, 6 descriptions, setting, plot
                return ([1] + [name.strip()] + [""] * 5 +
                       [desc.strip()] + [""] * 5 + [setting, plot])
        return [1] + [""] * 12 + [setting, plot]

    btn_generate_story.click(
        populate_characters,
        inputs=[ta_idea],
        outputs=[sl_number_of_characters] + character_names + character_descriptions + [ta_setting, ta_plot]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
