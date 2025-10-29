"""
Test script for SceneDevelopmentAgentADK.

This script tests the ADK-based scene development agent with sample story data.
Run with: python test_scene_development_adk.py
"""

import asyncio
import json
import time
from typing import Dict, List

from agents.scene_development_agent_adk import SceneDevelopmentAgentADK
from models.config import DEFAULT_MODEL_ID
from utils.logger import logger


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_CHARACTERS = [
    {
        "name": "Robot 734",
        "description": "A weathered maintenance robot with glowing blue optical sensors, rusty joints, and a dented chassis covered in moss. Despite its worn appearance, its movements are gentle and curious.",
        "personality": "Initially mechanical and task-focused, gradually awakening to wonder and emotion as it explores the garden.",
        "role": "Protagonist - discovers beauty and emotion",
        "visual_details": "Humanoid shape, approximately 5 feet tall, cylindrical head with two large blue sensor 'eyes', articulated arms with delicate manipulators"
    },
    {
        "name": "Lumina",
        "description": "A tiny bioluminescent sprite with translucent wings that shimmer with rainbow colors. She glows with a soft golden light and leaves trails of sparkles when she moves.",
        "personality": "Playful, wise, and gentle. She acts as a guide to the robot, teaching it about beauty and feeling.",
        "role": "Guide - helps the robot understand emotions",
        "visual_details": "6 inches tall, ethereal appearance, flowing dress made of petals, constantly glowing and leaving light trails"
    }
]

SAMPLE_SETTING = """
An abandoned botanical garden reclaimed by nature, where bioluminescent plants have taken over.
The garden is a maze of overgrown pathways, crumbling stone walls covered in glowing vines, and
ponds filled with luminous water lilies. Ancient statues are scattered throughout, half-hidden by
moss and flowers. The atmosphere is magical, with soft light filtering through the canopy and
bioluminescent particles floating in the air like fireflies. Time of day transitions from dawn
to dusk, showing different aspects of the garden's beauty.
"""

SAMPLE_PLOT = """
Robot 734 awakens in the abandoned garden after years of dormancy. Its original purpose was
maintenance, but the garden has transformed into something it doesn't recognize. As it explores,
it encounters Lumina, a bioluminescent sprite who has made the garden her home. Through Lumina's
guidance and the beauty of the garden, Robot 734 begins to experience emotions for the first time:
wonder at the glowing plants, curiosity about the transformation, joy in Lumina's playful presence,
and ultimately, a sense of belonging. The story is a gentle journey of awakening and discovering
that beauty and emotion can emerge even in the most unexpected places.
"""


# ============================================================================
# Test Functions
# ============================================================================

