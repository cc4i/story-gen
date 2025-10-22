"""
Video generation utilities using Google's Veo 2.0 model.
"""

import time
import os
import uuid
from typing import Dict, List, Optional, Tuple, Any
import google.auth
import google.auth.transport.requests
import requests
from google.cloud import storage
import subprocess
import tempfile
import json

from utils.llm import call_llm
from models.config import VEO_PROJECT_ID, LOCAL_STORAGE, VEO_STORAGE_BUCKET, PROJECT_ID
from utils.acceptance import to_snake_case
from models.exceptions import APIError, StorageError, FileUploadError

from utils.logger import logger



# API endpoints
video_model = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{VEO_PROJECT_ID}/locations/us-central1/publishers/google/models"

# Constants
VIDEO_GENERATION_TIMEOUT = 300  # 5 minutes
POLLING_INTERVAL = 10
MAX_RETRIES = 30

def prediction_endpoint(model_id: str) -> str:
    return f"{video_model}/{model_id}:predictLongRunning"

def fetch_endpoint(model_id: str) -> str:
    return f"{video_model}/{model_id}:fetchPredictOperation"

def upload_local_file_to_gcs(bucket_name: str, sub_folder: str, local_file_path: str) -> str:
    """
    Uploads a local file to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        sub_folder: Subfolder path in the bucket
        local_file_path: Path to the local file

    Returns:
        The GCS URI of the uploaded file

    Raises:
        StorageError: If the upload operation fails
    """
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(bucket_name)

        blob_name = to_snake_case(local_file_path.split("/")[-1])
        if sub_folder:
            blob_name = f"{sub_folder}/{blob_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"File {local_file_path} uploaded to {gcs_uri}")
        return gcs_uri
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise StorageError(f"Failed to upload file to GCS: {str(e)}")
    
def upload_image(input_image_path: str, whoami: str) -> str:
    """
    Upload an image to Google Cloud Storage.
    
    Args:
        input_image_path: Path to the image file
        whoami: User identifier
        
    Returns:
        GCS path of the uploaded file
        
    Raises:
        FileUploadError: If upload fails
    """
    try:
        logger.info(f"Uploading image: {input_image_path} for user: {whoami}")
        return upload_local_file_to_gcs(
            f"{VEO_STORAGE_BUCKET}", 
            f"uploaded-images-for-marketing-short/{whoami}", 
            input_image_path
        )
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise FileUploadError(f"Failed to upload image: {str(e)}")
    
