
import os
import re
import time
import gradio as gr
from utils.ce_audio import generate_audio_by_gemini, choose_random_voice
from utils.logger import logger
import json
from handlers.ui_handlers import clear_temp_files
from utils.video_ts import merge_audio_at_time


def generate_audio():
    clear_temp_files("tmp/default", ".wav")
    all_audio_files = {}
    audio_files = []
    random_voice={}
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_script_") and file.endswith(".txt"):
            logger.info(f"script file: {file}")
            order = file.split(".")[0].split("_")[2]
            string_script = open(f"tmp/images/default/{file}", "r").read()
            json_script = json.loads(string_script)
            for script in json_script:
                character_name=script["character"]
                gender=script["gender"]
                message=script["dialogue"]
                start_time=script["time"]
                # message = f"Say in Singaporean TONE: {message}"
                # Ignore feeling in the message, eg: (Gasps softly)
                message = re.sub(r"\(.*?\)", '', message)
                if len(message) > 0:
                    message = f"Say: {message}"
                    if random_voice.get(character_name) is None:
                        random_voice[character_name] = choose_random_voice(gender)
                    voice_name = random_voice[character_name]
                    print(f"Generating audio for {character_name} with voice {voice_name}")
                    audio_files.append(generate_audio_by_gemini(message, gender, order, character_name, start_time, voice_name))
                    # Add a small delay between audio generation due to rate limit
                    time.sleep(5)
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
    print(all_audio_files)
    
    # Create a list of Dropdown updates
    dropdown_updates = []
    for i in range(1, 13):
        dropdown_updates.append(gr.Dropdown(choices=all_audio_files[str(i)]))
    return dropdown_updates

def show_generated_audios():
    all_audio_files = {}
    path = "tmp/default"
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".wav"):
                order = file.split("-")[0]
                if all_audio_files.get(order) is None:
                    all_audio_files[order]= [f"tmp/default/{file}"]
                else:
                    all_audio_files[order].append(f"tmp/default/{file}")
    
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
    audio_files = []
    video_files = {}
    merged_list = {}
    for file in os.listdir("tmp/default"):
        if file.endswith(".wav"):
            audio_files.append(f"tmp/default/{file}")
    print("===========audio_files=============")
    print(audio_files)
    print("===========audio_files=============")

    for file in os.listdir("tmp/default"):
        if file.endswith(".mp4"):
            # video_files.append(f"tmp/default/{file}")
            order = file.split("-")[0]
            video_files[order] = f"tmp/default/{file}"
    print("===========video_files=============")
    print(video_files)
    print("===========video_files=============")
    
    for audio_file in audio_files:
        print(f"audio_file: {audio_file}")
        strings = audio_file.split("/")[-1].split("-")
        print(f"strings: {strings}")
        order = strings[0]
        character_name = strings[1]
        start_time = strings[2].split(".")[0]
        video_file = video_files[order]
        print(f"video_file: {video_file}")

        if merged_list.get(video_file) is None:
            merged_list[video_file] = {"audios": [{"audio_file": audio_file, "start_time": start_time}]}
        else:
            merged_list[video_file]["audios"].append({"audio_file": audio_file, "start_time": start_time})
    print("===========merged_list=============")
    print(merged_list)
    print("===========merged_list=============")

    
    for video_file in merged_list.keys():
        merged_video=video_file.split(".")[0] + "-merged.mp4"
        audios = merged_list[video_file]["audios"]
        for audio in audios:
            print(f"audio: {audio}")
            if os.path.exists(merged_video):
                merge_audio_at_time(merged_video, audio["audio_file"], merged_video, int(audio["start_time"]))
            else:
                merge_audio_at_time(video_file, audio["audio_file"], merged_video, int(audio["start_time"]))
