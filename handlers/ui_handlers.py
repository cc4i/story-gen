import json
import gradio as gr
import os
import re
import json
from utils.acceptance import to_snake_case_v2
from utils.logger import logger
from utils.config import (
    STORY_JSON,
    CHARACTERS_JSON,
    SETTING_TXT,
    PLOT_TXT,
    CHARACTERS_DIR,
    VIDEOS_DIR,
)

def check_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def clear_temp_files(path: str, extension: str):
    check_folder(path)
    for file in os.listdir(path):
        if extension == ".*":
            os.remove(os.path.join(path, file))
        elif file.endswith(extension):
            os.remove(os.path.join(path, file))

def play_audio(audio_file):
    logger.debug(f"Playing audio file: {audio_file}")
    return audio_file

def update_storyboard_visibility(count):
    return [gr.update(visible=i < int(count)) for i in range(12)]

def update_character_visibility(count):
    return [gr.update(visible=i < int(count)) for i in range(6)]

def show_story():
    MAX_CHARACTERS = 6
    characters_file_path = CHARACTERS_JSON
    setting_file_path = SETTING_TXT
    plot_file_path = PLOT_TXT
    characters_images_dir = CHARACTERS_DIR

    num_characters = 0
    names = [""] * MAX_CHARACTERS
    sexs = ["Male"] * MAX_CHARACTERS
    voices = ["Low"] * MAX_CHARACTERS
    descriptions = [""] * MAX_CHARACTERS
    character_image_paths = [None] * MAX_CHARACTERS
    setting = ""
    plot = ""

    try:
        if os.path.exists(characters_file_path):
            with open(characters_file_path, "r") as f:
                character_list = json.load(f)
                num_characters = len(character_list)
                logger.info(f"Loading {num_characters} characters from {characters_file_path}")

                for idx, char in enumerate(character_list):
                    if idx < MAX_CHARACTERS:
                        names[idx] = char.get("name", "")
                        sexs[idx] = char.get("sex", "Male")
                        voices[idx] = char.get("Voice", "Low")
                        descriptions[idx] = char.get("description", "")
                        if os.path.exists(characters_images_dir):
                            image_path = os.path.join(characters_images_dir, f"{to_snake_case_v2(names[idx])}.png")
                            logger.debug(f"Character {idx+1}: name={names[idx]}, image_path={image_path}")
                            if os.path.exists(image_path):
                                character_image_paths[idx] = image_path
                                logger.debug(f"Loaded character image: {os.path.basename(image_path)}")

        if os.path.exists(setting_file_path):
            with open(setting_file_path, "r") as f:
                setting = f.read()
                logger.debug(f"Loaded setting from {setting_file_path}: {len(setting)} chars")

        if os.path.exists(plot_file_path):
            with open(plot_file_path, "r") as f:
                plot = f.read()
                logger.debug(f"Loaded plot from {plot_file_path}: {len(plot)} chars")

    except Exception as e:
        logger.error(
            f"Error loading story data: {str(e)}",
            exc_info=True,
            extra={
                "characters_file": characters_file_path,
                "setting_file": setting_file_path,
                "plot_file": plot_file_path
            }
        )

    character_row_visibility = update_character_visibility(num_characters)

    return [num_characters] + character_row_visibility + character_image_paths + names + sexs + voices + descriptions + [setting, plot]

