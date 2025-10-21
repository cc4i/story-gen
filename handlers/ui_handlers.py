
import gradio as gr
import os
import json

def check_folder(path):
    # check folder tmp/ and subfolder tmp/images/default
    if not os.path.exists(path):
        os.makedirs(path)

def clear_temp_files(path:str, extension:str):
    check_folder(path)
    for file in os.listdir(path):
        if extension==".*":
            os.remove(f"{path}/{file}")
        elif file.endswith(extension):
            os.remove(f"{path}/{file}")

def play_audio(audio_file):
    print(f"audio_file: {audio_file}")
    return audio_file

def update_storyboard_visibility(count):
    # The function must return an update for each row component
    return [gr.update(visible=i < int(count)) for i in range(12)]

def update_character_visibility(count):
    # The function must return an update for each character row component
    return [gr.update(visible=i < int(count)) for i in range(6)]

def show_story():
    MAX_CHARACTERS = 6
    characters_file_path = "tmp/default/characters.json"
    setting_file_path = "tmp/default/setting.txt"
    plot_file_path = "tmp/default/plot.txt"
    characters_images_dir = "tmp/default/characters"

    # Initialize variables
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

        # Load character images
        if os.path.exists(characters_images_dir):
            for i in range(MAX_CHARACTERS):
                image_path = f"{characters_images_dir}/character_{i+1}.png"
                if os.path.exists(image_path):
                    character_image_paths[i] = image_path

        if os.path.exists(setting_file_path):
            with open(setting_file_path, "r") as f:
                setting = f.read()

        if os.path.exists(plot_file_path):
            with open(plot_file_path, "r") as f:
                plot = f.read()

    except Exception as e:
        print(f"An unexpected error occurred in show_story: {e}")

    # Add character row visibility updates
    character_row_visibility = update_character_visibility(num_characters)

    return [num_characters] + character_row_visibility + character_image_paths + names + sexs + voices + descriptions + [setting, plot]

def show_images_and_prompts(number_of_scenes):
    MAX_SCENES = 12
    path = "tmp/default/videos"
    
    # Get images
    scene_image_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_") and file.endswith(".png"):
                scene_image_files.append(os.path.join(path, file))
    # Pad with None if fewer images than scenes are found
    padded_images = (scene_image_files + [None] * MAX_SCENES)[:MAX_SCENES]
    
    # Get prompts
    scene_prompt_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_prompt_") and file.endswith(".txt"):
                scene_prompt_files.append(os.path.join(path, file))
    
    generated_scene_prompts = []
    for f in scene_prompt_files:
        with open(f, "r") as file:
            generated_scene_prompts.append(file.read())
    # Pad with empty strings if fewer prompts than scenes are found
    padded_prompts = (generated_scene_prompts + [""] * MAX_SCENES)[:MAX_SCENES]

    # Return a single, flat list: all image paths, then all prompts
    # The order and length must match the `outputs` in the click event
    return padded_images + padded_prompts
