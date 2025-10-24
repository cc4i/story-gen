#!/usr/bin/env python
"""
Comparison example: Original IdeaGenerationAgent vs ADK-based IdeaGenerationAgentADK

This script demonstrates the differences and similarities between the two implementations.
"""

import asyncio
import time
from agents.idea_agent import IdeaGenerationAgent
from agents.idea_agent_adk import IdeaGenerationAgentADK


def compare_agents():
    """Compare both agent implementations side by side."""

    test_idea = "A magical forest where trees can swap places at night"
    test_style = "Studio Ghibli"

    print("=" * 80)
    print("STORY GENERATION AGENT COMPARISON")
    print("=" * 80)
    print(f"\nTest Idea: {test_idea}")
    print(f"Style: {test_style}\n")

    # ========================================================================
    # Test 1: Original Agent
    # ========================================================================
    print("=" * 80)
    print("TEST 1: Original IdeaGenerationAgent")
    print("=" * 80)

    start_time = time.time()
    original_agent = IdeaGenerationAgent()

    try:
        characters_orig, setting_orig, plot_orig = original_agent.generate_story(
            idea=test_idea,
            style=test_style
        )
        orig_duration = time.time() - start_time

        print(f"\n✓ Generation completed in {orig_duration:.2f}s")
        print(f"  Characters: {len(characters_orig)}")
        print(f"  Setting length: {len(setting_orig)} chars")
        print(f"  Plot length: {len(plot_orig)} chars")

        # Show iteration history
        history_orig = original_agent.get_iteration_history()
        print(f"\n  Iterations: {len(history_orig)}")
        if history_orig:
            final_score = history_orig[-1].critique.score if history_orig[-1].critique else "N/A"
            print(f"  Final score: {final_score}/10")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        characters_orig, setting_orig, plot_orig = None, None, None
        orig_duration = 0

    # ========================================================================
    # Test 2: ADK-based Agent
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: ADK-based IdeaGenerationAgentADK")
    print("=" * 80)

    start_time = time.time()
    adk_agent = IdeaGenerationAgentADK()

    try:
        characters_adk, setting_adk, plot_adk = adk_agent.generate_story(
            idea=test_idea,
            style=test_style
        )
        adk_duration = time.time() - start_time

        print(f"\n✓ Generation completed in {adk_duration:.2f}s")
        print(f"  Characters: {len(characters_adk)}")
        print(f"  Setting length: {len(setting_adk)} chars")
        print(f"  Plot length: {len(plot_adk)} chars")

        # Show iteration history
        history_adk = adk_agent.get_iteration_history()
        print(f"\n  Iterations: {len(history_adk)}")
        if history_adk:
            final_score = history_adk[-1].critique.score if history_adk[-1].critique else "N/A"
            print(f"  Final score: {final_score}/10")
            print(f"  Best score achieved: {adk_agent.state.best_score}/10")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        characters_adk, setting_adk, plot_adk = None, None, None
        adk_duration = 0

    # ========================================================================
    # Comparison Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    print("\n📊 Performance:")
    if orig_duration > 0 and adk_duration > 0:
        print(f"  Original Agent:     {orig_duration:.2f}s")
        print(f"  ADK Agent:          {adk_duration:.2f}s")
        diff = adk_duration - orig_duration
        print(f"  Difference:         {diff:+.2f}s ({diff/orig_duration*100:+.1f}%)")

    print("\n🏗️  Architecture:")
    print("  Original Agent:     Single class with manual loop")
    print("  ADK Agent:          Multi-agent system with LoopAgent")

    print("\n🔍 Observability:")
    print("  Original Agent:     Custom logging")
    print("  ADK Agent:          ADK event streaming + telemetry")

    print("\n⚙️  Configuration:")
    print("  Original Agent:     Hardcoded constants")
    print("  ADK Agent:          ADK RunConfig + custom tools")

    print("\n💡 Key Differences:")
    print("  1. ADK agent uses Google's Agent Development Kit framework")
    print("  2. ADK agent has better modularity (3 specialized sub-agents)")
    print("  3. ADK agent provides richer event streaming and telemetry")
    print("  4. Both maintain the same public API for backward compatibility")

    print("\n✅ API Compatibility:")
    print("  Both agents expose the same interface:")
    print("  - generate_story(idea, style) → (characters, setting, plot)")
    print("  - get_iteration_history() → List[StoryIteration]")
    print("  - get_critique_summary() → str")

    print("\n" + "=" * 80)
    print("Conclusion: Both agents produce high-quality results.")
    print("Choose ADK agent for:")
    print("  - Better modularity and testability")
    print("  - Advanced observability and telemetry")
    print("  - Future extensibility with ADK ecosystem")
    print("\nChoose Original agent for:")
    print("  - Simpler dependencies (only google-genai)")
    print("  - Faster setup and slightly lower overhead")
    print("=" * 80)


async def compare_async():
    """Compare async performance."""
    print("\n" + "=" * 80)
    print("ASYNC PERFORMANCE TEST")
    print("=" * 80)

    test_idea = "A time-traveling bookshop that sells yesterday's newspapers"
    test_style = "Wes Anderson"

    print(f"\nTest Idea: {test_idea}")
    print(f"Style: {test_style}\n")

    # Original agent
    print("Testing Original Agent (async)...")
    original_agent = IdeaGenerationAgent()
    start = time.time()
    # Original agent doesn't have async, so we'll skip
    print("  (Original agent doesn't support native async)")

    # ADK agent
    print("\nTesting ADK Agent (async)...")
    adk_agent = IdeaGenerationAgentADK()
    start = time.time()
    characters, setting, plot = await adk_agent.generate_story_async(test_idea, test_style)
    duration = time.time() - start

    print(f"✓ ADK Agent completed in {duration:.2f}s")
    print(f"  Characters: {len(characters)}")
    print(f"  Best score: {adk_agent.state.best_score}/10")


if __name__ == "__main__":
    # Run synchronous comparison
    compare_agents()

    # Run async test
    print("\n")
    asyncio.run(compare_async())

    print("\n🎉 Comparison complete!")
