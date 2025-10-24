
import os
import gradio as gr


from ui.idea_tab import idea_tab
from ui.story_tab import story_tab
from ui.visual_storyboard_tab import visual_storyboard_tab
from ui.visual_storyboard_v31_tab import visual_storyboard_v31_tab
from ui.short_ingredients_tab import short_ingredients_tab
from ui.big_thing_tab import big_thing_tab

from handlers.idea_handlers import generate_random_idea, load_idea
from handlers.story_handlers import generate_story, update_story, developing_story, generate_character_images
from handlers.video_handlers import generate_video, generate_video_v31, show_generated_videos, show_merged_videos
from handlers.audio_handlers import generate_audio, show_generated_audios, merge_audios
from handlers.ui_handlers import show_images_and_prompts, show_images_and_prompts_v31, play_audio, update_character_visibility, show_story
from utils.video_ts import merge_videos_moviepy
from utils.config import VIDEOS_DIR

with gr.Blocks(
    theme=gr.themes.Glass(),
    title="Story GeN Studio • AI Video Generation",
    css="""
        /* Tab title styling */
        .tab-nav button,
        .tabs button,
        button[role="tab"],
        .svelte-1b6s6s button {
            font-size: 1.25em !important;
            font-weight: 700 !important;
            padding: 10px 16px !important;
            line-height: 1.2 !important;
        }

        /* Fix TextArea scrollbar visibility */
        textarea {
            overflow-y: auto !important;
            overflow-x: auto !important;
        }

        /* Ensure scrollbar is always visible when content overflows */
        textarea:not(:focus) {
            overflow-y: auto !important;
        }
    """,
    js="""
    function() {
        const params = new URLSearchParams(window.location.search);
        if (!params.has('__theme')) {
            document.body.classList.remove('dark');
            document.body.classList.add('light');
        }

        // Make tab titles bigger
        setTimeout(() => {
            const tabButtons = document.querySelectorAll('button[role="tab"]');
            tabButtons.forEach(btn => {
                btn.style.fontSize = '1.25em';
                btn.style.fontWeight = '700';
                btn.style.padding = '10px 16px';
                btn.style.lineHeight = '1.2';
            });

            // Fix textarea scrollbar visibility
            const textareas = document.querySelectorAll('textarea');
            textareas.forEach(textarea => {
                textarea.style.overflowY = 'auto';
                textarea.style.overflowX = 'auto';
                // Force reflow to make browser recalculate scrollbar visibility
                textarea.offsetHeight;
            });
        }, 100);
    }
    """
) as demo:
    with gr.Row():
        with gr.Column(scale=20):
            gr.Markdown("""
                <div style="display: flex; align-items: center; gap: 16px; padding: 10px 0;">
                    <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg"
                         alt="Gemini" style="width: 52px; height: 52px;">
                    <div>
                        <h1 style="margin: 0; font-size: 2.2em; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            Story GeN Studio
                        </h1>
                        <p style="margin: 4px 0 0 0; opacity: 0.75; font-size: 0.95em;">
                            From imagination to screen • Powered by Google AI
                        </p>
                    </div>
                </div>
            """)
        with gr.Column(scale=1):
            gr.Textbox(value="", interactive=False, visible=False)
            # gr.Button("Logout", link="/logout", scale=1)
    # Tab 1: Idea Tab
    ta_idea, dd_style, cb_use_agent, btn_random_idea, btn_generate_story = idea_tab()
    btn_random_idea.click(
        generate_random_idea,
        inputs=None,
        outputs=[ta_idea]
    )

    # Tab 2: Story Tab
    (sl_number_of_characters, character_rows, character_images, character_names,character_sexs, character_voices,
     character_descriptions, btn_generate_character_images, btn_update_story, ta_setting,
     ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_story_model, btn_developing,
     ta_developed_story) = story_tab()
    # Generate character images
    btn_generate_character_images.click(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )
    # Generate story now populates character fields
    def populate_characters(idea, style, use_agent):
        MAX_CHARACTERS = 6
        character_list, setting, plot = generate_story(idea, style=style, use_agent=use_agent)
        return show_story()
    generate_story_step1 = btn_generate_story.click(
        populate_characters,
        inputs=[ta_idea, dd_style, cb_use_agent],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot]
    )
    generate_story_step1.then(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )
    # Update the number of charaters and triggers to generating the new story
    def update_character_count(number_of_characters, idea, style, use_agent):
        character_rows = update_character_visibility(number_of_characters)
        characters, setting, plot = generate_story(idea + f" Number of characters: {number_of_characters}", style=style, use_agent=use_agent)
        return show_story()

    update_character_step1=sl_number_of_characters.release(
        fn=update_character_count,
        inputs=[sl_number_of_characters, ta_idea, dd_style, cb_use_agent],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot],
        queue=False
    )
    update_character_step1.then(
        generate_character_images,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style],
        outputs=character_images
    )

    # Tab 3: Visual Storyboard Tab
    (scene_images, scene_texts, scene_audios_dropdown, scene_audios,
     character_list, veo_model_id, cb_generate_audio, btn_generate_videos,
     btn_generate_audios, btn_merge_audios, storyboard_rows) = visual_storyboard_tab(sl_number_of_scenes)
    # Developing story
    developing_story_step1 = btn_developing.click(
        developing_story,
        inputs=[sl_number_of_characters] + character_images + character_names + character_sexs + character_voices + character_descriptions +
               [ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_story_model, dd_style],
        outputs=[ta_developed_story]
    )
    developing_story_step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
 

    # Tab 3: Visual Storyboard v31 Tab
    (scene_images_v31, scene_texts_v31, veo_model_id_v31, cb_generate_audio_v31, 
     btn_generate_videos_v31, storyboard_rows_v31 ) = visual_storyboard_v31_tab(sl_number_of_scenes)
    developing_story_step1.then(show_images_and_prompts_v31, inputs=[sl_number_of_scenes], outputs=scene_images_v31 + scene_texts_v31)

    # Tab 4: Short Ingredients Tab
    short_ingredients, btn_merge_videos = short_ingredients_tab()
    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_videos_v31.click(
        generate_video_v31,
        inputs=scene_images_v31 + scene_texts_v31 + [veo_model_id_v31, cb_generate_audio], outputs=[short_ingredients]
    )
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)

    # Tab 5: Merged Tab/BigThing
    merged_video = big_thing_tab()
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    # Load the existed images and prompts if any
    demo.load(load_idea, inputs=None, outputs=[ta_idea])
    demo.load(show_story, inputs=None, outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting] + [ta_plot])
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_images_and_prompts_v31, inputs=[sl_number_of_scenes], outputs=scene_images_v31 + scene_texts_v31)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])



# Main
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    demo.launch(server_name="0.0.0.0", server_port=port)
