import json

def save_characters(characters):
    with open("tmp/images/characters/characters.txt", "w") as f:
        f.write(characters)

def save_setting(setting):
    with open("tmp/images/default/setting.txt", "w") as f:
        f.write(setting)

def save_plot(plot):
    with open("tmp/images/default/plot.txt", "w") as f:
        f.write(plot)

def save_prompt(scene_num, prompt):
    with open(f"tmp/images/default/scene_prompt_{scene_num}.txt", "w") as f:
        f.write(prompt)

def save_script(scene_num, script):
    with open(f"tmp/images/default/scene_script_{scene_num}.json", "w") as f:
        f.write(json.dumps(json.loads(script), indent=4))