def show_images_and_prompts(number_of_scenes):
    MAX_SCENES = 12
    path = VIDEOS_DIR

    scene_image_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            # Match only files with pattern: scene_[integer].png
            if re.match(r'^scene_\d+\.png$', file):
                scene_image_files.append(os.path.join(path, file))

    # Sort by scene number (numeric, not alphabetical)
    def get_scene_number(path):
        filename = os.path.basename(path)
        match = re.search(r'scene_(\d+)\.png', filename)
        return int(match.group(1)) if match else 0

    scene_image_files.sort(key=get_scene_number)
    logger.info(f"Loaded {len(scene_image_files)} scene images from {path}")
    padded_images = (scene_image_files + [None] * MAX_SCENES)[:MAX_SCENES]

    scene_prompt_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            # Match only files with pattern: scene_prompt_[integer].txt
            if re.match(r'^scene_prompt_\d+\.txt$', file):
                scene_prompt_files.append(os.path.join(path, file))

    # Sort by scene number (numeric, not alphabetical)
    def get_prompt_number(path):
        filename = os.path.basename(path)
        match = re.search(r'scene_prompt_(\d+)\.txt', filename)
        return int(match.group(1)) if match else 0

    scene_prompt_files.sort(key=get_prompt_number)

    generated_scene_prompts = []
    for f in scene_prompt_files:
        try:
            with open(f, "r") as file:
                content = file.read().strip()
                if content:
                    # Try to parse as JSON and re-format, or just use as-is
                    try:
                        generated_scene_prompts.append(json.dumps(json.loads(content), indent=4))
                    except json.JSONDecodeError:
                        generated_scene_prompts.append(content)
                else:
                    generated_scene_prompts.append("")
        except Exception as e:
            logger.error(
                f"Error reading scene prompt file: {str(e)}",
                exc_info=True,
                extra={"file_path": f}
            )
            generated_scene_prompts.append("")

    logger.info(f"Loaded {len(generated_scene_prompts)} scene prompts")
    padded_prompts = (generated_scene_prompts + [""] * MAX_SCENES)[:MAX_SCENES]

    scene_script_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_script_") and file.endswith(".json"):
                scene_script_files.append(os.path.join(path, file))

    scene_scripts = []
    for f in scene_script_files:
        with open(f, "r") as file:
            scene_scripts.append(file.read())
    padded_scripts = (scene_scripts + [""] * MAX_SCENES)[:MAX_SCENES]

    return padded_images + padded_prompts + padded_scripts

def show_images_and_prompts_v31(number_of_scenes):
    MAX_SCENES = 12
    path = VIDEOS_DIR
    
    def get_scene_v31_number(path):
        filename = os.path.basename(path)
        match = re.search(r'scene_v31_(\d+)\.png', filename)
        return int(match.group(1)) if match else 0

    def get_character_images(num, data_json):
        character_images=[]
        for data in data_json["story_scenes"]:
            if data["scene_number"]==num:
                for n in data["characters"]:
                    # Handle both string names and dict objects with 'name' field
                    character_name = n["name"] if isinstance(n, dict) else n
                    character_images.append(f"{CHARACTERS_DIR}/{to_snake_case_v2(character_name)}.png")
        return character_images
    
    with open(STORY_JSON, "r") as f:
        story_json = json.load(f)
        
    # Collect v31 scene files
    scene_v31_files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if re.match(r'^scene_v31_\d+\.png$', file):
                scene_v31_files.append(file)

    # Sort by scene number
    scene_v31_files.sort(key=get_scene_v31_number)

    references_image_files = []
    for file in scene_v31_files:
        all_images = []
        all_images.append(os.path.join(path, file))
        n = get_scene_v31_number(file)
        character_images = get_character_images(n, story_json)
        for ci in character_images:
            if os.path.exists(ci):
                all_images.append(ci)
        references_image_files.append(all_images)

    padded_images = (references_image_files + [None] * MAX_SCENES)[:MAX_SCENES]

    scene_prompt_files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if re.match(r'^scene_prompt_v31_\d+\.txt$', file):
                scene_prompt_files.append(os.path.join(path, file))

    # Sort by scene number
    def get_prompt_v31_number(path):
        filename = os.path.basename(path)
        match = re.search(r'scene_prompt_v31_(\d+)\.txt', filename)
        return int(match.group(1)) if match else 0

    scene_prompt_files.sort(key=get_prompt_v31_number)

    generated_scene_prompts = []
    for f in scene_prompt_files:
        try:
            with open(f, "r") as file:
                content = file.read().strip()
                if content:
                    generated_scene_prompts.append(content)
                else:
                    generated_scene_prompts.append("")
        except Exception as e:
            logger.error(
                f"Error reading v31 scene prompt file: {str(e)}",
                exc_info=True,
                extra={"file_path": f}
            )
            generated_scene_prompts.append("")

    logger.info(f"Loaded {len(generated_scene_prompts)} v31 scene prompts with {len(references_image_files)} reference image sets")
    padded_prompts = (generated_scene_prompts + [""] * MAX_SCENES)[:MAX_SCENES]

    scene_script_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_script_") and file.endswith(".json"):
                scene_script_files.append(os.path.join(path, file))
    
    scene_scripts = []
    for f in scene_script_files:
        with open(f, "r") as file:
            scene_scripts.append(file.read())
    padded_scripts = (scene_scripts + [""] * MAX_SCENES)[:MAX_SCENES]

    # Return a single, flat list: all image paths, then all prompts
    # The order and length must match the `outputs` in the click event
    return padded_images + padded_prompts + padded_scripts

def show_story_details():
    pass
