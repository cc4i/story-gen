
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