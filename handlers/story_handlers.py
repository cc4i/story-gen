import gradio as gr
import json
import os
import uuid
import time
from utils.llm import call_llm
from utils.logger import logger
from utils.prompt_templates import generate_story_prompt, update_story_prompt, develop_story_prompt
from utils.gen_image import gen_images, gen_images_by_banana
from utils.acceptance import to_snake_case_v2
from PIL import Image
from io import BytesIO
from handlers.ui_handlers import check_folder, clear_temp_files
from utils.config import (
    CHARACTERS_DIR,
    VIDEOS_DIR,
    STORY_JSON
)
from utils.save_files import save_characters, save_setting, save_plot, save_story
from models.config import DEFAULT_MODEL_ID
from agents import IdeaGenerationAgent, IdeaGenerationAgentADK
from agents.scene_development_agent_adk import SceneDevelopmentAgentADK

def generate_story(idea, style="Studio Ghibli", use_agent=True, use_adk=True):
    """
    Generate story structure from user idea.

    Args:
        idea: User's story idea
        style: Visual style for the story (default: "Studio Ghibli")
        use_agent: If True, use self-critique agent for improved results.
                   If False, use original single-shot LLM approach.
        use_adk: If True, use Google ADK-based agent (IdeaGenerationAgentADK).
                 If False, use original agent (IdeaGenerationAgent).
                 Only applies when use_agent=True.

    Returns:
        Tuple of (characters, setting, plot)
    """
    operation_id = str(uuid.uuid4())[:8]
    logger.info(f"[{operation_id}] Generating story, use_agent={use_agent}, use_adk={use_adk}, style={style}")

    if use_agent:
        # Use agent with self-critique and refinement
        if use_adk:
            logger.info(f"[{operation_id}] Using IdeaGenerationAgentADK (Google ADK-based) for enhanced story generation")
            agent = IdeaGenerationAgentADK(model_id=DEFAULT_MODEL_ID)
        else:
            logger.info(f"[{operation_id}] Using IdeaGenerationAgent (original) for enhanced story generation")
            agent = IdeaGenerationAgent(model_id=DEFAULT_MODEL_ID)

        characters, setting, plot = agent.generate_story(idea, style)

        # Log agent insights
        critique_summary = agent.get_critique_summary()
        logger.info(f"[{operation_id}] Agent iteration summary:\n{critique_summary}")
    else:
        # Original single-shot approach
        logger.info(f"[{operation_id}] Using traditional single-shot generation")
        system_instruction, prompt = generate_story_prompt(idea)
        history = ""
        string_response = call_llm(system_instruction, prompt, history, DEFAULT_MODEL_ID)
        json_response = json.loads(string_response)
        characters = json_response["characters"]
        setting = json_response["setting"]
        plot = json_response["plot"]

    save_characters(characters)
    save_setting(setting)
    save_plot(plot)

    logger.info(f"[{operation_id}] Story generation completed successfully")
    return characters, setting, plot

def update_story(idea, characters):
    system_instruction, prompt = update_story_prompt(idea, characters)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, DEFAULT_MODEL_ID)
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
    operation_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    check_folder("tmp/default/characters")
    clear_temp_files("tmp/default/characters", ".*")

    # Parse arguments
    number_of_characters = int(args[0])
    character_names = args[1:7]
    character_sexs = args[7:13]
    character_voices = args[13:19]
    character_descriptions = args[19:25]
    style = args[25]

    logger.info(f"[{operation_id}] Starting character image generation: count={number_of_characters}, style={style}")

    generated_images = []
    for i in range(number_of_characters):
        # Create character image prompt
        char_prompt = f"""
            # Full-body shot of the character: ***{character_names[i]}***
            # Sex: ***{character_sexs[i]}***
            # A ***{style}*** image of ***{character_descriptions[i]}***
            # Background: ***The background must be a solid, clean, plain white background, isolating the character.***
        """

        logger.info(f"[{operation_id}] Character {i+1}/{number_of_characters}: Generating image for '{character_names[i]}'")
        logger.debug(f"[{operation_id}] Character prompt: {char_prompt[:100]}...")

        try:
            images_data = gen_images_by_banana(char_prompt)
            image = Image.open(BytesIO(images_data[0]))
            image_path = f"tmp/default/characters/{to_snake_case_v2(character_names[i])}.png"
            image.save(image_path)
            generated_images.append(image_path)
            logger.info(f"[{operation_id}] Character {i+1}: Saved to {to_snake_case_v2(character_names[i])}.png")
        except Exception as e:
            logger.error(
                f"[{operation_id}] Character {i+1} ({character_names[i]}): Image generation failed: {str(e)}",
                exc_info=True,
                extra={
                    "operation_id": operation_id,
                    "character_name": character_names[i],
                    "character_index": i
                }
            )
            generated_images.append(None)

    # Pad with None to match max characters (6)
    while len(generated_images) < 6:
        generated_images.append(None)

    duration = time.time() - start_time
    logger.info(f"[{operation_id}] Character image generation completed: total={number_of_characters}, duration={duration:.2f}s")

    return generated_images


