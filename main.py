
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
from handlers.video_handlers import generate_video, generate_video_v31, generate_video_v31_with_validation, show_generated_videos, show_merged_videos
from handlers.audio_handlers import generate_audio, show_generated_audios, merge_audios
from handlers.ui_handlers import show_story_details, show_images_and_prompts, show_images_and_prompts_v31, play_audio, update_character_visibility, show_story
from utils.video_ts import merge_videos_moviepy
from utils.config import VIDEOS_DIR
from utils.status_helper import append_status, format_status_display

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

    # Global state for status messages (defined early so all handlers can use it)
    status_messages = gr.State([])

    # Tab 1: Idea Tab
    ta_idea, dd_style, cb_use_agent, cb_use_adk, btn_random_idea, btn_generate_story = idea_tab()

    # Toggle ADK checkbox visibility based on agent checkbox
    def toggle_adk_visibility(use_agent):
        return gr.update(visible=use_agent, interactive=use_agent)

    cb_use_agent.change(
        toggle_adk_visibility,
        inputs=[cb_use_agent],
        outputs=[cb_use_adk]
    )

    # Helper function: Generate random idea with status
    def generate_random_idea_with_status(current_messages):
        """Wrapper for generate_random_idea that emits status updates."""
        messages = append_status(
            "Generating random story idea...",
            current_messages,
            "PROGRESS"
        )

        try:
            result = generate_random_idea()
            messages = append_status(
                "Random idea generated!",
                messages,
                "SUCCESS"
            )
            return result, messages, format_status_display(messages)
        except Exception as e:
            messages = append_status(
                f"Random idea generation failed: {str(e)}",
                messages,
                "ERROR"
            )
            return "", messages, format_status_display(messages)

    # Helper function: Developing story with status updates
    def developing_story_with_status(*args):
        """Wrapper for developing_story that emits status updates."""
        # Extract status_messages (last argument) and handler arguments
        *handler_args, current_messages = args

        # Parse key info from args for status messages
        number_of_scenes = int(handler_args[33])
        style = handler_args[36]
        use_scene_adk = handler_args[37] if len(handler_args) > 35 else True

        # Initial status
        messages = append_status(
            f"Starting scene development ({number_of_scenes} scenes, {style} style, ADK={'ON' if use_scene_adk else 'OFF'})",
            current_messages,
            "PROGRESS"
        )
        yield messages, format_status_display(messages)

        # Call the actual handler
        try:
            result = developing_story(*handler_args)

            # Success status
            messages = append_status(
                f"Scene development complete! Generated {number_of_scenes} scenes",
                messages,
                "SUCCESS"
            )
            yield messages, format_status_display(messages)

        except Exception as e:
            # Error status
            messages = append_status(
                f"Scene development failed: {str(e)}",
                messages,
                "ERROR"
            )
            yield messages, format_status_display(messages)
            raise

    # Tab 2: Story Tab
    (sl_number_of_characters, character_rows, character_images, character_names,character_sexs, character_voices,
     character_descriptions, btn_generate_character_images, btn_update_story, ta_setting,
     ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_story_model, cb_use_scene_adk, btn_developing) = story_tab()

    # Tab 3: Visual Storyboard Tab
    (scene_images, scene_texts, scene_audios_dropdown, scene_audios, script_texts,
     character_list, veo_model_id, cb_generate_audio, btn_generate_videos,
     btn_generate_audios, btn_merge_audios, storyboard_rows) = visual_storyboard_tab(sl_number_of_scenes)

    # Tab 4: Visual Storyboard v31 Tab
    (scene_images_v31, scene_texts_v31, script_texts_v31, veo_model_id_v31, cb_generate_audio_v31,
     cb_enable_quality_validation, sl_quality_threshold, quality_report,
     btn_generate_videos_v31, storyboard_rows_v31) = visual_storyboard_v31_tab(sl_number_of_scenes)

    # Tab 5: Short Ingredients Tab
    short_ingredients, btn_merge_videos = short_ingredients_tab()

    # Tab 6: Merged Tab/BigThing
    merged_video = big_thing_tab()

    # Global Status Output (at bottom of UI, after all tabs)
    with gr.Row():
        gr.Markdown("---")
    with gr.Row():
        status_output = gr.Textbox(
            label="📊 Real-time Status",
            value="🟢 Ready",
            lines=8,
            max_lines=200,
            interactive=False,
            show_copy_button=True,
            elem_id="global_status_output"
        )

    # =================================================================
    # Button Click Handlers (after all UI components are defined)
    # =================================================================

    # Wire random idea button
    btn_random_idea.click(
        generate_random_idea_with_status,
        inputs=[status_messages],
        outputs=[ta_idea, status_messages, status_output]
    )

    # Helper function: Generate character images with status
    def generate_character_images_with_status(*args):
        """Wrapper for generate_character_images that emits status updates."""
        *handler_args, current_messages = args
        number_of_characters = int(handler_args[0])

        # Initial status
        messages = append_status(
            f"Generating character images ({number_of_characters} character{'s' if number_of_characters > 1 else ''})...",
            current_messages,
            "PROGRESS"
        )
        yield [None] * 6 + [messages, format_status_display(messages)]

        # Call the actual handler
        try:
            result = generate_character_images(*handler_args)

            # Success status
            messages = append_status(
                f"Character images generated successfully!",
                messages,
                "SUCCESS"
            )
            yield list(result) + [messages, format_status_display(messages)]

        except Exception as e:
            # Error status
            messages = append_status(
                f"Character image generation failed: {str(e)}",
                messages,
                "ERROR"
            )
            yield [None] * 6 + [messages, format_status_display(messages)]
            raise

    # Generate character images
    btn_generate_character_images.click(
        generate_character_images_with_status,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style, status_messages],
        outputs=character_images + [status_messages, status_output]
    )
    # Generate story now populates character fields
    def populate_characters(idea, style, use_agent, use_adk, current_messages):
        # Add initial status
        messages = append_status(
            f"Generating story from idea (Agent: {'ADK' if use_adk else 'Original' if use_agent else 'None'})...",
            current_messages,
            "PROGRESS"
        )
        status_update = messages, format_status_display(messages)

        try:
            character_list, setting, plot = generate_story(idea, style=style, use_agent=use_agent, use_adk=use_adk)
            result = show_story()

            # Success status
            messages = append_status(
                f"Story generated! {len(character_list)} character(s) created",
                messages,
                "SUCCESS"
            )
            return result + [messages, format_status_display(messages)]

        except Exception as e:
            # Error status
            messages = append_status(
                f"Story generation failed: {str(e)}",
                messages,
                "ERROR"
            )
            # Return empty results with error status
            empty_result = show_story()
            return empty_result + [messages, format_status_display(messages)]

    generate_story_step1 = btn_generate_story.click(
        populate_characters,
        inputs=[ta_idea, dd_style, cb_use_agent, cb_use_adk, status_messages],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot, status_messages, status_output]
    )
    generate_story_step1.then(
        generate_character_images_with_status,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style, status_messages],
        outputs=character_images + [status_messages, status_output]
    )
    # Update the number of charaters and triggers to generating the new story
    def update_character_count(number_of_characters, idea, style, use_agent, use_adk, current_messages):
        # Add status
        messages = append_status(
            f"Updating to {number_of_characters} character(s)...",
            current_messages,
            "PROGRESS"
        )

        try:
            character_rows = update_character_visibility(number_of_characters)
            characters, setting, plot = generate_story(idea + f" Number of characters: {number_of_characters}", style=style, use_agent=use_agent, use_adk=use_adk)
            result = show_story()

            # Success status
            messages = append_status(
                f"Story updated with {number_of_characters} character(s)",
                messages,
                "SUCCESS"
            )
            return result + [messages, format_status_display(messages)]

        except Exception as e:
            messages = append_status(
                f"Update failed: {str(e)}",
                messages,
                "ERROR"
            )
            empty_result = show_story()
            return empty_result + [messages, format_status_display(messages)]

    update_character_step1=sl_number_of_characters.release(
        fn=update_character_count,
        inputs=[sl_number_of_characters, ta_idea, dd_style, cb_use_agent, cb_use_adk, status_messages],
        outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting, ta_plot, status_messages, status_output],
        queue=False
    )
    update_character_step1.then(
        generate_character_images_with_status,
        inputs=[sl_number_of_characters] + character_names + character_sexs + character_voices + character_descriptions + [dd_style, status_messages],
        outputs=character_images + [status_messages, status_output]
    )
        
    # Developing story with status updates
    developing_story_step1 = btn_developing.click(
        developing_story_with_status,
        inputs=[sl_number_of_characters] + character_images + character_names + character_sexs + character_voices + character_descriptions +
               [ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_story_model, dd_style, cb_use_scene_adk, status_messages],
        outputs=[status_messages, status_output]
    )
    developing_story_step2 = developing_story_step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts + script_texts)
    developing_story_step2.then(show_images_and_prompts_v31, inputs=[sl_number_of_scenes], outputs=scene_images_v31 + scene_texts_v31 + script_texts_v31)

    # Video generation handlers
    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_videos_v31.click(
        generate_video_v31_with_validation,
        inputs=scene_images_v31 + scene_texts_v31 + [veo_model_id_v31, cb_generate_audio_v31, cb_enable_quality_validation, sl_quality_threshold],
        outputs=[short_ingredients, quality_report]
    )
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    # Load the existed images and prompts if any
    demo.load(load_idea, inputs=None, outputs=[ta_idea])
    demo.load(show_story, inputs=None, outputs=[sl_number_of_characters] + character_rows + character_images + character_names + character_sexs + character_voices + character_descriptions + [ta_setting] + [ta_plot])
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts + script_texts)
    demo.load(show_images_and_prompts_v31, inputs=[sl_number_of_scenes], outputs=scene_images_v31 + scene_texts_v31 + script_texts_v31)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])



# Main
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    demo.launch(server_name="0.0.0.0", server_port=port)