def print_separator(title: str = ""):
    """Print a section separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def print_scene_summary(scenes: List[Dict]):
    """Print a summary of generated scenes."""
    print(f"\n📊 Generated {len(scenes)} scenes:\n")
    for scene in scenes:
        print(f"Scene {scene.get('scene_number', '?')}:")
        print(f"  Location: {scene.get('location', 'N/A')[:80]}...")
        print(f"  Atmosphere: {scene.get('atmosphere', 'N/A')[:80]}...")
        print(f"  Characters: {', '.join(scene.get('characters', []))}")
        print(f"  Key Visual: {scene.get('key_visual_focus', 'N/A')[:80]}...")
        print()


def print_iteration_history(agent: SceneDevelopmentAgentADK):
    """Print iteration history."""
    history = agent.get_iteration_history()

    print(f"\n📈 Iteration History ({len(history)} iterations):\n")
    for iteration in history:
        print(f"Iteration {iteration.iteration}:")

        if iteration.validation:
            print(f"  Validation Scores:")
            print(f"    Visual: {iteration.validation.visual_score:.1f}/10")
            print(f"    Narrative: {iteration.validation.narrative_score:.1f}/10")
            print(f"    Technical: {iteration.validation.technical_score:.1f}/10")
            print(f"    Combined: {iteration.validation.combined_score:.1f}/10")

        if iteration.critique:
            print(f"  Critique:")
            print(f"    Overall Score: {iteration.critique.overall_score:.1f}/10")
            print(f"    Decision: {iteration.critique.decision}")
            if iteration.critique.strengths:
                print(f"    Strengths: {', '.join(iteration.critique.strengths[:2])}")
            if iteration.critique.weaknesses:
                print(f"    Weaknesses: {', '.join(iteration.critique.weaknesses[:2])}")

        print()


def test_sync_scene_development():
    """Test synchronous scene development."""
    print_separator("TEST 1: Synchronous Scene Development")

    try:
        # Create agent
        print("Creating SceneDevelopmentAgentADK...")
        agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)
        print("✅ Agent created successfully\n")

        # Generate scenes
        print("Generating scenes (this may take 2-3 minutes)...\n")
        start_time = time.time()

        scenes = agent.develop_scenes(
            characters=SAMPLE_CHARACTERS,
            setting=SAMPLE_SETTING,
            plot=SAMPLE_PLOT,
            number_of_scenes=6,
            duration_per_scene=6,
            style="Studio Ghibli"
        )

        duration = time.time() - start_time

        # Print results
        print(f"✅ Scene development completed in {duration:.1f}s")
        print_scene_summary(scenes)
        print_iteration_history(agent)

        # Print summary
        print(agent.get_critique_summary())

        # Validate output
        assert len(scenes) == 6, f"Expected 6 scenes, got {len(scenes)}"
        assert all('scene_number' in s for s in scenes), "Missing scene_number in scenes"
        assert all('location' in s for s in scenes), "Missing location in scenes"
        assert all('key_visual_focus' in s for s in scenes), "Missing key_visual_focus in scenes"

        print("\n✅ All validation checks passed!")

        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        print(f"\n❌ Test failed: {str(e)}")
        return False


async def test_async_scene_development():
    """Test asynchronous scene development."""
    print_separator("TEST 2: Asynchronous Scene Development")

    try:
        # Create agent
        print("Creating SceneDevelopmentAgentADK...")
        agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)
        print("✅ Agent created successfully\n")

        # Generate scenes
        print("Generating scenes asynchronously (this may take 2-3 minutes)...\n")
        start_time = time.time()

        scenes = await agent.develop_scenes_async(
            characters=SAMPLE_CHARACTERS,
            setting=SAMPLE_SETTING,
            plot=SAMPLE_PLOT,
            number_of_scenes=6,
            duration_per_scene=6,
            style="Studio Ghibli"
        )

        duration = time.time() - start_time

        # Print results
        print(f"✅ Async scene development completed in {duration:.1f}s")
        print_scene_summary(scenes)
        print_iteration_history(agent)

        # Validate output
        assert len(scenes) == 6, f"Expected 6 scenes, got {len(scenes)}"

        print("\n✅ Async test passed!")

        return True

    except Exception as e:
        logger.error(f"Async test failed: {str(e)}", exc_info=True)
        print(f"\n❌ Async test failed: {str(e)}")
        return False


def test_different_scene_counts():
    """Test with different scene counts."""
    print_separator("TEST 3: Different Scene Counts")

    test_cases = [
        {"scenes": 3, "duration": 8, "style": "Pixar"},
        {"scenes": 9, "duration": 5, "style": "Studio Ghibli"},
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['scenes']} scenes, {case['duration']}s each, {case['style']} style")
        print("-" * 80)

        try:
            agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)

            start_time = time.time()
            scenes = agent.develop_scenes(
                characters=SAMPLE_CHARACTERS[:1],  # Use just one character for speed
                setting=SAMPLE_SETTING,
                plot=SAMPLE_PLOT,
                number_of_scenes=case['scenes'],
                duration_per_scene=case['duration'],
                style=case['style']
            )
            duration = time.time() - start_time

            print(f"✅ Generated {len(scenes)} scenes in {duration:.1f}s")

            # Print quality scores
            history = agent.get_iteration_history()
            if history:
                last_iteration = history[-1]
                if last_iteration.critique:
                    print(f"   Final Score: {last_iteration.critique.overall_score:.1f}/10")
                    print(f"   Decision: {last_iteration.critique.decision}")

            assert len(scenes) == case['scenes'], f"Expected {case['scenes']} scenes, got {len(scenes)}"

        except Exception as e:
            logger.error(f"Test case {i} failed: {str(e)}", exc_info=True)
            print(f"❌ Test case {i} failed: {str(e)}")
            return False

    print("\n✅ All scene count tests passed!")
    return True


def test_quality_metrics():
    """Test quality metrics and iteration tracking."""
    print_separator("TEST 4: Quality Metrics and Iteration Tracking")

    try:
        print("Creating agent and generating scenes...")
        agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)

        scenes = agent.develop_scenes(
            characters=SAMPLE_CHARACTERS,
            setting=SAMPLE_SETTING,
            plot=SAMPLE_PLOT,
            number_of_scenes=6,
            duration_per_scene=6,
            style="Studio Ghibli"
        )

        # Check iteration history
        history = agent.get_iteration_history()
        print(f"\n✅ Completed {len(history)} iterations")

        # Verify each iteration has required data
        for iteration in history:
            assert iteration.scenes is not None, f"Iteration {iteration.iteration} missing scenes"
            assert iteration.critique is not None, f"Iteration {iteration.iteration} missing critique"
            assert iteration.validation is not None, f"Iteration {iteration.iteration} missing validation"

            print(f"\nIteration {iteration.iteration}:")
            print(f"  Validation Combined Score: {iteration.validation.combined_score:.1f}/10")
            print(f"  Critique Overall Score: {iteration.critique.overall_score:.1f}/10")
            print(f"  Decision: {iteration.critique.decision}")

        # Check best score tracking
        print(f"\n📊 Quality Metrics:")
        print(f"  Best Score: {agent.state.best_score:.1f}/10")
        print(f"  Quality Threshold: {agent.state.quality_threshold:.1f}/10")
        print(f"  Total Iterations: {len(history)}")

        # Verify quality threshold
        assert agent.state.best_score >= 0, "Invalid best score"
        assert len(history) <= agent.MAX_ITERATIONS, f"Exceeded max iterations: {len(history)} > {agent.MAX_ITERATIONS}"

        print("\n✅ Quality metrics test passed!")
        return True

    except Exception as e:
        logger.error(f"Quality metrics test failed: {str(e)}", exc_info=True)
        print(f"\n❌ Quality metrics test failed: {str(e)}")
        return False


def test_scene_structure():
    """Test that generated scenes have all required fields."""
    print_separator("TEST 5: Scene Structure Validation")

    required_fields = [
        'scene_number',
        'location',
        'atmosphere',
        'characters',
        'dialogue',
        'key_actions',
        'key_visual_focus',
        'sound_design',
        'style'
    ]

    try:
        print("Generating scenes for structure validation...")
        agent = SceneDevelopmentAgentADK(model_id=DEFAULT_MODEL_ID)

        scenes = agent.develop_scenes(
            characters=SAMPLE_CHARACTERS,
            setting=SAMPLE_SETTING,
            plot=SAMPLE_PLOT,
            number_of_scenes=4,  # Smaller count for faster testing
            duration_per_scene=6,
            style="Studio Ghibli"
        )

        print(f"\n✅ Generated {len(scenes)} scenes")
        print("\nValidating scene structure...")

        # Check each scene
        for scene in scenes:
            scene_num = scene.get('scene_number', '?')
            print(f"\nScene {scene_num}:")

            for field in required_fields:
                if field not in scene:
                    print(f"  ❌ Missing field: {field}")
                    raise AssertionError(f"Scene {scene_num} missing required field: {field}")
                else:
                    value = scene[field]
                    if field == 'characters':
                        print(f"  ✓ {field}: {len(value)} character(s)")
                    elif field == 'dialogue':
                        print(f"  ✓ {field}: {len(value)} line(s)")
                    elif field == 'key_actions':
                        print(f"  ✓ {field}: {len(value)} action(s)")
                    elif isinstance(value, str):
                        print(f"  ✓ {field}: {len(value)} chars")

        print("\n✅ All scenes have required structure!")
        return True

    except Exception as e:
        logger.error(f"Structure validation failed: {str(e)}", exc_info=True)
        print(f"\n❌ Structure validation failed: {str(e)}")
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests."""
    print_separator("Scene Development Agent ADK - Test Suite")
    print("Testing the 5-agent, two-phase scene development system")
    print("This will test quality validation, refinement loops, and output structure")

    results = {}

    # Test 1: Sync
    results['sync'] = test_sync_scene_development()

    # Test 2: Async
    results['async'] = asyncio.run(test_async_scene_development())

    # Test 3: Different scene counts
    results['scene_counts'] = test_different_scene_counts()

    # Test 4: Quality metrics
    results['quality'] = test_quality_metrics()

    # Test 5: Scene structure
    results['structure'] = test_scene_structure()

    # Summary
    print_separator("Test Results Summary")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")

    print(f"\n{'=' * 80}")
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print(f"{'=' * 80}\n")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Scene Development Agent is working correctly.")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
