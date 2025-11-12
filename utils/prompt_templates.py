from typing import Tuple
from .llm import load_prompt


def generate_story_prompt(idea: str) -> Tuple[str, str]:
    system_instruction = load_prompt("story_development/generate_story.md")

    prompt_template = load_prompt("story_development/generate_story_user.md")
    prompt = prompt_template.format(idea=idea)
    return system_instruction, prompt

def update_story_prompt(idea: str, characters: str) -> Tuple[str, str]:
    system_instruction = load_prompt("story_development/update_story.md")
    
    prompt_template = load_prompt("story_development/update_story_user.md")
    prompt = prompt_template.format(idea=idea, characters=characters)

def develop_story_prompt(characters: list[dict], setting: str, plot: str, number_of_scenes: int, duration_per_scene: int, style: str) -> Tuple[str, str]:
    system_instruction = load_prompt("story_development/develop_story.md")
    prompt_template = load_prompt("story_development/develop_story_user.md")
    prompt = prompt_template.format(
        characters=characters,
        setting=setting,
        plot=plot,
        number_of_scenes=number_of_scenes,
        duration_per_scene=duration_per_scene,
        style=style
    )

    return system_instruction, prompt