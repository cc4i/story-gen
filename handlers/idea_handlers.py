from utils.llm import call_llm
from utils.config import IDEA_TXT
from models.config import DEFAULT_MODEL_ID
import os

def generate_random_idea():
    system_instruction=""
    prompt="""
        Generate a random, specific concise story idea, less than three sentences and without any explanation. The idea must be fit for all ages.
    """
    history = ""
    string_response = call_llm(system_instruction, prompt, history, DEFAULT_MODEL_ID)

    # Save the latest idea to idea.txt (overwrites previous)
    with open(IDEA_TXT, "w") as f:
        f.write(string_response)

    return string_response

def load_idea():
    """Load the latest idea from idea.txt if it exists"""
    if os.path.exists(IDEA_TXT):
        with open(IDEA_TXT, "r") as f:
            return f.read()
    return ""