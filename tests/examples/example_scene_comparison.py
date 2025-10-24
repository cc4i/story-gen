"""
Scene Development Comparison Script

This script compares the original single-shot scene development approach
with the new ADK-based multi-agent system.

Run with: python example_scene_comparison.py
"""

import json
import time
from typing import Dict, List

from agents.scene_development_agent_adk import SceneDevelopmentAgentADK
from handlers.story_handlers import developing_story
from models.config import DEFAULT_MODEL_ID
from utils.logger import logger


# ============================================================================
# Sample Story Data
# ============================================================================

SAMPLE_CHARACTERS = [
    {
        "name": "Luna",
        "sex": "Female",
        "voice": "Soft, melodic",
        "description": "A young astronomer with wild curly hair and round glasses, wearing a constellation-patterned jacket. Her eyes light up when she talks about stars.",
        "style": "Studio Ghibli"
    },
    {
        "name": "Comet",
        "sex": "N/A",
        "voice": "Ethereal, whisper-like",
        "description": "A small glowing creature made of stardust, resembling a cross between a fox and a shooting star. Leaves sparkles wherever it goes.",
        "style": "Studio Ghibli"
    }
]

SAMPLE_SETTING = """
A magical observatory perched on a floating mountain above the clouds. The observatory
is made of crystalline glass and ancient wood, with telescopes of various sizes pointing
at the night sky. The surrounding gardens are filled with celestial flowers that bloom
only at night, their petals reflecting starlight. Pathways wind through the clouds,
and the aurora borealis dances overhead.
"""

SAMPLE_PLOT = """
Luna, a young astronomer, discovers Comet, a lost celestial creature, hiding in her
observatory. Comet has fallen from the stars and can't find its way home. Together,
they embark on a journey through the night sky, visiting different constellations
and meeting other star creatures. Luna uses her knowledge of astronomy to help Comet
navigate back to its celestial family, while Comet teaches Luna about the magic and
wonder hidden in the stars she's studied all her life. Their friendship bridges the
gap between science and magic.
"""


# ============================================================================
# Comparison Functions
# ============================================================================

def print_header(text: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width + "\n")


def print_scene_summary(scene: Dict, index: int):
    """Print a formatted scene summary."""
    print(f"\n{'─' * 80}")
    print(f"📍 Scene {index}: {scene.get('scene_number', index)}")
    print(f"{'─' * 80}")

    print(f"\n🏞️  Location:")
    print(f"   {scene.get('location', 'N/A')[:200]}...")

    print(f"\n🌅 Atmosphere:")
    print(f"   {scene.get('atmosphere', 'N/A')[:200]}...")

    print(f"\n👥 Characters:")
    characters = scene.get('characters', [])
    char_names = [c if isinstance(c, str) else c.get('name', 'Unknown') for c in characters]
    print(f"   {', '.join(char_names)}")

    print(f"\n🎬 Key Actions:")
    for i, action in enumerate(scene.get('key_actions', [])[:3], 1):
        print(f"   {i}. {action[:150]}...")

    print(f"\n🎯 Key Visual Focus:")
    print(f"   {scene.get('key_visual_focus', 'N/A')[:200]}...")

    if scene.get('dialogue'):
        print(f"\n💬 Dialogue:")
        for line in scene.get('dialogue', [])[:2]:
            char = line.get('character', 'Unknown')
            text = line.get('line', '')
            print(f"   {char}: \"{text[:100]}...\"")


