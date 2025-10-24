
import os
from moviepy import VideoFileClip, concatenate_videoclips, CompositeAudioClip, AudioFileClip
from utils.config import VIDEOS_DIR, MERGED_VIDEO_MP4
from utils.logger import logger

# merge mutiple videos into one
def merge_videos_moviepy(video_path=VIDEOS_DIR, output_path=MERGED_VIDEO_MP4, method="compose"):
    """
    Merge multiple videos into one using MoviePy.

    Args:
        video_path (str): Path to the directory containing the videos to merge.
        output_path (str): Path to save the merged output video file.
        method (str): Method to use for merging.
    """

    logger.info(f"Starting video merge: source={video_path}, output={output_path}, method={method}")
    clip_paths = []
    clips = []
    try:
        # Load each video file into a VideoFileClip object
        for file in os.listdir(video_path):
            if file.endswith("_0.mp4"):
                logger.debug(f"Found clip: {file}")
                clip_paths.append(os.path.join(video_path, file))

        # Sort clip_paths by sequence number (numeric sort, not alphabetical)
        # Files are named like: sequence-uuid-video_0.mp4
        # Extract the sequence number (first part before dash) and sort numerically
        def get_sequence_number(path):
            filename = os.path.basename(path)
            # Extract sequence number from filename like "1-uuid-video_0.mp4"
            try:
                seq_num = int(filename.split('-')[0])
                logger.debug(f"Extracted sequence {seq_num} from {filename}")
                return seq_num
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not extract sequence from {filename}: {e}")
                return 0

        logger.info(f"Sorting {len(clip_paths)} clips by sequence number")
        clip_paths.sort(key=get_sequence_number)

        logger.info(f"Loading {len(clip_paths)} clips in sorted order")
        for path in clip_paths:
            logger.debug(f"Loading clip: {os.path.basename(path)}")
            clips.append(VideoFileClip(path))
        

        if not clips:
            logger.warning("No valid video clips found to merge")
            return False

        # Debug: Print final clips order before concatenation
        logger.info(f"Final clips order (total: {len(clips)}):")
        for i, (path, clip) in enumerate(zip(clip_paths, clips)):
            filename = os.path.basename(path)
            logger.info(f"  {i+1}. {filename} (duration: {clip.duration:.2f}s)")

        # Concatenate the video clips
        logger.info(f"Concatenating {len(clips)} clips using method='{method}'")
        final_clip = concatenate_videoclips(clips, method=method)

        # Write the result to a file
        # You can specify codecs, bitrate, threads, ffmpeg_params etc. for more control
        # libx264 is a common video codec, aac is a common audio codec
        logger.info(f"Writing merged video to: {output_path}")
        final_clip.write_videofile(output_path,
                                 codec="libx264",        # Video codec
                                 audio_codec="aac",       # Audio codec
                                 temp_audiofile='temp-audio.m4a', # Temporary file for audio processing
                                 remove_temp=True,        # Remove the temp file after processing
                                 threads=4,               # Number of threads to use (adjust as needed)
                                 preset='medium',         # FFMPEG preset for speed vs quality (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
                                 ffmpeg_params=["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"] # Example: Ensure dimensions are even for some codecs
                                 )

        logger.info(f"Successfully merged {len(clips)} videos into: {output_path}")

        # Close all the clips to free up resources
        final_clip.close()
        for clip in clips:
            clip.close()

        return output_path

    except Exception as e:
        logger.error(f"Video merge failed: {str(e)}")
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
    logger.info(f"Loading video clip: {video_path}")
    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration

    # Validate start time
    if start_time_seconds < 0:
        logger.error("Start time cannot be negative")
        video_clip.close()
        return
    if start_time_seconds >= video_duration:
        logger.warning(f"Start time ({start_time_seconds}s) is at or after video duration ({video_duration}s). Audio may not play.")
        # You might choose to return here or proceed (audio won't be heard)

    logger.info(f"Loading audio clip: {audio_path}")
    new_audio_clip = AudioFileClip(audio_path)

    logger.info(f"Positioning audio to start at {start_time_seconds}s")
    # Set the start time for the new audio clip relative to the video timeline
    positioned_audio = new_audio_clip.with_start(start_time_seconds)

    # Get the original audio from the video clip, if it exists
    original_audio = video_clip.audio
    audio_clips_to_composite = []

    if original_audio:
        logger.info("Layering new audio over existing video audio")
        # If you wanted to *replace* the original audio from start_time_seconds onwards,
        # you would need to cut the original audio:
        # original_audio_part1 = original_audio.subclip(0, start_time_seconds)
        # audio_clips_to_composite.append(original_audio_part1)
        # audio_clips_to_composite.append(positioned_audio)

        # For layering/mixing: include both original and positioned new audio
        audio_clips_to_composite.append(original_audio)
        audio_clips_to_composite.append(positioned_audio)
    else:
        logger.info("No existing audio, adding new audio track")
        # If there's no original audio, just use the positioned new audio
        audio_clips_to_composite.append(positioned_audio)


    logger.info("Creating composite audio track")
    # Create a composite audio clip. If the list contains the original audio
    # and the positioned new audio, they will be mixed/layered.
    final_audio = CompositeAudioClip(audio_clips_to_composite)

    logger.info("Applying audio to video")
    # Set the composite audio to the video clip
    final_clip = video_clip.with_audio(final_audio)

    # Ensure the final duration is capped by the video's duration
    # Moviepy usually handles this, but explicit setting can prevent issues.
    final_clip = final_clip.with_duration(video_duration)

    logger.info(f"Writing final video to: {output_path}")
    try:
        # Write the result to a file
        final_clip.write_videofile(output_path,
                                   codec='libx264',
                                   audio_codec='aac',
                                   temp_audiofile='temp-audio.m4a',
                                   remove_temp=True,
                                   threads=4,
                                   logger='bar')
        logger.info("Audio merge completed successfully")

    except Exception as e:
        logger.error(f"Video writing failed: {str(e)}")
        logger.error("Please check file paths, permissions, and available disk space")
        # Add more specific error handling if needed

    finally:
        # Good practice: Ensure all clips are closed to release file handles
        logger.debug("Closing clips")
        if original_audio:
            original_audio.close()
        new_audio_clip.close()
        # positioned_audio doesn't need explicit closing as it's derived
        # final_audio doesn't need explicit closing
        video_clip.close()
        if 'final_clip' in locals() and final_clip: # Check if final_clip was created
             final_clip.close()