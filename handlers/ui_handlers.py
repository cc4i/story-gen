
import gradio as gr
import os
import json
from utils.acceptance import to_snake_case_v2
from utils.config import (
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
    print(f"audio_file: {audio_file}")
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
                for idx, char in enumerate(character_list):
                    if idx < MAX_CHARACTERS:
                        names[idx] = char.get("name", "")
                        sexs[idx] = char.get("sex", "Male")
                        voices[idx] = char.get("Voice", "Low")
                        descriptions[idx] = char.get("description", "")
                        if os.path.exists(characters_images_dir):
                            image_path = os.path.join(characters_images_dir, f"{to_snake_case_v2(names[idx])}.png")
                            print(f"image_path: {image_path}")
                            if os.path.exists(image_path):
                                character_image_paths[idx] = image_path
                                print(f"character_image_paths: {character_image_paths}")

        if os.path.exists(setting_file_path):
            with open(setting_file_path, "r") as f:
                setting = f.read()

        if os.path.exists(plot_file_path):
            with open(plot_file_path, "r") as f:
                plot = f.read()

    except Exception as e:
        print(f"An unexpected error occurred in show_story: {e}")

    character_row_visibility = update_character_visibility(num_characters)

    return [num_characters] + character_row_visibility + character_image_paths + names + sexs + voices + descriptions + [setting, plot]

def show_images_and_prompts(number_of_scenes):
    MAX_SCENES = 12
    path = VIDEOS_DIR
    
    scene_image_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_") and file.endswith(".png"):
                scene_image_files.append(os.path.join(path, file))
    padded_images = (scene_image_files + [None] * MAX_SCENES)[:MAX_SCENES]
    
    scene_prompt_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_prompt_") and file.endswith(".txt"):
                scene_prompt_files.append(os.path.join(path, file))
    
    generated_scene_prompts = []
    for f in scene_prompt_files:
        with open(f, "r") as file:
            generated_scene_prompts.append(json.dumps(json.loads(file.read()), indent=4))
    padded_prompts = (generated_scene_prompts + [""] * MAX_SCENES)[:MAX_SCENES]

    return padded_images + padded_prompts