def compare_scene_quality(original_scenes: List[Dict], adk_scenes: List[Dict]):
    """Compare quality metrics between original and ADK scenes."""
    print_header("Quality Comparison")

    # Scene count
    print(f"📊 Scene Count:")
    print(f"   Original: {len(original_scenes)} scenes")
    print(f"   ADK:      {len(adk_scenes)} scenes")

    # Visual detail comparison
    original_loc_avg = sum(len(s.get('location', '')) for s in original_scenes) / len(original_scenes)
    adk_loc_avg = sum(len(s.get('location', '')) for s in adk_scenes) / len(adk_scenes)

    print(f"\n📝 Average Location Description Length:")
    print(f"   Original: {original_loc_avg:.0f} characters")
    print(f"   ADK:      {adk_loc_avg:.0f} characters")
    print(f"   Improvement: {((adk_loc_avg / original_loc_avg - 1) * 100):.1f}%")

    # Action complexity
    original_actions_avg = sum(len(s.get('key_actions', [])) for s in original_scenes) / len(original_scenes)
    adk_actions_avg = sum(len(s.get('key_actions', [])) for s in adk_scenes) / len(adk_scenes)

    print(f"\n🎬 Average Number of Key Actions per Scene:")
    print(f"   Original: {original_actions_avg:.1f} actions")
    print(f"   ADK:      {adk_actions_avg:.1f} actions")

    # Dialogue richness
    original_dialogue = sum(len(s.get('dialogue', [])) for s in original_scenes)
    adk_dialogue = sum(len(s.get('dialogue', [])) for s in adk_scenes)

    print(f"\n💬 Total Dialogue Lines:")
    print(f"   Original: {original_dialogue} lines")
    print(f"   ADK:      {adk_dialogue} lines")


def run_original_approach() -> List[Dict]:
    """Run original single-shot scene development."""
    print_header("Running Original Single-Shot Approach")

    print("⏱️  Starting generation...")
    start_time = time.time()

    # Prepare arguments for developing_story
    args = []

    # Number of characters
    args.append(len(SAMPLE_CHARACTERS))

    # Character images (6 placeholders)
    args.extend([None] * 6)

    # Character names (6)
    for i in range(6):
        args.append(SAMPLE_CHARACTERS[i]['name'] if i < len(SAMPLE_CHARACTERS) else '')

    # Character sexes (6)
    for i in range(6):
        args.append(SAMPLE_CHARACTERS[i]['sex'] if i < len(SAMPLE_CHARACTERS) else 'N/A')

    # Character voices (6)
    for i in range(6):
        args.append(SAMPLE_CHARACTERS[i]['voice'] if i < len(SAMPLE_CHARACTERS) else '')

    # Character descriptions (6)
    for i in range(6):
        args.append(SAMPLE_CHARACTERS[i]['description'] if i < len(SAMPLE_CHARACTERS) else '')

    # Setting, plot, scenes, duration, model, style
    args.extend([
        SAMPLE_SETTING,
        SAMPLE_PLOT,
        6,  # number_of_scenes
        6,  # duration_per_scene
        DEFAULT_MODEL_ID,
        "Studio Ghibli",
        False  # use_scene_adk = False for original approach
    ])

    # Run original approach
    result_json = developing_story(*args)
    result = json.loads(result_json)

    duration = time.time() - start_time

    print(f"✅ Original approach completed in {duration:.1f}s")

    scenes = result.get('story_scenes', [])
    print(f"📊 Generated {len(scenes)} scenes")

    return scenes


def run_adk_approach() -> tuple[List[Dict], SceneDevelopmentAgentADK]:
    """Run ADK-based multi-agent scene development."""
    print_header("Running ADK Multi-Agent Approach")

    print("⏱️  Starting generation (this may take 2-3 minutes)...")
    start_time = time.time()

    # Create agent
    agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)

    # Generate scenes
    scenes = agent.develop_scenes(
        characters=SAMPLE_CHARACTERS,
        setting=SAMPLE_SETTING,
        plot=SAMPLE_PLOT,
        number_of_scenes=6,
        duration_per_scene=6,
        style="Studio Ghibli"
    )

    duration = time.time() - start_time

    print(f"✅ ADK approach completed in {duration:.1f}s")
    print(f"📊 Generated {len(scenes)} scenes")
    print(f"⭐ Best quality score: {agent.state.best_score:.1f}/10")
    print(f"🔄 Total iterations: {len(agent.get_iteration_history())}")

    return scenes, agent


