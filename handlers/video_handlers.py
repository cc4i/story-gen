
import os
import json
import random
from utils.gen_video import upload_image, image_to_video, image_to_video_v31, download_videos
from models.config import VEO_STORAGE_BUCKET
from utils.video_ts import merge_videos_moviepy
from handlers.ui_handlers import clear_temp_files
from utils.config import STORY_JSON, VIDEOS_DIR, MERGED_VIDEO_MP4
from utils.llm import call_llm
from utils.logger import logger



def generate_video_v31(*args):
    """
    Generate videos from v31 storyboard.

    Args:
        *args: First 12 are scene images, next 12 are scene texts,
               then model_id, then is_generate_audio
    """
    clear_temp_files(VIDEOS_DIR, "_0.mp4")
    MAX_SCENES = 12

    # Split args into components
    scene_images_v31 = list(args[:MAX_SCENES])
    scene_texts_v31 = list(args[MAX_SCENES:MAX_SCENES*2])
    chosen_veo_model_id = args[MAX_SCENES*2]
    is_generate_audio = args[MAX_SCENES*2 + 1]

    # clear_temp_files(VIDEOS_DIR, "_v31_0.mp4")
    all_files = []

    logger.info(f"Video generation v3.1: model={chosen_veo_model_id}, audio={is_generate_audio}, scenes={MAX_SCENES}")

    for i, (images, prompt_txt) in enumerate(zip(scene_images_v31, scene_texts_v31)):
        image_paths = []
        if images is not None and images:
            logger.info(f"Scene {i+1}/{MAX_SCENES}: Processing {len(images) if isinstance(images, list) else 'unknown'} reference images")

            if isinstance(images, list):
                for j, image in enumerate(images):
                    # Gradio Gallery returns tuples: (path, caption)
                    image_path = image[0] if isinstance(image, tuple) else image
                    logger.debug(f"Scene {i+1}: Reference image {j+1}: {image_path}")
                    image_paths.append(image_path)
            else:
                logger.debug(f"Scene {i+1}: Images data: {images}")

            if prompt_txt:
                logger.info(f"Scene {i+1}/{MAX_SCENES}: Prompt={prompt_txt[:100]}...")

            output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"
            logger.info(f"Scene {i+1}/{MAX_SCENES}: Starting video generation")
            op, rr = image_to_video_v31(
                model_id=chosen_veo_model_id, 
                prompt=prompt_txt, 
                reference_image_paths=image_paths, 
                seed=random.randint(0, 1000000),
                aspect_ratio="16:9",
                sample_count=1,
                output_gcs=output_gcs,
                negative_prompt="",
                durations=8,
                generate_audio=is_generate_audio,
                resolution="1080p"
            )
            files = download_videos(op, "default", f"{i+1}", False)
            all_files.extend(files)
            
    # Sort by sequence number (numeric sort, not alphabetical)
    def get_sequence_number(path):
        filename = os.path.basename(path)
        try:
            return int(filename.split('-')[0])
        except (ValueError, IndexError):
            return 0

    all_files.sort(key=get_sequence_number)
    return all_files




def generate_video(chosen_veo_model_id, is_generate_audio):
    clear_temp_files(VIDEOS_DIR, "_0.mp4")

    all_files = []
    for file in os.listdir(VIDEOS_DIR):
        if file.startswith("scene_") and file.endswith(".png"):
            image_path = os.path.join(VIDEOS_DIR, file)
            sequence = file.split('.')[0].split('_')[1]
            video_prompt_path = os.path.join(VIDEOS_DIR, f"scene_prompt_{sequence}.txt")
            video_prompt = open(video_prompt_path, "r").read()
            video_prompt = f"""
                Generate a video based on the following description:
                ***{video_prompt}***
            """
            logger.info(f"Generating video for scene {sequence}: image={image_path}")
            logger.debug(f"Scene {sequence} prompt: {video_prompt[:200]}...")

            # generate video
            image_gcs_path = upload_image(image_path, "default")
            output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"
            op, rr = image_to_video(
                model_id=chosen_veo_model_id,
                prompt=video_prompt,
                image_gcs=image_gcs_path,
                image_gcs_last=None,
                seed=random.randint(0, 1000000),
                aspect_ratio="16:9",
                sample_count=1,
                output_gcs=output_gcs,
                negative_prompt="",
                enhance="true",
                durations=8,
                generate_audio=is_generate_audio,
                resolution="1080p"
            )
            files = download_videos(op, "default", sequence, False)
            all_files.extend(files)

    # Sort by sequence number (numeric sort, not alphabetical)
    def get_sequence_number(path):
        filename = os.path.basename(path)
        try:
            return int(filename.split('-')[0])
        except (ValueError, IndexError):
            return 0

    all_files.sort(key=get_sequence_number)
    return all_files

def show_generated_videos():
    generated_videos = []
    logger.info(f"Loading generated videos from: {VIDEOS_DIR}")
    for file in os.listdir(VIDEOS_DIR):
        if file.endswith("_0.mp4"):
            logger.debug(f"Found video file: {file}")
            generated_videos.append(os.path.join(VIDEOS_DIR, file))

    # Sort by sequence number (numeric sort, not alphabetical)
    def get_sequence_number(path):
        filename = os.path.basename(path)
        try:
            return int(filename.split('-')[0])
        except (ValueError, IndexError):
            return 0

    generated_videos.sort(key=get_sequence_number)
    return generated_videos

def show_merged_videos():
    return MERGED_VIDEO_MP4
