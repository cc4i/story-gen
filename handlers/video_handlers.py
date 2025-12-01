
import os
import json
import random
from typing import List, Dict
from utils.gen_video import upload_image, image_to_video, image_to_video_v31, download_videos
from models.config import VEO_STORAGE_BUCKET
from utils.video_ts import merge_videos_moviepy
from handlers.ui_handlers import clear_temp_files
from utils.config import STORY_JSON, VIDEOS_DIR, MERGED_VIDEO_MP4
from utils.llm import call_llm
from utils.logger import logger
from utils.save_files import save_script
from agents.video_quality_agent import VideoQualityAgent



def generate_video_v31(*args):
    """
    Generate videos from v31 storyboard.

    Args:
        *args: First 12 are scene images, next 12 are scene texts, next 12 are script texts
               then model_id, then is_generate_audio
    """
    clear_temp_files(VIDEOS_DIR, "_0.mp4")
    MAX_SCENES = 12

    # Split args into components
    scene_images_v31 = list(args[:MAX_SCENES])
    scene_texts_v31 = list(args[MAX_SCENES:MAX_SCENES*2])
    script_texts_v31 = list(args[MAX_SCENES*2:MAX_SCENES*3])
    chosen_veo_model_id = args[MAX_SCENES*3]
    is_generate_audio = args[MAX_SCENES*3 + 1]

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




def generate_video(chosen_veo_model_id, is_generate_audio, *args):
    script_texts = list(args)
    for i in range(12):
        save_script(i+1, script_texts[i], False)

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