def send_request_to_google_api(api_endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sends an HTTP request to a Google API endpoint.

    Args:
        api_endpoint: The URL of the Google API endpoint.
        data: Optional dictionary of data to send in the request body.

    Returns:
        The response from the Google API.

    Raises:
        APIError: If the API request fails.
    """
    try:
        # Get access token calling API
        creds, project = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        access_token = creds.token

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(api_endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise APIError(f"Failed to send request to Google API: {str(e)}")


def compose_videogen_request(
    prompt: str,
    image_uri: Optional[str],
    image_uri_last: Optional[str],
    gcs_uri: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    negative_prompt: str,
    person_generation: str = "allow_adult",
    enhance_prompt: str = "true",
    duration_seconds: int = 8,
    generate_audio: Optional[str] = None,
    resolution: str = "720p"
) -> Dict[str, Any]:
    """
    Composes a request for video generation.

    Args:
        prompt: Text prompt for video generation
        image_uri: Optional GCS URI of input image
        gcs_uri: GCS URI for output storage
        seed: Random seed for generation
        aspect_ratio: Video aspect ratio
        sample_count: Number of videos to generate
        negative_prompt: Text describing what to avoid
        person_generation: Person generation policy
        enhance_prompt: Whether to enhance the prompt
        duration_seconds: Video duration in seconds
        generate_audio: Whether to generate audio ("true" or "false")
        resolution: Video resolution (720p, 1080p), only for veo-3.0 model

    Returns:
        Dictionary containing the composed request
    """
    
    instance = {"prompt": prompt}
    if image_uri:
        instance["image"] = {"gcsUri": image_uri, "mimeType": "png"}
    if image_uri_last:
        instance["lastFrame"] = {"gcsUri": image_uri_last, "mimeType": "png"}
    
    if generate_audio:
        return {
            "instances": [instance],
            "parameters": {
                "storageUri": gcs_uri,
                "sampleCount": sample_count,
                "seed": seed,
                "aspectRatio": aspect_ratio,
                "negativePrompt": negative_prompt,
                "personGeneration": person_generation,
                "resolution": resolution,
                "enhancePrompt": enhance_prompt.lower() == "true",
                "durationSeconds": duration_seconds,
                "generateAudio": generate_audio.lower() == "true"
            },
        }
    else:
        return {
            "instances": [instance],
            "parameters": {
                "storageUri": gcs_uri,
                "sampleCount": sample_count,
                "seed": seed,
                "aspectRatio": aspect_ratio,
                "negativePrompt": negative_prompt,
                "personGeneration": person_generation,
                "resolution": resolution,
                "enhancePrompt": enhance_prompt.lower() == "true",
                "durationSeconds": duration_seconds
            },
        }
    

def fetch_operation(model_id: str, lro_name: str, itr: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    Fetches the status of a long-running operation.

    Args:
        lro_name: Name of the long-running operation
        itr: Maximum number of iterations to wait

    Returns:
        Operation response from Google API

    Raises:
        APIError: If the operation fails or times out
    """
    request = {"operationName": lro_name}
    for i in range(itr):
        try:
            resp = send_request_to_google_api(fetch_endpoint(model_id), request)
            if "done" in resp and resp["done"]:
                logger.info(f"Operation {lro_name} completed successfully")
                return resp
            time.sleep(POLLING_INTERVAL)
        except APIError as e:
            logger.error(f"Error fetching operation {lro_name}: {str(e)}")
            raise
    
    raise APIError(f"Operation {lro_name} timed out after {itr * POLLING_INTERVAL} seconds")

def text_to_video(
    model_id: str,
    prompt: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    output_gcs: str,
    negative_prompt: str,
    enhance: str,
    durations: int,
    generate_audio: str,
    resolution: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a video from text using Google's Veo 2.0 model.

    Args:
        model_id: The ID of the model to use
        prompt: The text prompt describing the video to generate
        seed: Random seed for generation (0-4294967295)
        aspect_ratio: Video aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4)
        sample_count: Number of videos to generate (1-5)
        output_gcs: Google Cloud Storage URI for output
        negative_prompt: Text describing what to avoid in generation
        enhance: Whether to enhance the prompt ("yes" or "no")
        durations: Video duration in seconds (5-8)
        generate_audio: Whether to generate audio ("true" or "false")
        resolution: Video resolution (720p, 1080p), only for veo-3.0 model

    Returns:
        Tuple containing:
        - Operation response from Google API
        - Dictionary containing request and response details

    Raises:
        ValueError: If input parameters are invalid
        APIError: If the API request fails
    """
    logger.info(f"model_id: {model_id}")
    logger.info(f"Starting text-to-video generation with prompt: {prompt}")
    if "2.0" in model_id:
        # handle logic for 2.0 model
        generate_audio = None
    req = compose_videogen_request(
        prompt, None, None, output_gcs, seed, aspect_ratio, sample_count, 
        negative_prompt, "allow_adult", enhance, durations, generate_audio, resolution
    )
    logger.info(f"Composed request: {json.dumps(req, indent=4)}")
    resp = send_request_to_google_api(prediction_endpoint(model_id), req)
    logger.info(f"Received initial response for operation: {resp}")
    r_resp = fetch_operation(model_id, resp["name"])
    return r_resp, {"req": req, "resp": r_resp}

def image_to_video(
    model_id: str,
    prompt: str,
    image_gcs: str,
    image_gcs_last: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    output_gcs: str,
    negative_prompt: str,
    enhance: str,
    durations: int,
    generate_audio: str,
    resolution: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a video from an image using Google's Veo 2.0 model.

    Args:
        model_id: The ID of the model to use
        prompt: The text prompt describing the video to generate
        image_gcs: GCS URI of the input image
        image_gcs_last: GCS URI of the input last image
        seed: Random seed for generation (0-4294967295)
        aspect_ratio: Video aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4)
        sample_count: Number of videos to generate (1-5)
        output_gcs: Google Cloud Storage URI for output
        negative_prompt: Text describing what to avoid in generation
        enhance: Whether to enhance the prompt ("yes" or "no")
        durations: Video duration in seconds (5-8)
        generate_audio: Whether to generate audio ("true" or "false")
        resolution: Video resolution (720p, 1080p), only for veo-3.0 model

    Returns:
        Tuple containing:
        - Operation response from Google API
        - Dictionary containing request and response details

    Raises:
        ValueError: If input parameters are invalid
        APIError: If the API request fails
    """
    logger.info(f"model_id: {model_id}")
    logger.info(f"Starting image-to-video generation with prompt: {prompt}")
    
    if "2.0" in model_id:
        # handle logic for 2.0 model
        logger.info(f"image_gcs: {image_gcs}")
        logger.info(f"image_gcs_last: {image_gcs_last}")
        generate_audio = None
        if image_gcs_last and image_gcs_last!="":
            req = compose_videogen_request(
                prompt, image_gcs, image_gcs_last, output_gcs, seed, aspect_ratio, sample_count,
                negative_prompt, "allow_adult", enhance, durations, generate_audio, resolution
            )
        else:
            req = compose_videogen_request(
                prompt, image_gcs, None, output_gcs, seed, aspect_ratio, sample_count,
                negative_prompt, "allow_adult", enhance, durations, generate_audio, resolution
            )
    else:
        req = compose_videogen_request(
            prompt, image_gcs, None, output_gcs, seed, aspect_ratio, sample_count,
            negative_prompt, "allow_adult", enhance, durations, generate_audio, resolution
        )
    logger.info(f"Composed request: {json.dumps(req, indent=4)}")
    resp = send_request_to_google_api(prediction_endpoint(model_id), req)
    logger.info(f"Received initial response for operation: {resp}")
    r_resp = fetch_operation(model_id, resp["name"])
    return r_resp, {"req": req, "resp": r_resp}

def copy_gcs_file_to_local(gcs_uri: str, local_file_path: str) -> None:
    """
    Copies a file from Google Cloud Storage to a local file path.

    Args:
        gcs_uri: The GCS URI of the file to copy
        local_file_path: The local file path where the file should be copied

    Raises:
        StorageError: If the file copy operation fails
    """
    try:
        client = storage.Client(project=os.getenv("PROJECT_ID"))
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_file_path)
        logger.info(f"File {gcs_uri} copied to {local_file_path}")
    except Exception as e:
        logger.error(f"Error copying file: {str(e)}")
        raise StorageError(f"Failed to copy file from GCS: {str(e)}")