def show_adk_insights(agent: SceneDevelopmentAgentADK):
    """Show detailed ADK agent insights."""
    print_header("ADK Agent Insights")

    print("📈 Iteration History:\n")
    for iteration in agent.get_iteration_history():
        print(f"Iteration {iteration.iteration}:")

        if iteration.validation:
            print(f"  Validation Scores:")
            print(f"    Visual:     {iteration.validation.visual_score:.1f}/10")
            print(f"    Narrative:  {iteration.validation.narrative_score:.1f}/10")
            print(f"    Technical:  {iteration.validation.technical_score:.1f}/10")
            print(f"    Combined:   {iteration.validation.combined_score:.1f}/10")

        if iteration.critique:
            print(f"  Critique:")
            print(f"    Overall Score: {iteration.critique.overall_score:.1f}/10")
            print(f"    Decision:      {iteration.critique.decision}")

            if iteration.critique.strengths:
                print(f"    Top Strengths:")
                for strength in iteration.critique.strengths[:2]:
                    print(f"      ✓ {strength}")

            if iteration.critique.weaknesses:
                print(f"    Key Weaknesses:")
                for weakness in iteration.critique.weaknesses[:2]:
                    print(f"      ✗ {weakness}")

        print()

    # Print critique summary
    print("\n" + agent.get_critique_summary())


def side_by_side_comparison(original_scene: Dict, adk_scene: Dict, scene_num: int):
    """Show side-by-side comparison of a single scene."""
    print_header(f"Scene {scene_num}: Side-by-Side Comparison")

    print("🔵 ORIGINAL (Single-Shot)\n")
    print_scene_summary(original_scene, scene_num)

    print("\n\n🟢 ADK (Multi-Agent)\n")
    print_scene_summary(adk_scene, scene_num)

    print("\n" + "=" * 80)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run the comparison."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     Scene Development Comparison: Original vs ADK Agent        ║
║                                                                ║
║  This script demonstrates the quality improvement when using   ║
║  the ADK-based multi-agent scene development system versus     ║
║  the original single-shot LLM approach.                        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    print("\n📖 Story Summary:")
    print(f"   Title: Luna and the Stardust Creature")
    print(f"   Characters: {len(SAMPLE_CHARACTERS)}")
    print(f"   Scenes: 6 (6 seconds each)")
    print(f"   Style: Studio Ghibli")

    # Run original approach
    try:
        original_scenes = run_original_approach()
    except Exception as e:
        logger.error(f"Original approach failed: {str(e)}", exc_info=True)
        print(f"\n❌ Original approach failed: {str(e)}")
        print("Continuing with ADK approach only...\n")
        original_scenes = []

    # Run ADK approach
    try:
        adk_scenes, agent = run_adk_approach()
    except Exception as e:
        logger.error(f"ADK approach failed: {str(e)}", exc_info=True)
        print(f"\n❌ ADK approach failed: {str(e)}")
        return

    # Show ADK insights
    show_adk_insights(agent)

    # Compare quality
    if original_scenes:
        compare_scene_quality(original_scenes, adk_scenes)

        # Side-by-side comparison for first 3 scenes
        print_header("Detailed Scene Comparisons")
        for i in range(min(3, len(original_scenes), len(adk_scenes))):
            side_by_side_comparison(original_scenes[i], adk_scenes[i], i + 1)
    else:
        print("\n⚠️  Skipping comparison (original approach not available)")

    # Final summary
    print_header("Summary")

    if original_scenes:
        print("✅ Both approaches completed successfully")
        print(f"\n📊 Results:")
        print(f"   Original: {len(original_scenes)} scenes, ~30s generation time")
        print(f"   ADK:      {len(adk_scenes)} scenes, ~2-3min generation time")
        print(f"   ADK Quality Score: {agent.state.best_score:.1f}/10")
        print(f"\n💡 Recommendation: Use ADK for production, original for quick prototypes")
    else:
        print("✅ ADK approach completed successfully")
        print(f"\n📊 Results:")
        print(f"   ADK: {len(adk_scenes)} scenes")
        print(f"   Quality Score: {agent.state.best_score:.1f}/10")
        print(f"   Iterations: {len(agent.get_iteration_history())}")

    print("\n" + "=" * 80)
    print("🎉 Comparison complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
