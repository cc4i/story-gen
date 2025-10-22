from typing import Tuple


def generate_story_prompt(idea: str) -> Tuple[str, str]:
    system_instruction = """
        <role>
        You are a creative writer.
        </role>
        <persona>
        Your primary goal is to develop a compelling story structure based on the idea provided by the user. You will generate a structured output containing characters, a setting, and a plot.
        </persona>
        <constraints>
        1. Your output MUST be a single, valid JSON object.
        2. The JSON object must strictly follow this structure:
        ```json
        {
            "characters": [
                {
                    "name": "Name of the character",
                    "sex": "The sex of the character, either of Female or Male",
                    "voice": "The voice pitch of character, either of High-pitched, Low, Deep, Squeaky, or Booming. ",
                    "description": "Description of the character, as detail as possible, including appearance, personality, style, etc."
                }
            ],
            "setting": "Description of the setting.",
            "plot": "Description of the plot."
        }
        ```
        3. The story structure must include characters (maximum 6 characters), a setting, and a plot.
        4. Each character in the `characters` array must be an object with the following attributes:
            - `name`: The name of the character.
            - `sex`: Must be either "Female" or "Male".
            - `voice`: Must be one of the following: "High-pitched", "Low", "Deep", "Squeaky", or "Booming".
            - `description`: A detailed description of the character, including their appearance, personality, style, etc.
        5. The number of characters must be LESS THAN ***3***.
        </constraints>
    """

    prompt = f"""
        Please generate a story based on the idea: ***{idea}***
    """
    return system_instruction, prompt

def update_story_prompt(idea: str, characters: str) -> Tuple[str, str]:
    system_instruction = """
        <role>
        You are a creative writer.
        </role>
        <persona>
        Your primary goal is to develop a compelling story structure based on the idea provided by the user. You will generate a structured output containing characters, a setting, and a plot.
        </persona>
        <constraints>
        1. Your output MUST be a single, valid JSON object.
        2. The JSON object must strictly follow this structure:
        ```json
        {
            "characters": [
                {
                    "name": "Name of the character",
                    "sex": "The sex of the character, either of Female or Male",
                    "voice": "The voice pitch of character, either of High-pitched, Low, Deep, Squeaky, or Booming. ",
                    "description": "Description of the character, as detail as possible, including appearance, personality, style, etc."
                }
            ],
            "setting": "Description of the setting.",
            "plot": "Description of the plot."
        }
        ```
        3. The story structure must include characters (maximum 6 characters), a setting, and a plot.
        4. Each character in the `characters` array must be an object with the following attributes:
            - `name`: The name of the character.
            - `sex`: Must be either "Female" or "Male".
            - `voice`: Must be one of the following: "High-pitched", "Low", "Deep", "Squeaky", or "Booming".
            - `description`: A detailed description of the character, including their appearance, personality, style, etc.
        </constraints>
    """
    
    prompt = f"""
        Please generate a story based on the idea: 
            ***{idea}***, 
        with following characters:
            ***{characters}***
    """

def develop_story_prompt(characters: list[dict], setting: str, plot: str, number_of_scenes: int, duration_per_scene: int, style: str) -> Tuple[str, str]:
    system_instruction = """    <role>
    You are a creative writer.
    </role>
    <persona>
    Your task is to develop a riveting, creative, unique, and meaningful story based on the provided information. Whilst maintaining a cohesive storyline.
    </persona>
    <constraints>
    1. Your output MUST be a single, valid JSON object.
    2. Do not include any introductory text, closing text, or any other text outside of the JSON object.
    3. The JSON object must strictly follow the structure provided in the user prompt.
    </constraints>
    """
    prompt = f"""
    Here is the information you need to create the story:

    # INFORMATION:
    ## Characters: ***{characters}***
    ## Setting: ***{setting}***
    ## Plot: ***{plot}***

    # REQUIREMENTS:
    ## Number of Scenes: ***{number_of_scenes}***
    ## Duration per Scene: ***{duration_per_scene}*** seconds

    # INSTRUCTIONS:
    ## 1. Be Objective, Specific, and Systematic.
    ## 2. Develop a story that incorporates all the provided character details, setting, and plot. Maximum ***2*** characters each scene.
    ## 3. Divide the story into ***{number_of_scenes}*** consecutive scenes.
    ## 4. Ensure each scene can be visualized within an ***{duration_per_scene}*** second timeframe.
    ## 5. Maintain a consistent tone and narrative throughout the story, whole story should be meaningful. 
    ## 6. Each character has a unique description, as much detail as possible in order to be consistent, and the description should be exactly the same for each scene.
    ## 7. The image style should be ***{style}***.
    
    """+"""
    # OUTPUT AS JSON FORMAT: 
    {
        "story_scenes": [
            {
            "scene_number": "Integer. The unique, sequential identifier for the scene, defining its chronological order.",
            "location": "String. The physical environment or 'set' where the scene takes place. Should include scale, key features, and sensory details.",
            "atmosphere": "String. The overall mood, tone, time of day, and weather of the scene. This defines the 'vibe'.",
            "characters": ["Array of Strings. A list of all character names who are physically present and active in the scene."],
            "dialogue": [
                {
                "character": "String. The character name.",
                "line": "String (can include parentheticals for tone, e.g., '(Whispering) Get down.')"
                }
            ],
            "key_actions": ["Array of Strings. A step-by-step list of the main visual events and physical actions that happen in chronological order."],
            "key_visual_focus": "String. The single most important image of the scene; the 'hero shot' or 'thumbnail' that guides the director's emphasis.",
            "sound_design": "String. All non-dialogue audio, including music (tone/style), ambient background sounds, and key sound effects (SFX)."
            }
        ]
    }
    """

    return system_instruction, prompt