def generate_video_v31_with_validation(*args):
    """
    Generate videos from v31 storyboard with quality validation and auto-retry.

    Args:
        *args: First 12 are scene images, next 12 are scene texts, next 12 are script_texts
               then model_id, then is_generate_audio, then enable_validation,
               then quality_threshold

    Returns:
        Tuple of (all_video_files, quality_report_data)
    """
    MAX_SCENES = 12

    # Split args into components
    scene_images_v31 = list(args[:MAX_SCENES])
    scene_texts_v31 = list(args[MAX_SCENES:MAX_SCENES*2])
    script_texts_v31 = list(args[MAX_SCENES*2:MAX_SCENES*3])
    chosen_veo_model_id = args[MAX_SCENES*3]
    is_generate_audio = args[MAX_SCENES*3 + 1]
    enable_validation = args[MAX_SCENES*3 + 2] if len(args) > MAX_SCENES*2 + 2 else True
    quality_threshold = args[MAX_SCENES*3 + 3] if len(args) > MAX_SCENES*2 + 3 else 8.0

    logger.info(f"Video generation v3.1 with validation: model={chosen_veo_model_id}, "
                f"audio={is_generate_audio}, validation={enable_validation}, "
                f"threshold={quality_threshold}")

    # If validation disabled, use original function
    if not enable_validation:
        logger.info("Quality validation disabled - using standard generation")
        all_files = generate_video_v31(*args[:MAX_SCENES*3 + 2])
        return all_files, None

    # Save scripts
    for i in range(12):
        save_script(i+1, script_texts_v31[i], True)

    # Load character references and scene data
    character_refs = load_character_references()
    scene_descriptions = load_scene_descriptions()

    # Initialize quality agent
    vqa = VideoQualityAgent(
        quality_threshold=quality_threshold,
        max_retries=2
    )

    # Phase 1: Generate initial videos
    logger.info(f"[Phase 1] Generating initial videos for all scenes...")
    clear_temp_files(VIDEOS_DIR, "_0.mp4")
    all_files = []
    video_metadata = []  # Track metadata for validation

    for i, (images, prompt_txt) in enumerate(zip(scene_images_v31, scene_texts_v31)):
        image_paths = []
        if images is not None and images:
            if isinstance(images, list):
                for j, image in enumerate(images):
                    image_path = image[0] if isinstance(image, tuple) else image
                    image_paths.append(image_path)

            if prompt_txt:
                output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"
                logger.info(f"Scene {i+1}/{MAX_SCENES}: Generating video")

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

                # Store metadata for validation
                if files:
                    video_metadata.append({
                        "path": files[0],
                        "scene_number": i + 1,
                        "prompt": prompt_txt,
                        "references": image_paths,
                        "scene_description": scene_descriptions[i] if i < len(scene_descriptions) else {},
                        "duration": 8.0
                    })

    # Sort by sequence number
    def get_sequence_number(path):
        filename = os.path.basename(path)
        try:
            return int(filename.split('-')[0])
        except (ValueError, IndexError):
            return 0

    all_files.sort(key=get_sequence_number)

    logger.info(f"[Phase 1] Generated {len(all_files)} videos")

    # Phase 2: Validate all videos
    logger.info(f"[Phase 2] Validating {len(video_metadata)} videos...")
    validation_reports = vqa.validate_videos_parallel(
        videos=video_metadata,
        character_references=character_refs,
        scene_descriptions=scene_descriptions
    )

    # Phase 3: Retry failed scenes
    retry_scenes = vqa.get_retry_scenes()

    if retry_scenes:
        logger.info(f"[Phase 3] Retrying {len(retry_scenes)} scenes with improved prompts...")

        for retry_data in retry_scenes:
            scene_num = retry_data["scene_number"]
            improved_prompt = retry_data["improved_prompt"]
            retry_count = retry_data["retry_count"]

            logger.info(f"Scene {scene_num}: Retry attempt {retry_count} with improved prompt")

            # Find original scene data
            original_scene = next((s for s in video_metadata if s["scene_number"] == scene_num), None)
            if not original_scene:
                logger.warning(f"Scene {scene_num}: Could not find original data for retry")
                continue

            # Regenerate with improved prompt
            output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"

            try:
                op, rr = image_to_video_v31(
                    model_id=chosen_veo_model_id,
                    prompt=improved_prompt,  # Use improved prompt
                    reference_image_paths=original_scene["references"],
                    seed=random.randint(0, 1000000),
                    aspect_ratio="16:9",
                    sample_count=1,
                    output_gcs=output_gcs,
                    negative_prompt="",
                    durations=8,
                    generate_audio=is_generate_audio,
                    resolution="1080p"
                )
                new_files = download_videos(op, "default", f"{scene_num}", False)

                if new_files:
                    # Replace old file in list and delete failed video
                    old_file_idx = scene_num - 1
                    if old_file_idx < len(all_files):
                        old_video_path = all_files[old_file_idx]
                        logger.info(f"Scene {scene_num}: Replacing {old_video_path} with {new_files[0]}")

                        # Delete the failed video file
                        try:
                            if os.path.exists(old_video_path):
                                os.remove(old_video_path)
                                logger.info(f"Scene {scene_num}: Deleted failed video: {old_video_path}")
                        except Exception as delete_error:
                            logger.warning(f"Scene {scene_num}: Failed to delete old video: {delete_error}")

                        all_files[old_file_idx] = new_files[0]

                    # Re-validate the new video
                    logger.info(f"Scene {scene_num}: Re-validating improved video...")
                    retry_report = vqa.validate_video(
                        video_path=new_files[0],
                        scene_number=scene_num,
                        character_references=character_refs,
                        scene_description=original_scene["scene_description"],
                        original_prompt=improved_prompt,
                        expected_duration=8.0,
                        retry_count=retry_count
                    )

                    logger.info(f"Scene {scene_num}: Retry result - Decision={retry_report.decision.decision}, "
                                f"Score={retry_report.decision.overall_score:.1f}/10")

            except Exception as e:
                logger.error(f"Scene {scene_num}: Retry failed: {str(e)}")
                continue

    # Phase 4: Generate quality report
    logger.info(f"[Phase 4] Generating quality report...")
    quality_report = vqa.generate_quality_report()

    logger.info(f"Quality Validation Complete: {quality_report['summary']}")

    # Convert quality report to DataFrame format for Gradio
    report_data = [
        [
            r["scene"],
            r["anatomy"],
            r["consistency"],
            r["technical"],
            r["overall_score"],
            r["decision"],
            0  # Retry count - would need to track this
        ]
        for r in quality_report["detailed_reports"]
    ]

    all_files.sort(key=get_sequence_number)
    return all_files, report_data


def load_character_references() -> List[Dict]:
    """
    Load character reference images and descriptions from story data.

    Returns:
        List of dicts with character info
    """
    try:
        characters_json_path = os.path.join(VIDEOS_DIR, "../characters.json")
        if os.path.exists(characters_json_path):
            with open(characters_json_path, "r") as f:
                characters = json.load(f)

            # Add image paths
            for char in characters:
                char_name = char.get("name", "").lower().replace(" ", "_")
                img_path = os.path.join(VIDEOS_DIR, "../characters", f"{char_name}.png")
                char["image_path"] = img_path if os.path.exists(img_path) else None

            return characters

        logger.warning("No characters.json found - validation may be limited")
        return []

    except Exception as e:
        logger.error(f"Error loading character references: {str(e)}")
        return []


def load_scene_descriptions() -> List[Dict]:
    """
    Load scene descriptions from story.json.

    Returns:
        List of scene dicts
    """
    try:
        if os.path.exists(STORY_JSON):
            with open(STORY_JSON, "r") as f:
                story_data = json.load(f)
                scenes = story_data.get("story_scenes", [])
                logger.info(f"Loaded {len(scenes)} scene descriptions from story.json")
                return scenes

        logger.warning("No story.json found - using empty scene descriptions")
        return []

    except Exception as e:
        logger.error(f"Error loading scene descriptions: {str(e)}")
        return []