def upload_local_file_to_gcs(bucket_name: str, sub_folder: str, local_file_path: str) -> str:
    """
    Uploads a local file to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        sub_folder: Subfolder path in the bucket
        local_file_path: Path to the local file

    Returns:
        The GCS URI of the uploaded file

    Raises:
        StorageError: If the upload operation fails
    """
    try:
        client = storage.Client(project=os.getenv("PROJECT_ID"))
        bucket = client.bucket(bucket_name)

        blob_name = to_snake_case(local_file_path.split("/")[-1])
        if sub_folder:
            blob_name = f"{sub_folder}/{blob_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"File {local_file_path} uploaded to {gcs_uri}")
        return gcs_uri
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise StorageError(f"Failed to upload file to GCS: {str(e)}")

def download_videos(op: Dict[str, Any], whoami: str, seqence: str, loop_seamless: bool) -> List[str]:
    """
    Downloads generated videos from GCS to local storage.

    Args:
        op: Operation response containing video information
        whoami: User identifier for local storage path
        seqence: Sequence number of the video
        loop_seamless: Whether to loop the video seamlessly
    Returns:
        List of local file paths for downloaded videos

    Raises:
        StorageError: If video download fails
    """
    logger.info("--------------------------------")
    logger.info(f"op: {op}")
    logger.info("--------------------------------")
    logger.info(f"Starting video download for user: {whoami}")
    local_path = f"{LOCAL_STORAGE}/{whoami}/videos"
    logger.info(f"local_path: {local_path}")

    if not os.path.exists(local_path):
        os.makedirs(local_path)
 
    l_files = []
    if op.get("error") is None:
        if op["response"]:
            if op["response"].get("raiMediaFilteredReasons") is None:
                logger.info(f"op['response']['videos']: {op['response']['videos']}")
                for video in op["response"]["videos"]:
                    gcs_uri = video["gcsUri"]
                    file_name = f"{local_path}/{seqence}-{str(uuid.uuid4())}-" + gcs_uri.split("/")[-1]
                    file_name_loop_seamless = f"{local_path}/{seqence}-{str(uuid.uuid4())}-loop_seamless-" + gcs_uri.split("/")[-1]
                    try:
                        copy_gcs_file_to_local(gcs_uri, file_name)
                        
                        if loop_seamless:
                            make_video_cyclic(file_name, file_name_loop_seamless)
                            l_files.append(file_name_loop_seamless)
                        else:
                            l_files.append(file_name)
                    except StorageError as e:
                        logger.error(f"Failed to download video: {str(e)}")
                        continue
    return l_files

