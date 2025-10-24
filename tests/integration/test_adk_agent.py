#!/usr/bin/env python
"""
Test script for the ADK-based idea generation agent.

This script demonstrates and tests the new IdeaGenerationAgentADK implementation.
"""

import asyncio
import json
from agents.idea_agent_adk import IdeaGenerationAgentADK
from utils.logger import logger


async def test_adk_agent():
    """Test the ADK-based agent with a sample story idea."""
    print("=" * 80)
    print("Testing ADK-based Story Generation Agent")
    print("=" * 80)

    # Initialize the agent
    agent = IdeaGenerationAgentADK()

    # Test story ideas
    test_cases = [
        {
            "idea": "A young robot discovers emotions while exploring an abandoned garden",
            "style": "Studio Ghibli"
        },
        # Uncomment to test more cases
        # {
        #     "idea": "Time-traveling chef must fix historical food disasters",
        #     "style": "Pixar"
        # }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}")
        print(f"{'=' * 80}")
        print(f"Idea: {test_case['idea']}")
        print(f"Style: {test_case['style']}")
        print()

        try:
            # Generate story
            characters, setting, plot = await agent.generate_story_async(
                idea=test_case['idea'],
                style=test_case['style']
            )

            # Display results
            print("\n" + "=" * 80)
            print("GENERATED STORY")
            print("=" * 80)

            print("\n📋 CHARACTERS:")
            for idx, char in enumerate(characters, 1):
                print(f"\n  {idx}. {char.get('name', 'Unknown')}")
                print(f"     Sex: {char.get('sex', 'N/A')}")
                print(f"     Voice: {char.get('voice', 'N/A')}")
                print(f"     Description: {char.get('description', 'N/A')}")

            print(f"\n🎬 SETTING:")
            print(f"  {setting}")

            print(f"\n📖 PLOT:")
            print(f"  {plot}")

            # Display iteration history
            print("\n" + "=" * 80)
            print("ITERATION HISTORY")
            print("=" * 80)

            history = agent.get_iteration_history()
            for iteration in history:
                if iteration.critique:
                    print(f"\nIteration {iteration.iteration}:")
                    print(f"  Score: {iteration.critique.score}/10")
                    print(f"  Passes threshold: {iteration.critique.passes_threshold}")
                    print(f"  Strengths:")
                    for strength in iteration.critique.strengths:
                        print(f"    + {strength}")
                    print(f"  Weaknesses:")
                    for weakness in iteration.critique.weaknesses:
                        print(f"    - {weakness}")
                    if iteration.critique.suggestions:
                        print(f"  Suggestions:")
                        for suggestion in iteration.critique.suggestions:
                            print(f"    → {suggestion}")

            # Display summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Total iterations: {len(history)}")
            print(f"Best score: {agent.state.best_score}/10")
            print(f"Quality threshold: {agent.state.quality_threshold}")
            print(f"Threshold met: {agent.state.best_score >= agent.state.quality_threshold}")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.error("Test failed", exc_info=True)
            raise

    print("\n" + "=" * 80)
    print("✅ All tests completed successfully!")
    print("=" * 80)


def test_sync_wrapper():
    """Test the synchronous wrapper function."""
    print("\n" + "=" * 80)
    print("Testing Synchronous Wrapper")
    print("=" * 80)

    agent = IdeaGenerationAgentADK()

    idea = "A magical library where books come alive at midnight"
    style = "Disney"

    print(f"Idea: {idea}")
    print(f"Style: {style}")
    print("\nGenerating story (sync mode)...\n")

    characters, setting, plot = agent.generate_story(idea, style)

    print("✅ Synchronous generation completed!")
    print(f"Generated {len(characters)} characters")
    print(f"Setting length: {len(setting)} characters")
    print(f"Plot length: {len(plot)} characters")


if __name__ == "__main__":
    # Test async version
    print("\n🚀 Starting ADK Agent Tests\n")

    asyncio.run(test_adk_agent())

    # Test sync version
    print("\n" + "=" * 80)
    test_sync_wrapper()

    print("\n🎉 All tests passed!\n")
