
import json
import os
from utils.llm import call_llm
from utils.logger import logger
from utils.prompt_templates import generate_story_prompt, update_story_prompt, develop_story_prompt
from utils.gen_image import gen_images, gen_images_by_banana
from PIL import Image
from io import BytesIO
from handlers.ui_handlers import check_folder, clear_temp_files

def save_characters(characters):
    with open("tmp/default/characters.json", "w") as f:
        if isinstance(characters, str):
            char_list = []
            for line in characters.split('\n'):
                if line.strip():
                    name, desc = line.split(':', 1)
                    char_list.append({"name": name.strip(), "description": desc.strip()})
            json.dump(char_list, f, indent=4)
        else:
            json.dump(characters, f, indent=4)

def save_setting(setting):
    with open("tmp/default/setting.txt", "w") as f:
        f.write(setting)

def save_plot(plot):
    with open("tmp/default/plot.txt", "w") as f:
        f.write(plot)

def generate_story(idea):
    system_instruction, prompt = generate_story_prompt(idea)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    json_response = json.loads(string_response)
    characters = json_response["characters"]
    setting = json_response["setting"]
    plot = json_response["plot"]

    save_characters(characters)
    save_setting(setting)
    save_plot(plot)

    return characters, setting, plot

def update_story(idea, characters):
    save_characters(characters)

    system_instruction, prompt = update_story_prompt(idea, characters)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    json_response = json.loads(string_response)
    setting = json_response["setting"]
    plot = json_response["plot"]

    save_setting(setting)
    save_plot(plot)

    return setting, plot

def generate_character_images(*args):
    """Generate images for each character based on their descriptions

    Args:
        args[0]: number_of_characters (int)
        args[1:7]: character_names (6 values)
        args[7:13]: character_sexs (6 values)
        args[13:19]: character_voices (6 values)
        args[19:25]: character_descriptions (6 values)
        args[25]: style (str)
    """
    check_folder("tmp/default/characters")

    # Parse arguments
    number_of_characters = int(args[0])
    character_names = args[1:7]
    character_sexs = args[7:13]
    character_voices = args[13:19]
    character_descriptions = args[19:25]
    style = args[25]


    generated_images = []
    for i in range(number_of_characters):

        # Create character image prompt
        char_prompt = f"""
            Full-body shot of the character: ***{character_names[i]}*** 
            Sex: ***{character_sexs[i]}***
            The description of character: ***{character_descriptions[i]}***
            Style: ***{style}***
            Background: ***The background must be a solid, clean, plain white background, isolating the character.***
        """
        images_data=gen_images_by_banana(char_prompt)
        image = Image.open(BytesIO(images_data[0]))
        image_path = f"tmp/default/characters/character_{i+1}.png"
        image.save(image_path)
        generated_images.append(image_path)

    # Pad with None to match max characters (6)
    while len(generated_images) < 6:
        generated_images.append(None)

    return generated_images

def developing_story(*args):
    """Develop the full story with scenes, images, and scripts

    Args:
        args[0]: number_of_characters (int)
        args[1:7]: character_images (6 values)
        args[7:13]: character_names (6 values)
        args[13:19]: character_sexs (6 values)
        args[19:25]: character_voices (6 values)
        args[25:31]: character_descriptions (6 values)
        args[31]: setting (str)
        args[32]: plot (str)
        args[33]: number_of_scenes (int)
        args[34]: duration_per_scene (int)
        args[35]: style (str)

    Returns:
        list: [story_response] + flattened script_rows updates (144 values: 12 scenes * 3 lines * 4 fields)
    """
    import gradio as gr

    # Parse arguments
    number_of_characters = int(args[0])
    character_images = args[1:7]
    character_names = args[7:13]
    character_sexs = args[13:19]
    character_voices = args[19:25]
    character_descriptions = args[25:31]
    setting = args[31]
    plot = args[32]
    number_of_scenes = int(args[33])
    duration_per_scene = int(args[34])
    style = args[35]

    # Build characters string for the prompt
    character_lines = []
    for i in range(number_of_characters):
        if character_names[i] and character_descriptions[i]:
            character_lines.append(f"{character_names[i]}: {character_descriptions[i]}")
    characters = "\n".join(character_lines)

    # Clear old video files
    clear_temp_files("tmp/default/videos", ".*")
    check_folder("tmp/default/videos")

    # Save the story data
    save_characters(characters)
    save_setting(setting)
    save_plot(plot)

    # Generate the story development
    system_instruction, prompt = develop_story_prompt(characters, setting, plot, number_of_scenes, duration_per_scene, style)
    history = ""
    logger.info(f"Developing story with prompt: {prompt}")
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")

    # Save full string response to file
    with open("tmp/default/story.json", "w") as f:
        f.write(string_response)
    json_response = json.loads(string_response)

    # Generate images and save prompts/scripts for each scene
    for i, scene in enumerate(json_response, 1):
        image_prompt = scene["image_prompt"]

        generated_image_data = gen_images_by_banana(image_prompt)[0]

        image = Image.open(BytesIO(generated_image_data))
        image.save(f"tmp/default/videos/scene_{i}.png")

        video_prompt_file = f"tmp/default/videos/scene_prompt_{i}.txt"
        with open(video_prompt_file, "w") as f:
            f.write(scene["description"])

        video_script_file = f"tmp/default/videos/scene_script_{i}.txt"
        with open(video_script_file, "w") as f:
            f.write(json.dumps(scene["scripts"]))

    # Build script_rows updates (12 scenes * 3 lines * 4 fields)
    script_updates = []
    char_names = [line.split(":")[0].strip() for line in characters.split("\n") if line.strip()]

    for i in range(12):  # MAX_SCENES = 12
        if i < number_of_scenes:
            # Read the script file for this scene
            with open(f"tmp/default/videos/scene_script_{i+1}.txt", "r") as f:
                json_script = json.loads(f.read())

            for j in range(3):  # Up to 3 script lines per scene
                if j < len(json_script):
                    # Visible, character, dialogue, time
                    script_updates.append(gr.update(visible=True))
                    script_updates.append(gr.update(value=json_script[j]["character"]))
                    script_updates.append(gr.update(value=json_script[j]["dialogue"]))
                    script_updates.append(gr.update(value=float(json_script[j]["time"])))
                else:
                    # Hidden row
                    script_updates.append(gr.update(visible=False))
                    script_updates.append(gr.update(value=""))
                    script_updates.append(gr.update(value=""))
                    script_updates.append(gr.update(value=0.0))
        else:
            # Scene doesn't exist, hide all 3 lines
            for j in range(3):
                script_updates.append(gr.update(visible=False))
                script_updates.append(gr.update(value=""))
                script_updates.append(gr.update(value=""))
                script_updates.append(gr.update(value=0.0))

    return [string_response] + script_updates
