import gradio as gr
import json
import os
from utils.llm import call_llm
from utils.logger import logger
from utils.prompt_templates import generate_story_prompt, update_story_prompt, develop_story_prompt
from utils.gen_image import gen_images, gen_images_by_banana
from utils.acceptance import to_snake_case_v2
from PIL import Image
from io import BytesIO
from handlers.ui_handlers import check_folder, clear_temp_files
from utils.config import (
    CHARACTERS_JSON,
    SETTING_TXT,
    PLOT_TXT,
    STORY_JSON,
    CHARACTERS_DIR,
    VIDEOS_DIR,
)
def save_characters(characters):
    with open(CHARACTERS_JSON, "w") as f:
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
    with open(SETTING_TXT, "w") as f:
        f.write(setting)

def save_plot(plot):
    with open(PLOT_TXT, "w") as f:
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
    system_instruction, prompt = update_story_prompt(idea, characters)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    json_response = json.loads(string_response)
    setting = json_response["setting"]
    plot = json_response["plot"]

    save_characters(characters)
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
    clear_temp_files("tmp/default/characters", ".*")

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
            # Full-body shot of the character: ***{character_names[i]}*** 
            # Sex: ***{character_sexs[i]}***
            # A ***{style}*** image of ***{character_descriptions[i]}***
            # Background: ***The background must be a solid, clean, plain white background, isolating the character.***
        """

        images_data=gen_images_by_banana(char_prompt)
        image = Image.open(BytesIO(images_data[0]))
        image_path = f"tmp/default/characters/{to_snake_case_v2(character_names[i])}.png"
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
    character_image_dict={}
    
    # Build characters string for the prompt
    characters = []
    for i in range(number_of_characters):
        if character_names[i] and character_descriptions[i]:
            characters.append({
                "name": character_names[i],
                "sex": character_sexs[i],
                "voice": character_voices[i],
                "description": character_descriptions[i]
            })
        if character_names[i] and character_descriptions[i]:
            character_image_dict[character_names[i]]=character_images[i]

    # Clear old video files
    check_folder("tmp/default/videos")
    clear_temp_files("tmp/default/videos", ".*")

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
    for i, scene in enumerate(json_response["story_scenes"],1):
        reference_images = []

        # Collect valid reference images for characters in this scene
        for n in scene["characters"]:
            # Handle both string names and dict objects with 'name' field
            character_name = n["name"] if isinstance(n, dict) else n
            img_path = f"tmp/default/characters/{to_snake_case_v2(character_name)}.png"
            if os.path.exists(img_path):
                reference_images.append(img_path)
                logger.info(f"Scene {i}: Added reference image for character '{character_name}': {img_path}")
            else:
                logger.warning(f"Scene {i}: Reference image not found for character '{character_name}': {img_path}")

        # Limit to max 3 reference images (API best practice)
        if len(reference_images) > 3:
            logger.warning(f"Scene {i}: Found {len(reference_images)} reference images, using only first 3")
            reference_images = reference_images[:3]

        # Extract character names (handle both string and dict formats)
        character_names_in_scene = [
            c["name"] if isinstance(c, dict) else c
            for c in scene["characters"]
        ]

        # Try with reference images first, fallback to no references if it fails
        try:
            image_prompt = f"""
                Generate a key image for the scene based on following description:
                - location: ***{scene["location"]}***
                - atmosphere: ***{scene["atmosphere"]}***
                - characters: ***{character_names_in_scene}***

                Notice:
                - All characters must be front face and aligned with referenced character image.
            """
            if reference_images:
                logger.info(f"Scene {i}: Generating with {len(reference_images)} reference image(s)")
                generated_image_data = gen_images_by_banana(prompt=image_prompt, reference_images=reference_images)[0]
            else:
                logger.info(f"Scene {i}: Generating without reference images")
                generated_image_data = gen_images_by_banana(prompt=image_prompt)[0]
        except Exception as e:
            logger.error(f"Scene {i}: Failed with reference images: {e}")
            logger.info(f"Scene {i}: Retrying without reference images")
            generated_image_data = gen_images_by_banana(prompt=image_prompt)[0]

        image = Image.open(BytesIO(generated_image_data))
        image.save(f"tmp/default/videos/scene_{i}.png")
        logger.info(f"Scene {i}: Saved image to tmp/default/videos/scene_{i}.png")

        video_prompt_file = f"tmp/default/videos/scene_prompt_{i}.txt"
        with open(video_prompt_file, "w") as f:
            f.write(json.dumps(scene, indent=4))

        video_script_file = f"tmp/default/videos/scene_script_{i}.txt"
        with open(video_script_file, "w") as f:
            f.write(json.dumps(scene["dialogue"], indent=4))

    return json.dumps(json_response, indent=4)
