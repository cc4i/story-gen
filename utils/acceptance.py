
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


def to_snake_case_v2(name):
    """
    Converts a string to snake_case.
    Handles CamelCase, PascalCase, spaces, and hyphens.
    """
    # 1. Replace any non-alphanumeric characters (except underscores) with spaces.
    #    This helps normalize different separators (like !, @, #, etc.)
    name = re.sub(r'[^a-zA-Z0-9_]', ' ', name)

    # 2. Convert to snake_case from PascalCase or CamelCase
    #    Insert an underscore before any uppercase letter that is not at the start
    #    and is followed by a lowercase letter OR
    #    is preceded by a lowercase letter/digit and followed by an uppercase letter/digit
    name = re.sub(r'(?<!^)(?=[A-Z][a-z])', '_', name)
    name = re.sub(r'(?<!^)(?=[A-Z][A-Z0-9_]*$)', '_', name) # for cases like 'HTMLTest' -> 'html_test'

    # Handle numbers: insert underscore before a digit if preceded by a letter/underscore
    name = re.sub(r'(?<=[a-zA-Z_])(?=[0-9])', '_', name)
    # Handle numbers: insert underscore after a digit if followed by a letter/underscore
    name = re.sub(r'(?<=[0-9])(?=[a-zA-Z_])', '_', name)


    # 3. Replace spaces and hyphens with underscores
    name = re.sub(r'[-\s]+', '_', name)

    # 4. Convert the string to lowercase
    name = name.lower()

    # 5. Remove any leading/trailing underscores
    name = name.strip('_')

    # 6. Remove any multiple underscores
    name = re.sub(r'_{2,}', '_', name)

    return name