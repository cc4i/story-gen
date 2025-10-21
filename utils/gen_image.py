
import os
from google import genai
from google.genai import types
from models.config import GEMINI_API_KEY

def gen_images(model_id, prompt, negative_prompt, number_of_images, aspect_ratio, is_enhance):
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    print(f"model_id: {model_id}, prompt: {prompt}, negative_prompt: {negative_prompt}, number_of_images: {number_of_images}, aspect_ratio: {aspect_ratio}, is_enhance: {is_enhance}")
    if is_enhance=="yes":
        enhance_prompt = True
    else:
        enhance_prompt = False

    response = client.models.generate_images(
        model=model_id,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            # negative_prompt =negative_prompt,
            number_of_images= number_of_images,
            aspect_ratio = aspect_ratio,
            # enhance_prompt=enhance_prompt,
            person_generation = "ALLOW_ADULT"
        )
    )
    return response.generated_images


def gen_images_by_banana(prompt, negative_prompt="", number_of_images=1, aspect_ratio="1:1", reference_images=None):
    """
    Generate images using Gemini 2.5 Flash Image model (gemini-2.5-flash-image)

    Args:
        prompt (str): The image generation prompt
        negative_prompt (str): Negative prompt to avoid certain features (optional, appended to prompt)
        number_of_images (int): Number of images to generate (1-4)
        aspect_ratio (str): Aspect ratio - supported values: "1:1", "2:3", "3:2", "4:3", "5:4", "9:16", "16:9", "21:9"
        reference_images (list, optional): List of reference images (max 3). Can be:
            - File paths (str): e.g., ["/path/to/image1.png", "/path/to/image2.png"]
            - PIL Image objects: e.g., [Image.open("image1.png"), Image.open("image2.png")]
            - Mixed: e.g., ["/path/to/image1.png", Image.open("image2.png")]

    Returns:
        list: List of generated image byte data

    Example:
        >>> # Without reference images
        >>> images = gen_images_by_banana("A nano banana in a fancy restaurant", aspect_ratio="16:9")
        >>>
        >>> # With reference images
        >>> ref_imgs = ["/path/to/style.png", "/path/to/reference.png"]
        >>> images = gen_images_by_banana("A nano banana", reference_images=ref_imgs)
        >>>
        >>> from PIL import Image
        >>> from io import BytesIO
        >>> img = Image.open(BytesIO(images[0]))
        >>> img.save("output.png")
    """
    from PIL import Image
    from io import BytesIO

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Validate aspect ratio
    valid_aspect_ratios = ["1:1", "2:3", "3:2", "4:3", "5:4", "9:16", "16:9", "21:9"]
    if aspect_ratio not in valid_aspect_ratios:
        print(f"Warning: Invalid aspect ratio '{aspect_ratio}'. Using '1:1' instead.")
        aspect_ratio = "1:1"

    # Validate and process reference images
    processed_ref_images = []
    if reference_images:
        if len(reference_images) > 3:
            print(f"Warning: Maximum 3 reference images allowed. Using first 3 images only.")
            reference_images = reference_images[:3]

        for idx, ref_img in enumerate(reference_images):
            try:
                if isinstance(ref_img, str):
                    # File path - load the image
                    processed_ref_images.append(Image.open(ref_img))
                    print(f"Loaded reference image {idx+1}: {ref_img}")
                elif isinstance(ref_img, Image.Image):
                    # Already a PIL Image
                    processed_ref_images.append(ref_img)
                    print(f"Using reference image {idx+1}: PIL Image object")
                else:
                    print(f"Warning: Reference image {idx+1} has invalid type. Skipping.")
            except Exception as e:
                print(f"Warning: Could not load reference image {idx+1}: {e}")

    # Combine prompt with negative prompt if provided
    full_prompt = prompt
    if negative_prompt:
        full_prompt = f"{prompt}. Avoid: {negative_prompt}"

    print(f"Generating image with Gemini 2.5 Flash Image model")
    print(f"Prompt: {full_prompt}")
    print(f"Aspect ratio: {aspect_ratio}")
    print(f"Reference images: {len(processed_ref_images)}")

    generated_images = []

    # Generate images (one at a time since Gemini doesn't support batch generation)
    for i in range(number_of_images):
        try:
            # Add aspect ratio instruction to the prompt since ImageConfig doesn't exist
            prompt_with_ratio = f"{full_prompt}\n\nGenerate the image with aspect ratio {aspect_ratio}."

            # Build contents list: reference images first, then text prompt
            contents = processed_ref_images + [prompt_with_ratio]

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['Image']  # Only return image
                )
            )

            # Extract image data from response
            image_parts = [
                part.inline_data.data
                for part in response.candidates[0].content.parts
                if part.inline_data
            ]

            if image_parts:
                generated_images.append(image_parts[0])
                print(f"Successfully generated image {i+1}/{number_of_images}")
            else:
                print(f"Warning: No image data in response for image {i+1}/{number_of_images}")

        except Exception as e:
            print(f"Error generating image {i+1}/{number_of_images}: {e}")
            raise Exception(f"Gemini image generation failed: {str(e)}")

    return generated_images

