
import gradio as gr
import os

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

def show_images_and_prompts(number_of_scenes):
    MAX_SCENES = 12
    path = "tmp/images/default"
    
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

    scene_script_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_script_") and file.endswith(".txt"):
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