def random_video_prompt() -> str:
    """
    Generates a random prompt for video generation using LLM.

    Returns:
        A randomly generated prompt string
    """
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt="""
            Generate a random prompt to text-to-image for Google Veo to generate a creative, inspirational video for landscapes, or cars, or nature, or technology, etc., which should boasts a cinematic quality with meticulously crafted shots and vibrant colors,  breathtaking, a true feast for the eyes.
            *INSTRUCTION*:
            The following elements should be included in your prompt:
                1. Subject: The object, person, animal, or scenery that you want in your video.
                2. Context: The background or context in which the subject is placed.
                3. Action: What the subject is doing (for example, walking, running, or turning their head).
                4. Style: This can be general or very specific. Consider using specific film style keywords, such as horror film, film noir, or animated styles like cartoon style render.
                5. Camera motion: Optional: What the camera is doing, such as aerial view, eye-level, top-down shot, or low-angle shot.
                6. Composition: Optional: How the shot is framed, such as wide shot, close-up, or extreme close-up.
                7. Ambiance: Optional: How the color and light contribute to the scene, such as blue tones, night, or warm tones.            
            *OUTPUT*:
            Output as string only, without explanation.
        """,
        history=""
    )

def rewrite_video_prompt(prompt: str) -> str:
    """
    Rewrites a video prompt to improve its quality using LLM.

    Args:
        prompt: The original prompt to improve

    Returns:
        An improved version of the prompt
    """
    return call_llm(
        system_instruction="You are a world-class prompt engineering expert. Your task is to take a user's prompt and rewrite it to be significantly more detailed, specific, and effective for Google models.",
        prompt=f"""
            Consider adding the following to enhance the prompt for Google Veo:
            - A clear persona for the AI (e.g., "Act as an expert marketer...").
            - A specific context or background.
            - A detailed description of the desired output format (e.g., markdown, JSON, a list of bullet points).
            - Key elements, constraints, or a specific tone to adopt.
            - A step-by-step thinking instruction if the task is complex.

            Return ONLY the rewritten, enhanced prompt. Do not include any explanations, preambles, or apologies.

            Original prompt:
            {prompt}
        """,
        history=""
    )

def make_video_cyclic(input_video_path, output_video_path):
    """
    Creates a seamlessly looping video by appending the first frame to the end.
    Uses FFmpeg directly for reliable video processing with smooth transition.

    Args:
        input_video_path (str): Path to the input video file
        output_video_path (str): Path where the cyclic output video will be saved
    """
    try:
        # Verify input file exists
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video file not found: {input_video_path}")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)

        # Create a temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Get video information for frame rate
            probe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'v:0',
                input_video_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, probe_cmd,
                    output=result.stdout, stderr=result.stderr
                )
            
            video_info = json.loads(result.stdout)
            fps = eval(video_info['streams'][0]['r_frame_rate'])

            # 2. Extract the first frame
            first_frame_path = os.path.join(temp_dir, "first_frame.png")
            logger.info(f"first_frame_path: {first_frame_path}")
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', os.path.abspath(input_video_path),
                '-vframes', '1',
                '-f', 'image2',
                first_frame_path
            ]
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, extract_cmd, 
                    output=result.stdout, stderr=result.stderr
                )

            # 3. Create a frame video with proper duration
            frame_video_path = os.path.join(temp_dir, "frame.mp4")
            frame_cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', first_frame_path,
                '-t', '0.25',  # Duration of 0.25 seconds for smoother transition
                '-r', str(fps),  # Match original frame rate
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                frame_video_path
            ]
            result = subprocess.run(frame_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, frame_cmd,
                    output=result.stdout, stderr=result.stderr
                )

            # 4. Create final video with crossfade transition
            concat_cmd = [
                'ffmpeg', '-y',
                '-i', input_video_path,
                '-i', frame_video_path,
                '-filter_complex',
                f'[0:v][1:v]xfade=transition=fade:duration=0.25:offset={max(0, float(video_info["streams"][0]["duration"]) - 0.25)}[v]',
                '-map', '[v]',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-profile:v', 'high',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-r', str(fps),  # Maintain original frame rate
                output_video_path
            ]
            result = subprocess.run(concat_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, concat_cmd,
                    output=result.stdout, stderr=result.stderr
                )

            logger.info(f"Successfully created smooth cyclic video: {output_video_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error:\nCommand: {' '.join(e.cmd)}\nOutput: {e.output}\nError: {e.stderr}")
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        raise RuntimeError("Failed to create cyclic video")
    except Exception as e:
        logger.error(f"Error creating cyclic video: {str(e)}")
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        raise

