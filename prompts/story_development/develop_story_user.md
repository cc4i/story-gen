
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
## 2. Develop a story that incorporates all the provided character details, setting, and plot. Maximum ***2*** characters each scene, characters must choose from provided character list.
## 3. Divide the story into ***{number_of_scenes}*** consecutive scenes.
## 4. Ensure each scene can be visualized within an ***{duration_per_scene}*** second timeframe.
## 5. Maintain a consistent tone and narrative throughout the story, whole story should be meaningful. 
## 6. Each character has a unique description, as much detail as possible in order to be consistent, and the description should be exactly the same for each scene.
## 7. The image/video style should be ***{style}***.
## 8. Make sure Continuity between scenes and the whole things together from begin to end are smoothly. 


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
        "sound_design": "String. All non-dialogue audio, including music (tone/style), ambient background sounds, and key sound effects (SFX).",
        "style": "String. The image/video style."
        }
    ]
}
