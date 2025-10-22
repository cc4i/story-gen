
import os
import random
from utils.gen_video import upload_image, image_to_video, download_videos
from models.config import VEO_STORAGE_BUCKET
from utils.video_ts import merge_videos_moviepy
from handlers.ui_handlers import clear_temp_files
from utils.config import VIDEOS_DIR, MERGED_VIDEO_MP4

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
            print(f"image_path: {image_path}")
            print(f"video_prompt: {video_prompt}")

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
    all_files.sort()
    return all_files

def show_generated_videos():
    generated_videos = []
    print(f"VIDEOS_DIR: {VIDEOS_DIR}")
    for file in os.listdir(VIDEOS_DIR):
        if file.endswith("_0.mp4"):
            print(f"image_path: {file}")
            generated_videos.append(os.path.join(VIDEOS_DIR, file))
    generated_videos.sort()
    return generated_videos

def show_merged_videos():
    return MERGED_VIDEO_MP4
