"""
Simple test script for the IdeaGenerationAgent.

This script tests the agent-based story generation without running the full Gradio app.
"""

import os
from dotenv import load_dotenv
from agents import IdeaGenerationAgent
from utils.logger import logger

# Load environment variables
load_dotenv()

def test_agent():
    """Test the IdeaGenerationAgent with a sample story idea."""

    print("\n" + "="*80)
    print("Testing IdeaGenerationAgent - Self-Critique Story Generation")
    print("="*80 + "\n")

    # Sample idea
    idea = """
    A young girl discovers she can talk to plants, and they tell her about
    an ancient tree in the forest that is dying. She embarks on a journey
    to save it and discovers a magical world beneath the roots.
    """

    style = "Studio Ghibli"

    print(f"📝 Idea: {idea.strip()}")
    print(f"🎨 Style: {style}\n")

    try:
        # Initialize agent
        agent = IdeaGenerationAgent()

        # Generate story with self-critique
        print("🤖 Agent starting story generation...\n")
        characters, setting, plot = agent.generate_story(idea, style)

        # Display results
        print("\n" + "="*80)
        print("✅ FINAL STORY STRUCTURE")
        print("="*80 + "\n")

        print("👥 CHARACTERS:")
        for i, char in enumerate(characters, 1):
            print(f"\n  {i}. {char['name']} ({char['sex']})")
            print(f"     Voice: {char['voice']}")
            print(f"     Description: {char['description'][:100]}...")

        print(f"\n\n🌍 SETTING:")
        print(f"  {setting[:200]}...")

        print(f"\n\n📖 PLOT:")
        print(f"  {plot[:200]}...")

        # Display iteration history
        print("\n\n" + "="*80)
        print("📊 ITERATION HISTORY")
        print("="*80 + "\n")

        print(agent.get_critique_summary())

        print("\n" + "="*80)
        print("✅ Test completed successfully!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Test failed", exc_info=True)
        raise

if __name__ == "__main__":
    test_agent()
