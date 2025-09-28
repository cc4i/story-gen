import os
from moviepy import VideoFileClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip


# merge mutiple videos into one
def merge_videos_moviepy(video_path="tmp/default", output_path="tmp/default/merged_video.mp4", method="compose"):
    """
    Merge multiple videos into one using MoviePy.

    Args:
        video_path (str): Path to the directory containing the videos to merge.
        output_path (str): Path to save the merged output video file.
        method (str): Method to use for merging.
    """

    print(f"Attempting to merge videos under {video_path} into {output_path} using MoviePy...")
    clip_paths = []
    clips = []
    try:
        # Load each video file into a VideoFileClip object
        for file in os.listdir(video_path):
            if file.endswith("0.mp4"):
                print(f"Loading clip: {file}")
                clip_paths.append(f"{video_path}/{file}")
        
        # sort clip_paths by order
        clip_paths.sort()
        for path in clip_paths:
            clips.append(VideoFileClip(path))

        if not clips:
            print("No valid video clips loaded.")
            return False

        # Concatenate the video clips
        print(f"Concatenating clips using method='{method}'...")
        final_clip = concatenate_videoclips(clips, method=method)

        # Write the result to a file
        # You can specify codecs, bitrate, threads, ffmpeg_params etc. for more control
        # libx264 is a common video codec, aac is a common audio codec
        print(f"Writing final video to {output_path}...")
        final_clip.write_videofile(output_path,
                                 codec="libx264",        # Video codec
                                 audio_codec="aac",       # Audio codec
                                 temp_audiofile='temp-audio.m4a', # Temporary file for audio processing
                                 remove_temp=True,        # Remove the temp file after processing
                                 threads=4,               # Number of threads to use (adjust as needed)
                                 preset='medium',         # FFMPEG preset for speed vs quality (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
                                 ffmpeg_params=["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"] # Example: Ensure dimensions are even for some codecs
                                 )

        print(f"Successfully merged videos into {output_path}")

        # Close all the clips to free up resources
        final_clip.close()
        for clip in clips:
            clip.close()

        return output_path

    except Exception as e:
        print(f"An error occurred during merging with MoviePy: {e}")
        # Ensure cleanup even on error
        if 'final_clip' in locals() and final_clip:
            try: final_clip.close()
            except: pass
        for clip in clips:
            try: clip.close()
            except: pass
        return None

# merge audio at a specific time
def merge_audio_at_time(video_path, audio_path, output_path, start_time_seconds):
    """
    Merges audio from an audio file onto a video file, starting at a specific time.
    The new audio will be layered over the original video audio (if any).

    Args:
        video_path (str): Path to the input video file.
        audio_path (str): Path to the input audio file.
        output_path (str): Path to save the merged output video file.
        start_time_seconds (float): The time (in seconds) in the video where
                                     the new audio should start playing.
    """
    print(f"Loading video clip: {video_path}")
    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration

    # Validate start time
    if start_time_seconds < 0:
        print("Error: Start time cannot be negative.")
        video_clip.close()
        return
    if start_time_seconds >= video_duration:
        print(f"Warning: Start time ({start_time_seconds}s) is at or after the video duration ({video_duration}s). Audio may not play.")
        # You might choose to return here or proceed (audio won't be heard)

    print(f"Loading audio clip: {audio_path}")
    new_audio_clip = AudioFileClip(audio_path)

    print(f"Positioning new audio to start at {start_time_seconds} seconds...")
    # Set the start time for the new audio clip relative to the video timeline
    positioned_audio = new_audio_clip.with_start(start_time_seconds)

    # Get the original audio from the video clip, if it exists
    original_audio = video_clip.audio
    audio_clips_to_composite = []

    if original_audio:
        print("Original video has audio. Layering new audio over it.")
        # If you wanted to *replace* the original audio from start_time_seconds onwards,
        # you would need to cut the original audio:
        # original_audio_part1 = original_audio.subclip(0, start_time_seconds)
        # audio_clips_to_composite.append(original_audio_part1)
        # audio_clips_to_composite.append(positioned_audio)

        # For layering/mixing: include both original and positioned new audio
        audio_clips_to_composite.append(original_audio)
        audio_clips_to_composite.append(positioned_audio)
    else:
        print("Original video has no audio. Adding new audio.")
        # If there's no original audio, just use the positioned new audio
        audio_clips_to_composite.append(positioned_audio)


    print("Creating final composite audio...")
    # Create a composite audio clip. If the list contains the original audio
    # and the positioned new audio, they will be mixed/layered.
    final_audio = CompositeAudioClip(audio_clips_to_composite)

    print("Setting final audio for the video clip...")
    # Set the composite audio to the video clip
    final_clip = video_clip.with_audio(final_audio)

    # Ensure the final duration is capped by the video's duration
    # Moviepy usually handles this, but explicit setting can prevent issues.
    final_clip = final_clip.with_duration(video_duration)

    print(f"Writing final video to: {output_path}")
    try:
        # Write the result to a file
        final_clip.write_videofile(output_path,
                                   codec='libx264',
                                   audio_codec='aac',
                                   temp_audiofile='temp-audio.m4a',
                                   remove_temp=True,
                                   threads=4,
                                   logger='bar')
        print("Merging complete!")

    except Exception as e:
        print(f"\nAn error occurred during video writing: {e}")
        print("Please check file paths, permissions, and available disk space.")
        # Add more specific error handling if needed

    finally:
        # Good practice: Ensure all clips are closed to release file handles
        print("Closing clips...")
        if original_audio:
            original_audio.close()
        new_audio_clip.close()
        # positioned_audio doesn't need explicit closing as it's derived
        # final_audio doesn't need explicit closing
        video_clip.close()
        if 'final_clip' in locals() and final_clip: # Check if final_clip was created
             final_clip.close()