def prepare_veo_prompt(story_json:list[dict], characters:list[dict], model_id:str):
    veo_prompts=[]
    system_instruction = """
            You are a prompting expert, your task is to create the best prompt for Veo to generate a high-quality video for a scene.
    """
    for scene in story_json:
        p_prompt = f"""
            Based on the scene description provided below, create a detailed prompt for generating a high-quality video. Include the following elements in your prompt:

            - Subject: The object, person, animal, or scenery that you want in your video.
            - Context: The background or context in which the subject is placed.
            - Action: What the subject is doing (for example, walking, running, or turning their head).
            - Style: This can be general or very specific. Consider using specific film style keywords, such as horror film, film noir, or animated styles like cartoon style render.
            - Camera motion: Optional: What the camera is doing, such as aerial view, eye-level, top-down shot, or low-angle shot.
            - Composition: Optional: How the shot is framed, such as wide shot, close-up, or extreme close-up.
            - Ambiance: Optional: How the color and light contribute to the scene, such as blue tones, night, or warm tones.
            - Dialog if any

            Notice:
            - To differentiate between multiple characters in the images, use the most distinguish descriptive details variable.
            - Output as plain text as prompt without any explaination.

            Here is the scene description:
            {scene}

            Here is the charaters description:
            {characters}
        """
        pp = call_llm(system_instruction, p_prompt, "", model_id)
        logger.info(f"Generated Veo prompt for scene {scene['scene_number']}: {pp[:100]}...")
        logger.debug(f"Full Veo prompt for scene {scene['scene_number']}: {pp}")
        veo_prompts.append(pp)

    return veo_prompts


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
        args[35]: model_id (str)
        args[36]: style (str)
        args[37]: use_scene_adk (bool, optional) - If True, use SceneDevelopmentAgentADK

    Returns:
        list: [story_response] + flattened script_rows updates (144 values: 12 scenes * 3 lines * 4 fields)
    """
    operation_id = str(uuid.uuid4())[:8]
    start_time = time.time()

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
    model_id = args[35]
    style = args[36]
    use_scene_adk = args[37] if len(args) > 37 else True  # Default to True
    character_image_dict={}

    logger.info(f"[{operation_id}] Starting story development: characters={number_of_characters}, scenes={number_of_scenes}, duration={duration_per_scene}s, style={style}, model={model_id}, use_scene_adk={use_scene_adk}")

    # Build characters string for the prompt
    characters = []
    for i in range(number_of_characters):
        if character_names[i] and character_descriptions[i]:
            characters.append({
                "name": character_names[i],
                "sex": character_sexs[i],
                "voice": character_voices[i],
                "description": character_descriptions[i],
                "style": style,
            })
        if character_names[i] and character_descriptions[i]:
            character_image_dict[character_names[i]]=character_images[i]

    # Clear old video files
    check_folder(f"{VIDEOS_DIR}")
    clear_temp_files(f"{VIDEOS_DIR}", ".*")

    # Save the story data
    save_characters(characters)
    save_setting(setting)
    save_plot(plot)

    # Generate the story development
    if use_scene_adk:
        # Use ADK-based Scene Development Agent (5-agent, two-phase system)
        logger.info(f"[{operation_id}] Using SceneDevelopmentAgentADK (Google ADK-based) for enhanced scene development")
        scene_agent = SceneDevelopmentAgentADK(model_id=model_id)

        scenes = scene_agent.develop_scenes(
            characters=characters,
            setting=setting,
            plot=plot,
            number_of_scenes=number_of_scenes,
            duration_per_scene=duration_per_scene,
            style=style
        )

        # Convert ADK output to expected format
        story_json = {
            "story_scenes": scenes
        }

        # Log agent insights
        critique_summary = scene_agent.get_critique_summary()
        logger.info(f"[{operation_id}] Scene development agent summary:\n{critique_summary}")
        logger.info(f"[{operation_id}] Best score: {scene_agent.state.best_score:.1f}/10")
    else:
        # Original single-shot approach
        logger.info(f"[{operation_id}] Using traditional single-shot scene development")
        system_instruction, prompt = develop_story_prompt(characters, setting, plot, number_of_scenes, duration_per_scene, style)
        history = ""
        logger.debug(f"[{operation_id}] Story prompt: {prompt[:200]}...")
        string_response = call_llm(system_instruction, prompt, history, model_id)
        story_json = json.loads(string_response)

    # Save full story to file
    save_story(story_json)
    logger.info(f"[{operation_id}] Story developed successfully, saved to {STORY_JSON}")

    # Generate images and save prompts/scripts for each scene in "Visual Storyboard" Tab
    logger.info(f"[{operation_id}] Generating images for {len(story_json['story_scenes'])} scenes")
    for i, scene in enumerate(story_json["story_scenes"],1):
        reference_images = []

        # Collect valid reference images for characters in this scene
        for n in scene["characters"]:
            # Handle both string names and dict objects with 'name' field
            character_name = n["name"] if isinstance(n, dict) else n
            img_path = f"tmp/default/characters/{to_snake_case_v2(character_name)}.png"
            if os.path.exists(img_path):
                reference_images.append(img_path)
                logger.debug(f"[{operation_id}] Scene {i}: Added reference image for character '{character_name}'")
            else:
                logger.warning(f"[{operation_id}] Scene {i}: Reference image not found for character '{character_name}': {img_path}")

        # Limit to max 3 reference images (API best practice)
        if len(reference_images) > 3:
            logger.warning(f"[{operation_id}] Scene {i}: Found {len(reference_images)} reference images, using only first 3")
            reference_images = reference_images[:3]

        # Extract character names (handle both string and dict formats)
        character_names_in_scene = [
            c["name"] if isinstance(c, dict) else c
            for c in scene["characters"]
        ]

        # Try with reference images first, fallback to no references if it fails
        try:
            key_image_prompt = f"""
                Generate a key image for the scene based on following description:
                - location: ***{scene["location"]}***
                - atmosphere: ***{scene["atmosphere"]}***
                - characters: ***{character_names_in_scene}***

                Notice:
                - All characters must be front face and aligned with referenced character image.
            """
            if reference_images:
                logger.info(f"[{operation_id}] Scene {i}/{number_of_scenes}: Generating with {len(reference_images)} reference image(s)")
                generated_image_data = gen_images_by_banana(prompt=key_image_prompt, reference_images=reference_images)[0]
            else:
                logger.info(f"[{operation_id}] Scene {i}/{number_of_scenes}: Generating without reference images")
                generated_image_data = gen_images_by_banana(prompt=key_image_prompt)[0]
        except Exception as e:
            logger.error(f"[{operation_id}] Scene {i}: Image generation failed with reference images: {str(e)}", exc_info=True)
            logger.info(f"[{operation_id}] Scene {i}: Retrying without reference images")
            generated_image_data = gen_images_by_banana(prompt=key_image_prompt)[0]

        image = Image.open(BytesIO(generated_image_data))
        image.save(f"{VIDEOS_DIR}/scene_{i}.png")
        logger.info(f"[{operation_id}] Scene {i}: Saved image to scene_{i}.png")

        video_prompt_file = f"{VIDEOS_DIR}/scene_prompt_{i}.txt"
        with open(video_prompt_file, "w") as f:
            f.write(json.dumps(scene, indent=4))

        video_script_file = f"{VIDEOS_DIR}/scene_script_{i}.json"
        with open(video_script_file, "w") as f:
            f.write(json.dumps(scene["dialogue"], indent=4))
        
        video_script_file_v31 = f"{VIDEOS_DIR}/v31_scene_script_{i}.json"
        with open(video_script_file_v31, "w") as f:
            f.write(json.dumps(scene["dialogue"], indent=4))
    ###

    # Generate images and save prompts for each scene in "Visual Storyboard v31" Tab
    logger.info(f"[{operation_id}] Generating v31 scene images (without characters)")
    for i, scene in enumerate(story_json["story_scenes"],1):
        try:
            scene_image_prompt = f"""
                Generate a scene image without characters for the scene based on following description:
                - location: ***{scene["location"]}***
                - atmosphere: ***{scene["atmosphere"]}***
                - style: ***{style}***
            """
            logger.info(f"[{operation_id}] Scene v31 {i}/{number_of_scenes}: Generating scene image")
            generated_image_data = gen_images_by_banana(prompt=scene_image_prompt)[0]
        except Exception as e:
            logger.error(f"[{operation_id}] Scene v31 {i}: Image generation failed: {str(e)}", exc_info=True)
            logger.info(f"[{operation_id}] Scene v31 {i}: Retrying scene image generation")
            generated_image_data = gen_images_by_banana(prompt=scene_image_prompt)[0]

        image = Image.open(BytesIO(generated_image_data))
        image.save(f"{VIDEOS_DIR}/scene_v31_{i}.png")
        logger.info(f"[{operation_id}] Scene v31 {i}: Saved to scene_v31_{i}.png")

    logger.info(f"[{operation_id}] Generating Veo prompts for {len(story_json['story_scenes'])} scenes")
    veo_prompts = prepare_veo_prompt(story_json["story_scenes"], characters, model_id)
    for i, vp in enumerate(veo_prompts,1):
        video_prompt_v31_file = f"{VIDEOS_DIR}/scene_prompt_v31_{i}.txt"
        with open(video_prompt_v31_file, "w") as f:
            f.write(vp)
    ###

    duration = time.time() - start_time
    logger.info(f"[{operation_id}] Story development completed: scenes={number_of_scenes}, total_images={number_of_scenes * 2}, duration={duration:.2f}s")

    return json.dumps(story_json, indent=4)
