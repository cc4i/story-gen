

import os
import re
import time
import uuid
import gradio as gr
from utils.ce_audio import generate_audio_by_gemini, choose_random_voice
from utils.logger import logger
import json
from handlers.ui_handlers import clear_temp_files
from utils.video_ts import merge_audio_at_time
from utils.config import DEFAULT_SESSION_DIR, VIDEOS_DIR

def generate_audio():
    operation_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"[{operation_id}] Starting audio generation from scene scripts")
    clear_temp_files(DEFAULT_SESSION_DIR, ".wav")

    all_audio_files = {}
    audio_files = []
    random_voice={}
    total_dialogues = 0

    for file in os.listdir(VIDEOS_DIR):
        if file.startswith("scene_script_") and file.endswith(".json"):
            logger.info(f"[{operation_id}] Processing script file: {file}")
            order = file.split(".")[0].split("_")[2]
            string_script = open(os.path.join(VIDEOS_DIR, file), "r").read()
            json_script = json.loads(string_script)

            for script in json_script:
                character_name=script["character"]
                gender=script["gender"]
                message=script["dialogue"]
                dialogue_start_time=script["time"]
                # message = f"Say in Singaporean TONE: {message}"
                # Ignore feeling in the message, eg: (Gasps softly)
                message = re.sub(r"\(.*?\)", '', message)
                if len(message) > 0:
                    message = f"Say: {message}"
                    if random_voice.get(character_name) is None:
                        random_voice[character_name] = choose_random_voice(gender)
                    voice_name = random_voice[character_name]
                    total_dialogues += 1
                    logger.info(f"[{operation_id}] Generating audio {total_dialogues}: character={character_name}, voice={voice_name}, gender={gender}, start_time={dialogue_start_time}s")
                    logger.debug(f"[{operation_id}] Dialogue text: {message[:100]}...")
                    audio_files.append(generate_audio_by_gemini(message, gender, order, character_name, dialogue_start_time, voice_name))
                    # Add a small delay between audio generation due to rate limit
                    time.sleep(5)

    logger.info(f"[{operation_id}] Generated {len(audio_files)} audio files, organizing by scene order")

    for f in audio_files:
        order = f.split("/")[-1].split("-")[0]
        if all_audio_files.get(order) is None:
            all_audio_files[order]= [f]
        else:
            all_audio_files[order].append("None")
            all_audio_files[order].append(f)
    for i in range (1, 13):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= ["None"]

    duration = time.time() - start_time
    logger.info(f"[{operation_id}] Audio generation completed: total_files={len(audio_files)}, scenes={len(all_audio_files)}, duration={duration:.2f}s")
    logger.debug(f"[{operation_id}] Audio files by scene: {list(all_audio_files.keys())}")
    
    # Create a list of Dropdown updates
    dropdown_updates = []
    for i in range(1, 13):
        dropdown_updates.append(gr.Dropdown(choices=all_audio_files[str(i)]))
    return dropdown_updates

def show_generated_audios():
    all_audio_files = {}
    path = DEFAULT_SESSION_DIR
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".wav"):
                order = file.split("-")[0]
                if all_audio_files.get(order) is None:
                    all_audio_files[order]= [os.path.join(path, file)]
                else:
                    all_audio_files[order].append(os.path.join(path, file))
    
    # Ensure all possible keys exist
    for i in range (1, 13):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= []

    # Return a list of Dropdown update objects
    dropdown_updates = []
    for i in range(1, 13):
        choices = all_audio_files[str(i)]
        choices.append("None")
        # Set the initial value to the first choice if available, otherwise None
        value = choices[0] if choices else None
        dropdown_updates.append(gr.Dropdown(choices=choices, value=value))
    return dropdown_updates

def merge_audios():
    operation_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"[{operation_id}] Starting audio-video merge process")

    audio_files = []
    video_files = {}
    merged_list = {}

    # Collect audio files
    for file in os.listdir(DEFAULT_SESSION_DIR):
        if file.endswith(".wav"):
            audio_files.append(os.path.join(DEFAULT_SESSION_DIR, file))
    audio_files.sort()
    logger.info(f"[{operation_id}] Found {len(audio_files)} audio files to merge")
    logger.debug(f"[{operation_id}] Audio files: {[os.path.basename(f) for f in audio_files]}")

    # Collect video files
    for file in os.listdir(DEFAULT_SESSION_DIR):
        if file.endswith(".mp4"):
            order = file.split("-")[0]
            video_files[order] = os.path.join(DEFAULT_SESSION_DIR, file)
    video_files.sort()
    logger.info(f"[{operation_id}] Found {len(video_files)} video files for merging")
    logger.debug(f"[{operation_id}] Video files by order: {list(video_files.keys())}")

    # Map audio files to their corresponding videos
    for audio_file in audio_files:
        audio_filename = os.path.basename(audio_file)
        logger.debug(f"[{operation_id}] Processing audio: {audio_filename}")
        strings = audio_file.split("/")[-1].split("-")
        order = strings[0]
        character_name = strings[1]
        start_time = strings[2].split(".")[0]

        if order not in video_files:
            logger.warning(f"[{operation_id}] No video file found for audio order={order}, character={character_name}. Skipping.")
            continue

        video_file = video_files[order]
        logger.debug(f"[{operation_id}] Mapping audio to video: order={order}, character={character_name}, start_time={start_time}s, video={os.path.basename(video_file)}")

        if merged_list.get(video_file) is None:
            merged_list[video_file] = {"audios": [{"audio_file": audio_file, "start_time": start_time}]}
        else:
            merged_list[video_file]["audios"].append({"audio_file": audio_file, "start_time": start_time})

    logger.info(f"[{operation_id}] Merging audio into {len(merged_list)} videos")

    # Merge audio into videos
    total_merges = 0
    for video_file in merged_list.keys():
        merged_video = video_file.split(".")[0] + "-merged.mp4"
        audios = merged_list[video_file]["audios"]
        logger.info(f"[{operation_id}] Processing video: {os.path.basename(video_file)} with {len(audios)} audio tracks")

        for idx, audio in enumerate(audios, 1):
            audio_filename = os.path.basename(audio["audio_file"])
            logger.debug(f"[{operation_id}] Merging audio {idx}/{len(audios)}: {audio_filename} at {audio['start_time']}s")
            try:
                if os.path.exists(merged_video):
                    merge_audio_at_time(merged_video, audio["audio_file"], merged_video, int(audio["start_time"]))
                else:
                    merge_audio_at_time(video_file, audio["audio_file"], merged_video, int(audio["start_time"]))
                total_merges += 1
            except Exception as e:
                logger.error(
                    f"[{operation_id}] Failed to merge audio into video: {str(e)}",
                    exc_info=True,
                    extra={
                        "operation_id": operation_id,
                        "video_file": video_file,
                        "audio_file": audio["audio_file"],
                        "start_time": audio["start_time"]
                    }
                )

    duration = time.time() - start_time
    logger.info(f"[{operation_id}] Audio-video merge completed: videos={len(merged_list)}, total_audio_merges={total_merges}, duration={duration:.2f}s")
