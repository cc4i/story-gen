
import json
import os
from utils.llm import call_llm
from utils.logger import logger
from utils.prompt_templates import generate_story_prompt, update_story_prompt, develop_story_prompt
from utils.gen_image import gen_images
from utils.save_files import save_characters, save_setting, save_plot
from PIL import Image
from io import BytesIO
from handlers.ui_handlers import check_folder, clear_temp_files

def generate_story(idea):
    system_instruction, prompt = generate_story_prompt(idea)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    json_response = json.loads(string_response)
    characters = ""
    for c in json_response["characters"]:
        characters += f"{c['name']}: {c['description']}\n"
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

def generate_character_images(number_of_characters, characters, style):
    """Generate images for each character based on their descriptions"""
    check_folder("tmp/images/characters")

    save_characters(characters)
    characters = characters.split("\n")

    generated_images = []
    for i in range(int(number_of_characters)):
        char = characters[i]

        if len(char) <= 2:
            generated_images.append(None)
            continue

        # Create character image prompt
        char_prompt = f"{char}. Style: {style}. Full body portrait, character design sheet."

        try:
            generated_image_response = gen_images(
                model_id="imagen-4.0-generate-preview-06-06",
                prompt=char_prompt,
                negative_prompt="blurry, low quality, distorted",
                number_of_images=1,
                aspect_ratio="1:1",
                is_enhance="yes"
            )[0]

            image = Image.open(BytesIO(generated_image_response.image.image_bytes))
            image_path = f"tmp/images/characters/character_{i+1}.png"
            image.save(image_path)
            generated_images.append(image_path)
        except Exception as e:
            logger.error(f"Error generating image for character {name}: {e}")
            generated_images.append(None)

    # Pad with None to match max characters (6)
    while len(generated_images) < 6:
        generated_images.append(None)

    return generated_images

def develope_story(characters, setting, plot, number_of_scenes, duration_per_scene, style):
    clear_temp_files("tmp/images/default", ".*")

    save_characters(characters)
    save_setting(setting)
    save_plot(plot)

    system_instruction, prompt = develop_story_prompt(characters, setting, plot, number_of_scenes, duration_per_scene, style)
    history = ""
    logger.info(f"Developing story with prompt: {prompt}")
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    # Save full string respose to file
    with open("tmp/images/default/story.json", "w") as f:
        f.write(string_response)
    json_response = json.loads(string_response)

    for i, scene in enumerate(json_response, 1):
        image_prompt = {
            "title": scene["title"],
            "description": scene["description"],
            "characters": scene["characters"],
            "image_prompt": scene["image_prompt"]
        }

        generated_image_response = gen_images(
            model_id="imagen-4.0-generate-preview-06-06",
            prompt=json.dumps(image_prompt),
            negative_prompt="",
            number_of_images=1,
            aspect_ratio="16:9",
            is_enhance="yes"
        )[0]

        image = Image.open(BytesIO(generated_image_response.image.image_bytes))
        image.save(f"tmp/images/default/scene_{i}.png")
        video_prompt_file = f"tmp/images/default/scene_prompt_{i}.txt"
        with open(video_prompt_file, "w") as f:
            f.write(scene["description"]) # f.write(scene["video_prompt"])
        video_script_file = f"tmp/images/default/scene_script_{i}.json"
        with open(video_script_file, "w") as f:
            f.write(json.dumps(scene["scripts"], indent=4))
    return string_response
