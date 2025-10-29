import json
from utils.config import (
    CHARACTERS_JSON,
    SETTING_TXT,
    PLOT_TXT,
    STORY_JSON,
)

def save_characters(characters):
    with open(CHARACTERS_JSON, "w") as f:
        if isinstance(characters, str):
            char_list = []
            for line in characters.split('\n'):
                if line.strip():
                    name, desc = line.split(':', 1)
                    char_list.append({"name": name.strip(), "description": desc.strip()})
            json.dump(char_list, f, indent=4)
        else:
            json.dump(characters, f, indent=4)

def save_setting(setting):
    with open(SETTING_TXT, "w") as f:
        f.write(setting)

def save_plot(plot):
    with open(PLOT_TXT, "w") as f:
        f.write(plot)

def save_story(story_json):
    with open(STORY_JSON, "w") as f:
        f.write(json.dumps(story_json, indent=4))

def save_prompt(scene_num, prompt):
    with open(f"tmp/images/default/scene_prompt_{scene_num}.txt", "w") as f:
        f.write(prompt)

def save_script(scene_num, script):
    with open(f"tmp/images/default/scene_script_{scene_num}.json", "w") as f:
        f.write(json.dumps(json.loads(script), indent=4))