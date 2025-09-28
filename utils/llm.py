"""
LLM (Large Language Model) utilities for text generation using Google's Gemini model.
"""

import json
import logging
from typing import Optional, List, Dict, Any

from google import genai
from google.genai import types

from models.config import DEFAULT_MODEL_ID, GEMINI_API_KEY
from models.exceptions import APIError, ValidationError

from utils.logger import logger

# Constants
TEMPERATURE = 0.7
TOP_P = 0.95
TOP_K = 64
MAX_OUTPUT_TOKENS = 65536

def string_to_pjson(json_string: str) -> Optional[str]:
    """
    Converts a JSON string to a properly formatted JSON string.

    Args:
        json_string: Input JSON string that may contain markdown code block markers

    Returns:
        Cleaned JSON string or None if invalid

    Raises:
        ValidationError: If the input string is empty or invalid
    """
    if not json_string or not isinstance(json_string, str):
        raise ValidationError("Input must be a non-empty string")

    try:
        # Remove the ```json and ``` markers
        json_str = json_string.strip()
        markers = ["```json", "``` JSON", "```"]
        for marker in markers:
            json_str = json_str.replace(marker, "")
        json_str = json_str.strip()
        
        # Validate JSON
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON string: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing JSON string: {str(e)}")
        raise ValidationError(f"Failed to process JSON string: {str(e)}")

def call_llm(
    system_instruction: str,
    prompt: str,
    history: str,
    model_id: str = DEFAULT_MODEL_ID
) -> str:
    """
    Calls the Gemini LLM model to generate text content.

    Args:
        system_instruction: System-level instruction for the model
        prompt: User prompt for text generation
        history: Conversation history (currently unused)
        model_id: ID of the model to use

    Returns:
        Generated text response

    Raises:
        APIError: If the API request fails
        ValidationError: If input parameters are invalid
    """
    try:
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("Prompt must be a non-empty string")
        if not model_id or not isinstance(model_id, str):
            raise ValidationError("Model ID must be a non-empty string")

        # Initialize client
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={'api_version': 'v1alpha'}
        )

        # Configure generation parameters
        generate_content_config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_CIVIC_INTEGRITY",
                    threshold="OFF",
                ),
            ],
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text=system_instruction),
            ],
        )

        # Prepare content
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        # Generate content
        logger.info(f"Generating content with model: {model_id}")
        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=generate_content_config
        )

        # Process response
        if not response or not response.text:
            raise APIError("No response received from Gemini API")

        # Convert response to JSON if possible
        result = string_to_pjson(response.text)
        if result is None:
            logger.warning("Response was not valid JSON, returning raw text")
            return response.text

        return result

    except Exception as e:
        logger.error(f"Error in LLM call: {str(e)}")
        raise APIError(f"Failed to generate content: {str(e)}")



