from typing import Tuple


def generate_story_prompt(idea: str) -> Tuple[str, str]:
    system_instruction = """
    You are a creative writer. Your task is to develop a compelling and short story based on the provided Idea. 
    """
    prompt = f"""
    Idea: {idea}
    
    """ + """
    Output as JSON format: 
    {
        "characters": [
            {
                "name": "Name of the character",
                "description": "Description of the character, as detail as possible, including appearance, personality, style, etc.",
            }
        ],
        "setting": "Description of the setting",
        "plot": "Description of the plot"
    }
    """
    return system_instruction, prompt

def develop_story_prompt(characters: str, setting: str, plot: str, number_of_scenes: int, duration_per_scene: int, style: str) -> Tuple[str, str]:
    system_instruction = """
    You are a creative writer. Your task is to develop a riveting, creative, unique, and meaningful story based on the provided information.Whilst maintaining a cohesive storyline. 
    """
    prompt = f"""
    
    # INFORMATION:
    * Characters: {characters}
    * Setting: {setting}
    * Plot: {plot}

    #REQUIREMENTS:
    * Number of Scenes: {number_of_scenes}
    * Duration per Scene: {duration_per_scene} seconds

    # INSTRUCTIONS:
    * 1. Be Objective, Specific, and Systematic.
    * 2. Develop a story that incorporates all the provided character details, setting, and plot.
    * 3. Divide the story into {number_of_scenes} consecutive scenes.
    * 4. Ensure each scene can be visualized within an {duration_per_scene} second timeframe.
    * 5. Maintain a consistent tone and narrative throughout the story, whole story should be meaningful. 
    * 6. Each character has a unique description, as much detail as possible in order to be consistent, and the description should be exactly the same for each scene.
    * 6. The image style should be {style}.
    
    """ + """
    EXAMPLE: 
    [
        {
            "title": "The Glitch",
            "description": "In Alice's apartment, a chaotic nexus where tangled wires bridged generations of technology – from humming vintage terminals to sleek chrome gadgets – she stumbled upon an anomaly amidst the clutter. A small, unfamiliar metallic device, palm-sized and obsidian-smooth with an unnatural curve, pulsed with a faint, ethereal blue glow amongst discarded circuit boards. As her fingers closed around its cool surface, the glow intensified, and the device flickered to life, showing not just the city outside her grimy window, but startlingly predicting it: a ghostly image of a delivery drone appeared on its screen moments before the actual drone zipped past. A chill mixed with intense curiosity gripped Alice as she held the impossible object, realizing she'd found something far stranger and more potent than any tech she'd ever handled – a tiny, unsettling window into the immediate future.",
            "characters": [
                {
                    "name": "Alice",
                    "description": "A curious woman in her late 20s with slightly messy dark hair, wearing a light blue t-shirt with the text "ASKJUNIOR" visible, living an ordinary life in a slightly worn-down futuristic city."
                }
            ],
            "image_prompt": "Alice, kneels amidst piles of old computer parts and sleek holographic displays in her cluttered apartment. She holds a small, glowing metallic device. Outside the window, a dense futuristic cityscape with neon signs and flying vehicles is visible under a hazy twilight sky. Style: Studio Ghibli.",
            "scripts": [
                {
                    "character": "Alice",
                    "gender": "female",
                    "dialogue": "I'm not sure what this is, but it's not just a tech anomaly. It's something else.",
                    "time": "2"
                }
            ]
        }
    ]
    # OUTPUT AS JSON FORMAT: 
    [
       
        {
            "title": "Title of each scene", 
            "description": "Description of each scene, as much detail as possible", 
            "characters": [{
                "name": "Name of the character",
                "description": "Description of the character, as much as possible in order to be consistent, include appearance(hair, face, eyes, clothes, etc.), personality, style, etc.",
            }]
            "image_prompt": "Prompt to generate the first image for each scene, include subjects (characters, objects, animals, scenery etc), the background or context in which the subject will be placed, and the image style. Do not include any description of the character, just name of the character.", 
            "scripts": [
                {
                    "character": "Name of the character",
                    "gender": "Gender of the character",
                    "dialogue": "Dialogue of the character",
                    "time": "Time of the dialogue beginning, unit: seconds, e.g. 2 - start from 2 seconds"
                }
            ]
        }
    ]
    
    """

    return system_instruction, prompt