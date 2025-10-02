
import os
import random
from utils.gen_video import upload_image, image_to_video, download_videos
from models.config import VEO_STORAGE_BUCKET
from utils.video_ts import merge_videos_moviepy
from handlers.ui_handlers import clear_temp_files

def generate_video(chosen_veo_model_id, is_generate_audio):
    clear_temp_files("tmp/default", ".mp4")

    all_files = []
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_") and file.endswith(".png"):
            image_path = f"tmp/images/default/{file}"
            seqence = file.split('.')[0].split('_')[1]
            video_prompt_path = f"tmp/images/default/scene_prompt_{seqence}.txt"
            video_prompt = open(video_prompt_path, "r").read()
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
            files = download_videos(op, "default", seqence, False)
            all_files.extend(files)
    all_files.sort()
    return all_files

def show_generated_videos():
    generated_videos = []
    for file in os.listdir("tmp/default"):
        if file.endswith("_0.mp4"):
            generated_videos.append(f"tmp/default/{file}")
    generated_videos.sort()
    return generated_videos

def show_merged_videos():
    merged_video = "tmp/default/merged_video.mp4"
    return merged_video
