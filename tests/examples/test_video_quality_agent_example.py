"""
Example script demonstrating Video Quality Agent usage.

This script shows how to use the VideoQualityAgentADK to validate videos
and get quality reports.

REQUIREMENTS:
- FFmpeg installed (`brew install ffmpeg` on macOS)
- Video files in tmp/default/ directory
- Character references in tmp/default/characters/
- story.json with scene descriptions
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.video_quality_agent import VideoQualityAgent
from utils.logger import logger


def example_validate_single_video():
    """
    Example 1: Validate a single video file.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Validating a Single Video")
    print("="*60 + "\n")

    # Initialize agent with quality threshold 8.0
    vqa = VideoQualityAgent(
        quality_threshold=8.0,
        max_retries=2
    )

    # Example character references
    character_refs = [
        {
            "name": "Alice",
            "description": "Young woman with blonde hair, wearing a blue dress and round glasses",
            "image_path": "tmp/default/characters/alice.png"  # Replace with actual path
        }
    ]

    # Example scene description
    scene_desc = {
        "scene_number": 1,
        "location": "Cozy library with wooden shelves and warm lighting",
        "atmosphere": "Quiet, studious, afternoon sunlight streaming through windows",
        "characters": ["Alice"],
        "key_actions": ["Alice walking between shelves", "Picking up a book", "Smiling softly"]
    }

    # Video file to validate (replace with actual path)
    video_path = "tmp/default/1-scene_1_0.mp4"

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        print("   Please generate videos first using the UI (🎬 The Shoot v3.1 tab)")
        return

    print(f"📹 Validating video: {video_path}")
    print(f"🎯 Quality threshold: {vqa.quality_threshold}/10")
    print(f"🔄 Max retries: {vqa.max_retries}")
    print()

    # Validate the video
    try:
        report = vqa.validate_video(
            video_path=video_path,
            scene_number=1,
            character_references=character_refs,
            scene_description=scene_desc,
            original_prompt="Alice exploring a cozy library, picking up a book with curiosity",
            expected_duration=8.0,
            retry_count=0
        )

        # Display results
        print("📊 VALIDATION RESULTS:")
        print("-" * 60)
        print(f"   Overall Score: {report.decision.overall_score:.1f}/10")
        print(f"   Decision: {report.decision.decision}")
        print()
        print("   Detailed Scores:")
        print(f"     • Anatomy: {report.anatomy.anatomy_score:.1f}/10")
        print(f"     • Consistency: {report.consistency.consistency_score:.1f}/10")
        print(f"     • Technical: {report.technical.technical_score:.1f}/10")
        print()

        # Show issues if any
        if report.anatomy.issues:
            print(f"   ⚠️  Anatomy Issues ({len(report.anatomy.issues)}):")
            for issue in report.anatomy.issues[:3]:  # Show first 3
                print(f"      - {issue.get('issue', 'Unknown')}")
            print()

        if not report.consistency.pass_validation:
            print(f"   ⚠️  Consistency Issues:")
            for char_name, char_match in report.consistency.character_matches.items():
                if char_match.get('issues'):
                    print(f"      {char_name}: {', '.join(char_match['issues'][:2])}")
            print()

        # Show improved prompt if retry recommended
        if report.decision.decision == "RETRY":
            print("   🔄 RETRY RECOMMENDED")
            print(f"   Improvement notes:")
            for note in report.decision.improvement_notes:
                print(f"      • {note}")
            print()
            print("   Improved prompt:")
            print(f"   {report.decision.improved_prompt[:200]}...")
            print()

        elif report.decision.decision == "ACCEPT":
            print("   ✅ VIDEO ACCEPTED - Quality meets threshold")
            print()

        elif report.decision.decision == "FAIL":
            print("   ❌ VIDEO FAILED - Quality below threshold after max retries")
            print()

    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()


def example_validate_multiple_videos():
    """
    Example 2: Validate multiple videos in batch.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Batch Validating Multiple Videos")
    print("="*60 + "\n")

    vqa = VideoQualityAgent(quality_threshold=8.0)

    # Example: Validate first 3 scene videos
    videos = []
    for i in range(1, 4):
        video_path = f"tmp/default/{i}-scene_{i}_0.mp4"
        if os.path.exists(video_path):
            videos.append({
                "path": video_path,
                "scene_number": i,
                "prompt": f"Scene {i} description",
                "references": [],
                "scene_description": {},
                "duration": 8.0
            })

    if not videos:
        print("❌ No videos found in tmp/default/")
        print("   Generate videos first using the UI")
        return

    print(f"📹 Found {len(videos)} videos to validate\n")

    # Validate all videos
    try:
        reports = vqa.validate_videos_parallel(
            videos=videos,
            character_references=[],
            scene_descriptions=[]
        )

        # Generate quality report
        quality_report = vqa.generate_quality_report()

        print("📊 QUALITY REPORT:")
        print("-" * 60)
        print(f"   {quality_report['summary']}")
        print()
        print("   Average Scores:")
        for metric, score in quality_report['statistics']['average_scores'].items():
            print(f"     • {metric.capitalize()}: {score}")
        print()

        # Show per-scene details
        print("   Per-Scene Results:")
        for scene_report in quality_report['detailed_reports']:
            status_icon = "✅" if scene_report['decision'] == "ACCEPT" else "🔄" if scene_report['decision'] == "RETRY" else "❌"
            print(f"     {status_icon} Scene {scene_report['scene']}: "
                  f"Overall={scene_report['overall_score']}, "
                  f"Decision={scene_report['decision']}")
        print()

        # Show which scenes need retry
        retry_scenes = vqa.get_retry_scenes()
        if retry_scenes:
            print(f"   🔄 {len(retry_scenes)} scenes need retry:")
            for retry in retry_scenes:
                print(f"     - Scene {retry['scene_number']}: "
                      f"Score={retry['current_score']:.1f}/10")
            print()

    except Exception as e:
        print(f"❌ Batch validation failed: {str(e)}")
        import traceback
        traceback.print_exc()


def check_prerequisites():
    """Check if FFmpeg is available."""
    from utils.video_analysis import check_ffmpeg_available

    print("\n" + "="*60)
    print("CHECKING PREREQUISITES")
    print("="*60 + "\n")

    if check_ffmpeg_available():
        print("✅ FFmpeg is available")
    else:
        print("❌ FFmpeg not found!")
        print("   Install with:")
        print("     macOS: brew install ffmpeg")
        print("     Ubuntu: sudo apt-get install ffmpeg")
        print("     Windows: Download from https://ffmpeg.org/download.html")
        return False

    # Check for video files
    video_dir = Path("tmp/default")
    if video_dir.exists():
        video_files = list(video_dir.glob("*_0.mp4"))
        print(f"✅ Found {len(video_files)} video files in tmp/default/")
    else:
        print("⚠️  tmp/default/ directory not found")
        print("   Generate videos first using the UI")

    print()
    return True


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("VIDEO QUALITY AGENT - USAGE EXAMPLES")
    print("="*60)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install FFmpeg and generate videos first.")
        return

    # Run examples
    try:
        example_validate_single_video()
        example_validate_multiple_videos()

        print("\n" + "="*60)
        print("✅ Examples completed!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Use the UI: python main.py")
        print("  2. Go to 🎬 The Shoot (v3.1) tab")
        print("  3. Enable '🔍 Enable Video Quality Validation'")
        print("  4. Click 'Generate Videos'")
        print("  5. Review the quality report")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
