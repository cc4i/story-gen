from utils.llm import call_llm

def generate_random_idea():
    system_instruction=""
    prompt="""
        Generate a random, specific concise story idea, less than three sentences and without any explanation. The idea must be fit for all ages.
    """
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    return string_response