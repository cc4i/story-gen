
import numpy as np
import re

def sepia(input_image):
    sepia_filter = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = input_image.dot(sepia_filter.T)
    sepia_img /= sepia_img.max()
    return sepia_img

def show(input_image):
    return input_image

def to_snake_case(input_string):
    """
    Converts a string to snake_case, keeping only numbers and letters,
    and replacing everything else with underscores.
    """
    # Replace non-alphanumeric characters with underscores
    s1 = re.sub(r'[^a-zA-Z0-9\.]+', '_', input_string)
    # Remove leading/trailing underscores
    s2 = s1.strip('_')
    # Convert to lowercase
    s3 = s2.lower()
    return s3