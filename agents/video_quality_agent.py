"""
Video Quality Validation Agent for video generation quality control.

This agent uses a 4-validator architecture with Gemini multimodal analysis:

ARCHITECTURE:
1. AnatomyValidator: Detects anatomical errors (extra limbs, morphing)
2. ConsistencyValidator: Validates character consistency with references
3. TechnicalValidator: Checks technical quality (blur, motion, duration)
4. QualityDecision: Aggregates scores and decides ACCEPT/RETRY/FAIL

The system validates videos, then selectively regenerates failed scenes
with improved prompts.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from google.genai import types, Client

from models.config import DEFAULT_MODEL_ID, GEMINI_API_KEY, PROJECT_ID, VERTEX_LOCATION
from utils.logger import logger
from utils.llm import call_llm, load_prompt
from utils.video_analysis import (
    extract_key_frames,
    extract_character_frames,
    get_video_metadata,
    calculate_motion_quality,
    extract_visual_quality_metrics,
    check_ffmpeg_available
)
from PIL import Image


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AnatomyValidationResult:
    """Results from anatomy validation."""
    anatomy_score: float
    issues: List[Dict]
    pass_validation: bool
    suggestions: List[str]
    frame_count: int


@dataclass
class ConsistencyValidationResult:
    """Results from consistency validation."""
    consistency_score: float
    character_matches: Dict[str, Dict]
    cross_scene_consistency: float
    pass_validation: bool
    suggestions: List[str]


@dataclass
class TechnicalValidationResult:
    """Results from technical validation."""
    technical_score: float
    duration_actual: float
    duration_expected: float
    motion_quality: float
    visual_clarity: float
    issues: List[str]
    pass_validation: bool


@dataclass
class QualityDecision:
    """Final quality decision."""
    decision: str  # "ACCEPT", "RETRY", "FAIL"
    overall_score: float
    weighted_breakdown: Dict[str, float]
    retry_count: int
    improved_prompt: Optional[str]
    improvement_notes: List[str]


@dataclass
class VideoValidationReport:
    """Complete validation report for one video."""
    video_path: str
    scene_number: int
    anatomy: AnatomyValidationResult
    consistency: ConsistencyValidationResult
    technical: TechnicalValidationResult
    decision: QualityDecision
    timestamp: float


# ============================================================================
# Shared State Container
# ============================================================================

class VideoQualityState:
    """Shared state container for video quality validation."""

    def __init__(self):
        # Input data
        self.videos: List[Dict] = []  # {path, scene_number, prompt, references}
        self.character_references: List[Dict] = []
        self.scene_descriptions: List[Dict] = []
        self.quality_threshold: float = 8.0
        self.max_retries: int = 2

        # Validation results
        self.validation_reports: List[VideoValidationReport] = []
        self.failed_scenes: List[Dict] = []
        self.retry_history: Dict[int, List[Dict]] = {}  # scene_number: [attempts]

        # Statistics
        self.total_validated: int = 0
        self.total_passed: int = 0
        self.total_retried: int = 0
        self.total_failed: int = 0


# ============================================================================
# Agent Instructions
# ============================================================================

ANATOMY_VALIDATOR_INSTRUCTION = load_prompt("quality_validation/anatomy_validator.md")

CONSISTENCY_VALIDATOR_INSTRUCTION = load_prompt("quality_validation/consistency_validator.md")

TECHNICAL_VALIDATOR_INSTRUCTION = load_prompt("quality_validation/technical_validator.md")

QUALITY_DECISION_INSTRUCTION = load_prompt("quality_validation/quality_decision.md")

PROMPT_REFINEMENT_AGENT_INSTRUCTION = load_prompt("quality_validation/prompt_refinement.md")


# ============================================================================
# Helper Functions for Gemini Multimodal Analysis
# ============================================================================

def analyze_frames_with_gemini(
    frames: List[Image.Image],
    instruction: str,
    context: Dict,
    model_id: str
) -> Dict:
    """
    Analyze video frames using Gemini multimodal model.

    Args:
        frames: List of PIL Image frames
        instruction: System instruction for the agent
        context: Additional context (character descriptions, etc.)
        model_id: Gemini model to use (from agent config)

    Returns:
        Parsed JSON response from model
    """
    client = Client(vertexai=True, project=PROJECT_ID, location=VERTEX_LOCATION)

    try:
        # Build prompt with context
        prompt_template = load_prompt("quality_validation/gemini_analysis_user.md")
        prompt = prompt_template.format(
            instruction=instruction,
            context=json.dumps(context, indent=2),
            frame_count=len(frames)
        )

        # Build contents: frames first, then text prompt
        contents = list(frames) + [prompt]

        logger.debug(f"Sending {len(frames)} frames to Gemini for analysis")

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent validation
                response_mime_type="application/json"
            )
        )

        # Parse JSON response
        result_text = response.text
        result_json = json.loads(result_text)

        logger.debug(f"Gemini analysis complete: {len(result_text)} chars")
        return result_json

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
        logger.error(f"Response text: {response.text[:500]}")
        raise Exception(f"Invalid JSON response from Gemini: {str(e)}")
    except Exception as e:
        logger.error(f"Gemini analysis failed: {str(e)}")
        raise


# ============================================================================
# Validator Agents (Synchronous Functions for Simplicity)
# ============================================================================

def validate_anatomy(
    video_path: str,
    character_descriptions: List[Dict],
    expected_character_count: int,
    model_id: str = DEFAULT_MODEL_ID
) -> AnatomyValidationResult:
    """
    Validate video anatomy using Gemini multimodal analysis.

    Args:
        video_path: Path to video file
        character_descriptions: List of character dicts with descriptions
        expected_character_count: Number of characters expected in scene
        model_id: Gemini model to use for validation

    Returns:
        AnatomyValidationResult with scores and issues
    """
    logger.info(f"[AnatomyValidator] Validating: {Path(video_path).name}")

    try:
        # Extract key frames
        frames = extract_key_frames(video_path, num_frames=10)

        # Prepare context
        context = {
            "expected_characters": expected_character_count,
            "character_descriptions": character_descriptions,
            "frame_count": len(frames)
        }

        # Analyze with Gemini
        result = analyze_frames_with_gemini(
            frames=frames,
            instruction=ANATOMY_VALIDATOR_INSTRUCTION,
            context=context,
            model_id=model_id
        )

        # Convert to dataclass
        return AnatomyValidationResult(
            anatomy_score=result.get("anatomy_score", 0.0),
            issues=result.get("issues", []),
            pass_validation=result.get("pass_validation", False),
            suggestions=result.get("suggestions", []),
            frame_count=result.get("frame_count", len(frames))
        )

    except Exception as e:
        logger.error(f"[AnatomyValidator] Validation failed: {str(e)}")
        # Return failure result
        return AnatomyValidationResult(
            anatomy_score=0.0,
            issues=[{"issue": f"Validation error: {str(e)}", "severity": "critical"}],
            pass_validation=False,
            suggestions=["Retry validation or regenerate video"],
            frame_count=0
        )


def validate_consistency(
    video_path: str,
    character_references: List[Dict],  # {name, image_path, description}
    scene_description: Dict,
    model_id: str = DEFAULT_MODEL_ID
) -> ConsistencyValidationResult:
    """
    Validate character consistency with reference images.

    Args:
        video_path: Path to video file
        character_references: List of {name, image_path, description}
        scene_description: Scene details
        model_id: Gemini model to use for validation

    Returns:
        ConsistencyValidationResult
    """
    logger.info(f"[ConsistencyValidator] Validating: {Path(video_path).name}")

    try:
        # Extract character-focused frames
        frames = extract_character_frames(video_path, num_frames=5)

        # Load reference images
        reference_images = []
        for char_ref in character_references:
            img_path = char_ref.get("image_path")
            if img_path and Path(img_path).exists():
                ref_img = Image.open(img_path)
                if ref_img.mode != 'RGB':
                    ref_img = ref_img.convert('RGB')
                reference_images.append(ref_img)

        # Combine reference images with video frames
        all_images = reference_images + frames

        # Prepare context
        context = {
            "character_references": character_references,
            "scene_description": scene_description,
            "reference_image_count": len(reference_images),
            "video_frame_count": len(frames)
        }

        # Analyze with Gemini
        result = analyze_frames_with_gemini(
            frames=all_images,
            instruction=CONSISTENCY_VALIDATOR_INSTRUCTION,
            context=context,
            model_id=model_id
        )

        return ConsistencyValidationResult(
            consistency_score=result.get("consistency_score", 0.0),
            character_matches=result.get("character_matches", {}),
            cross_scene_consistency=result.get("cross_scene_consistency", 0.0),
            pass_validation=result.get("pass_validation", False),
            suggestions=result.get("suggestions", [])
        )

    except Exception as e:
        logger.error(f"[ConsistencyValidator] Validation failed: {str(e)}")
        return ConsistencyValidationResult(
            consistency_score=0.0,
            character_matches={},
            cross_scene_consistency=0.0,
            pass_validation=False,
            suggestions=[f"Validation error: {str(e)}"]
        )


def validate_technical(
    video_path: str,
    expected_duration: float = 8.0
) -> TechnicalValidationResult:
    """
    Validate technical video quality.

    Args:
        video_path: Path to video file
        expected_duration: Expected duration in seconds

    Returns:
        TechnicalValidationResult
    """
    logger.info(f"[TechnicalValidator] Validating: {Path(video_path).name}")

    try:
        # Get video metadata
        metadata = get_video_metadata(video_path)
        actual_duration = metadata['duration']

        # Calculate motion quality
        motion_quality = calculate_motion_quality(video_path)

        # Get visual quality metrics
        visual_metrics = extract_visual_quality_metrics(video_path)
        visual_clarity = visual_metrics['clarity_score']

        # Check duration tolerance
        duration_diff = abs(actual_duration - expected_duration)
        duration_ok = duration_diff <= 0.5

        # Aggregate issues
        issues = []
        if not duration_ok:
            issues.append(f"Duration mismatch: {actual_duration:.1f}s vs expected {expected_duration:.1f}s")
        if motion_quality < 0.7:
            issues.append(f"Poor motion quality: {motion_quality:.2f}")
        if visual_clarity < 0.7:
            issues.append(f"Low visual clarity: {visual_clarity:.2f}")

        # Calculate technical score
        technical_score = (
            (10.0 if duration_ok else 6.0) * 0.3 +
            motion_quality * 10.0 * 0.35 +
            visual_clarity * 10.0 * 0.35
        )

        pass_validation = technical_score >= 7.5 and duration_ok

        return TechnicalValidationResult(
            technical_score=technical_score,
            duration_actual=actual_duration,
            duration_expected=expected_duration,
            motion_quality=motion_quality,
            visual_clarity=visual_clarity,
            issues=issues,
            pass_validation=pass_validation
        )

    except Exception as e:
        logger.error(f"[TechnicalValidator] Validation failed: {str(e)}")
        return TechnicalValidationResult(
            technical_score=0.0,
            duration_actual=0.0,
            duration_expected=expected_duration,
            motion_quality=0.0,
            visual_clarity=0.0,
            issues=[f"Validation error: {str(e)}"],
            pass_validation=False
        )


def make_quality_decision(
    anatomy_result: AnatomyValidationResult,
    consistency_result: ConsistencyValidationResult,
    technical_result: TechnicalValidationResult,
    original_prompt: str,
    retry_count: int,
    quality_threshold: float = 8.0
) -> QualityDecision:
    """
    Make final quality decision and generate improved prompt if needed.

    Args:
        anatomy_result: Anatomy validation result
        consistency_result: Consistency validation result
        technical_result: Technical validation result
        original_prompt: Original video generation prompt
        retry_count: Current retry count (0 = first attempt)
        quality_threshold: Minimum acceptable score

    Returns:
        QualityDecision with decision and optional improved prompt
    """
    logger.info(f"[QualityDecision] Making decision (retry_count={retry_count})")

    # Calculate weighted score
    overall_score = (
        anatomy_result.anatomy_score * 0.40 +
        consistency_result.consistency_score * 0.35 +
        technical_result.technical_score * 0.25
    )

    weighted_breakdown = {
        "anatomy": anatomy_result.anatomy_score,
        "consistency": consistency_result.consistency_score,
        "technical": technical_result.technical_score
    }

    logger.info(f"[QualityDecision] Scores: anatomy={anatomy_result.anatomy_score:.1f}, "
                f"consistency={consistency_result.consistency_score:.1f}, "
                f"technical={technical_result.technical_score:.1f}, "
                f"overall={overall_score:.1f}")

    # Decision logic
    decision = "ACCEPT"
    improved_prompt = None
    improvement_notes = []

    # Check for critical anatomy issues (always retry if fixable)
    has_critical_anatomy = any(
        issue.get("severity") == "critical"
        for issue in anatomy_result.issues
    )

    # Decision tree
    if overall_score >= quality_threshold:
        decision = "ACCEPT"
        logger.info(f"[QualityDecision] ACCEPT - score {overall_score:.1f} >= threshold {quality_threshold}")

    elif retry_count >= 2:
        # Max retries reached
        if overall_score >= 6.5:
            decision = "ACCEPT"
            logger.info(f"[QualityDecision] ACCEPT (max retries) - score {overall_score:.1f} acceptable")
        else:
            decision = "FAIL"
            logger.warning(f"[QualityDecision] FAIL - max retries exceeded, score still {overall_score:.1f}")

    elif has_critical_anatomy and retry_count < 2:
        # Critical anatomy issues - always retry
        decision = "RETRY"
        # Try LLM-powered refinement, fallback to rule-based if it fails
        try:
            improved_prompt, improvement_notes = refine_prompt_with_llm(
                original_prompt, anatomy_result, consistency_result, technical_result, retry_count
            )
            logger.info(f"[QualityDecision] RETRY - critical anatomy issues detected (using LLM refinement)")
        except Exception as e:
            logger.warning(f"[QualityDecision] LLM refinement failed, using rule-based fallback: {str(e)}")
            improved_prompt, improvement_notes = refine_prompt_rule_based(
                original_prompt, anatomy_result, consistency_result, technical_result
            )
            improvement_notes.append("Used rule-based fallback due to LLM failure")
            logger.info(f"[QualityDecision] RETRY - critical anatomy issues detected (using rule-based fallback)")

    elif overall_score < quality_threshold and retry_count < 2:
        # Below threshold - retry with improvements
        decision = "RETRY"
        # Try LLM-powered refinement, fallback to rule-based if it fails
        try:
            improved_prompt, improvement_notes = refine_prompt_with_llm(
                original_prompt, anatomy_result, consistency_result, technical_result, retry_count
            )
            logger.info(f"[QualityDecision] RETRY - score {overall_score:.1f} < threshold {quality_threshold} (using LLM refinement)")
        except Exception as e:
            logger.warning(f"[QualityDecision] LLM refinement failed, using rule-based fallback: {str(e)}")
            improved_prompt, improvement_notes = refine_prompt_rule_based(
                original_prompt, anatomy_result, consistency_result, technical_result
            )
            improvement_notes.append("Used rule-based fallback due to LLM failure")
            logger.info(f"[QualityDecision] RETRY - score {overall_score:.1f} < threshold {quality_threshold} (using rule-based fallback)")

    return QualityDecision(
        decision=decision,
        overall_score=overall_score,
        weighted_breakdown=weighted_breakdown,
        retry_count=retry_count,
        improved_prompt=improved_prompt,
        improvement_notes=improvement_notes
    )


def build_refinement_context(
    original_prompt: str,
    anatomy_result: AnatomyValidationResult,
    consistency_result: ConsistencyValidationResult,
    technical_result: TechnicalValidationResult,
    retry_count: int
) -> Dict:
    """
    Build comprehensive context for LLM-powered prompt refinement.

    Extracts all relevant validation details including:
    - Validator suggestions (currently unused in rule-based approach!)
    - Character-specific consistency issues
    - Severity-prioritized anatomy issues
    - Technical quality metrics

    Args:
        original_prompt: Original video generation prompt
        anatomy_result: Anatomy validation results
        consistency_result: Consistency validation results
        technical_result: Technical validation results
        retry_count: Current retry attempt number

    Returns:
        Dictionary with comprehensive validation context for LLM
    """
    # Extract character-specific consistency issues
    failing_characters = []
    for char_name, match_data in consistency_result.character_matches.items():
        similarity = match_data.get("reference_similarity", 1.0)
        if similarity < 0.85:
            failing_characters.append({
                "name": char_name,
                "similarity": similarity,
                "issues": match_data.get("issues", []),
                "severity": match_data.get("severity", "unknown")
            })

    # Prioritize anatomy issues by severity
    critical_anatomy = [i for i in anatomy_result.issues if i.get("severity") == "critical"]
    major_anatomy = [i for i in anatomy_result.issues if i.get("severity") == "major"]
    minor_anatomy = [i for i in anatomy_result.issues if i.get("severity") == "minor"]

    # Determine overall priority level
    if critical_anatomy:
        priority = "critical"
    elif major_anatomy or anatomy_result.anatomy_score < 7.0:
        priority = "high"
    elif not anatomy_result.pass_validation or not consistency_result.pass_validation:
        priority = "moderate"
    else:
        priority = "low"

    context = {
        "original_prompt": original_prompt,
        "retry_count": retry_count,
        "priority": priority,

        "anatomy_validation": {
            "score": anatomy_result.anatomy_score,
            "passed": anatomy_result.pass_validation,
            "critical_issues": critical_anatomy,
            "major_issues": major_anatomy,
            "minor_issues": minor_anatomy,
            "total_issues": len(anatomy_result.issues),
            "suggestions": anatomy_result.suggestions  # KEY: Now used by LLM!
        },

        "consistency_validation": {
            "score": consistency_result.consistency_score,
            "passed": consistency_result.pass_validation,
            "failing_characters": failing_characters,  # NEW: Character-specific issues
            "cross_scene_consistency": consistency_result.cross_scene_consistency,
            "suggestions": consistency_result.suggestions  # KEY: Now used by LLM!
        },

        "technical_validation": {
            "score": technical_result.technical_score,
            "passed": technical_result.pass_validation,
            "motion_quality": technical_result.motion_quality,
            "visual_clarity": technical_result.visual_clarity,
            "duration_actual": technical_result.duration_actual,
            "duration_expected": technical_result.duration_expected,
            "issues": technical_result.issues
        }
    }

    return context


def refine_prompt_with_llm(
    original_prompt: str,
    anatomy_result: AnatomyValidationResult,
    consistency_result: ConsistencyValidationResult,
    technical_result: TechnicalValidationResult,
    retry_count: int = 0,
    model_id: str = DEFAULT_MODEL_ID
) -> Tuple[str, List[str]]:
    """
    Use LLM to intelligently refine prompt based on validation results.

    This function leverages an LLM agent to:
    - Analyze validation failures holistically
    - Incorporate validator suggestions (previously unused!)
    - Generate character-specific improvements
    - Create targeted, context-aware refinements

    Args:
        original_prompt: Original prompt that generated the video
        anatomy_result: Anatomy validation results
        consistency_result: Consistency validation results
        technical_result: Technical validation results
        retry_count: Current retry attempt (0 = first)
        model_id: Gemini model to use for refinement

    Returns:
        Tuple of (improved_prompt, improvement_notes)

    Raises:
        Exception: If LLM refinement fails (caller should use fallback)
    """
    logger.info(f"[PromptRefinement] Using LLM-powered refinement (retry={retry_count})")

    try:
        # Build comprehensive context with all validation details
        context = build_refinement_context(
            original_prompt, anatomy_result, consistency_result,
            technical_result, retry_count
        )

        # Log what we're working with
        logger.debug(f"[PromptRefinement] Context built: priority={context['priority']}, "
                    f"anatomy_score={anatomy_result.anatomy_score:.1f}, "
                    f"consistency_score={consistency_result.consistency_score:.1f}, "
                    f"technical_score={technical_result.technical_score:.1f}")

        # Create refinement prompt for LLM
        refinement_prompt_template = load_prompt("quality_validation/refinement_user.md")
        refinement_prompt = refinement_prompt_template.format(context=json.dumps(context, indent=2))

        # Call LLM with prompt refinement agent instruction
        logger.debug(f"[PromptRefinement] Calling LLM with model: {model_id}")
        response_json = call_llm(
            system_instruction=PROMPT_REFINEMENT_AGENT_INSTRUCTION,
            prompt=refinement_prompt,
            history="",
            model_id=model_id
        )

        # Parse LLM response
        result = json.loads(response_json)

        # Extract improved prompt
        improved_prompt = result.get("improved_prompt", original_prompt)

        # Build improvement notes from LLM response
        improvement_notes = []

        # Add structured improvements
        for improvement in result.get("improvements_applied", []):
            category = improvement.get("category", "general")
            issue = improvement.get("issue_addressed", "unknown")
            fix = improvement.get("improvement", "applied fix")
            improvement_notes.append(f"[{category}] {issue}: {fix}")

        # Add suggestions used
        suggestions_used = result.get("suggestions_used", [])
        if suggestions_used:
            improvement_notes.append(f"Validator suggestions incorporated: {len(suggestions_used)}")

        # Add simplifications if any
        simplifications = result.get("simplifications", [])
        if simplifications:
            for simp in simplifications:
                improvement_notes.append(f"[simplification] {simp}")

        # Add metadata
        confidence = result.get("confidence", "N/A")
        expected_improvement = result.get("expected_score_improvement", "N/A")
        improvement_notes.append(f"LLM confidence: {confidence}, Expected improvement: {expected_improvement}")

        logger.info(f"[PromptRefinement] LLM refinement complete: {len(improvement_notes)} improvements applied")
        logger.debug(f"[PromptRefinement] Suggestions used: {suggestions_used}")

        return improved_prompt, improvement_notes

    except json.JSONDecodeError as e:
        logger.error(f"[PromptRefinement] Failed to parse LLM JSON response: {str(e)}")
        raise Exception(f"Invalid JSON from LLM refinement: {str(e)}")
    except Exception as e:
        logger.error(f"[PromptRefinement] LLM refinement failed: {str(e)}")
        raise  # Let caller handle fallback


def refine_prompt_rule_based(
    original_prompt: str,
    anatomy_result: AnatomyValidationResult,
    consistency_result: ConsistencyValidationResult,
    technical_result: TechnicalValidationResult
) -> Tuple[str, List[str]]:
    """
    Generate improved prompt based on validation results using rule-based approach.

    This is the original, static rule-based refinement function.
    It serves as a fallback when LLM-powered refinement fails.

    Args:
        original_prompt: Original prompt that generated the video
        anatomy_result: Anatomy validation results
        consistency_result: Consistency validation results
        technical_result: Technical validation results

    Returns:
        Tuple of (improved_prompt, improvement_notes)
    """
    improvements = []
    notes = []

    # Collect all suggestions
    all_suggestions = (
        anatomy_result.suggestions +
        consistency_result.suggestions +
        technical_result.issues  # Technical issues can guide improvements
    )

    # Build negative prompt additions
    negative_additions = []

    # Anatomy improvements
    if anatomy_result.anatomy_score < 8.0:
        negative_additions.extend([
            "extra limbs",
            "deformed hands",
            "multiple hands",
            "mutated fingers",
            "extra fingers",
            "distorted body"
        ])
        notes.append("Added negative prompts for anatomy")

    # Consistency improvements
    if consistency_result.consistency_score < 7.5:
        improvements.append("Exactly matching the reference character shown.")
        notes.append("Strengthened reference matching instruction")

    # Technical/motion improvements
    if technical_result.motion_quality < 0.8:
        improvements.append("Simple, slow, smooth camera movement.")
        improvements.append("Minimal character motion, natural expressions.")
        notes.append("Simplified motion complexity")

    # Build improved prompt
    improved_parts = []

    # Add reference strengthening prefix if needed
    if consistency_result.consistency_score < 7.5:
        improved_parts.append("CHARACTER APPEARANCE: Exactly matching the provided reference images.")

    # Add original prompt
    improved_parts.append(original_prompt)

    # Add improvements
    if improvements:
        improved_parts.append("\n" + " ".join(improvements))

    # Add negative prompt
    if negative_additions:
        negative_prompt = "AVOID: " + ", ".join(negative_additions)
        improved_parts.append(negative_prompt)
        notes.append("Added negative prompt")

    improved_prompt = "\n".join(improved_parts)

    logger.debug(f"[PromptRefinement] Applied {len(notes)} improvements")
    return improved_prompt, notes


# ============================================================================
# Main Video Quality Agent
# ============================================================================

class VideoQualityAgent:
    """
    Main agent for video quality validation and improvement.

    Uses Gemini multimodal analysis to validate videos and improve quality
    through intelligent retry with prompt refinement.
    """

    def __init__(
        self,
        quality_threshold: float = 8.0,
        max_retries: int = 2,
        model_id: str = DEFAULT_MODEL_ID
    ):
        """
        Initialize Video Quality Agent.

        Args:
            quality_threshold: Minimum acceptable quality score (0-10)
            max_retries: Maximum retry attempts per video
            model_id: Gemini model ID for validation
        """
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries
        self.model_id = model_id
        self.state = VideoQualityState()

        # Check FFmpeg availability
        if not check_ffmpeg_available():
            logger.warning("FFmpeg not available - some quality checks may fail")

        logger.info(f"[VideoQualityAgent] Initialized: threshold={quality_threshold}, max_retries={max_retries}")

    def validate_video(
        self,
        video_path: str,
        scene_number: int,
        character_references: List[Dict],
        scene_description: Dict,
        original_prompt: str,
        expected_duration: float = 8.0,
        retry_count: int = 0
    ) -> VideoValidationReport:
        """
        Validate a single video with all three validators.

        Args:
            video_path: Path to video file
            scene_number: Scene number
            character_references: List of character reference dicts
            scene_description: Scene details
            original_prompt: Original generation prompt
            expected_duration: Expected video duration
            retry_count: Current retry attempt (0 = first)

        Returns:
            Complete validation report
        """
        logger.info(f"[VideoQualityAgent] Validating scene {scene_number}: {Path(video_path).name} (attempt {retry_count + 1})")

        start_time = time.time()

        # Run all three validators
        # In production, these could run in parallel for speed
        logger.info(f"[VideoQualityAgent] Running anatomy validation...")
        anatomy_result = validate_anatomy(
            video_path=video_path,
            character_descriptions=[ref.get("description", "") for ref in character_references],
            expected_character_count=len(character_references),
            model_id=self.model_id
        )

        logger.info(f"[VideoQualityAgent] Running consistency validation...")
        consistency_result = validate_consistency(
            video_path=video_path,
            character_references=character_references,
            scene_description=scene_description,
            model_id=self.model_id
        )

        logger.info(f"[VideoQualityAgent] Running technical validation...")
        technical_result = validate_technical(
            video_path=video_path,
            expected_duration=expected_duration
        )

        # Make final decision
        logger.info(f"[VideoQualityAgent] Making quality decision...")
        decision = make_quality_decision(
            anatomy_result=anatomy_result,
            consistency_result=consistency_result,
            technical_result=technical_result,
            original_prompt=original_prompt,
            retry_count=retry_count,
            quality_threshold=self.quality_threshold
        )

        duration = time.time() - start_time

        # Build report
        report = VideoValidationReport(
            video_path=video_path,
            scene_number=scene_number,
            anatomy=anatomy_result,
            consistency=consistency_result,
            technical=technical_result,
            decision=decision,
            timestamp=time.time()
        )

        logger.info(f"[VideoQualityAgent] Validation complete in {duration:.1f}s: "
                    f"Decision={decision.decision}, Score={decision.overall_score:.1f}/10")

        return report

    def validate_videos_parallel(
        self,
        videos: List[Dict],  # {path, scene_number, prompt, references}
        character_references: List[Dict],
        scene_descriptions: List[Dict]
    ) -> List[VideoValidationReport]:
        """
        Validate multiple videos in parallel (simulation - actual parallel needs async).

        Args:
            videos: List of video dicts
            character_references: Character reference data
            scene_descriptions: Scene description data

        Returns:
            List of validation reports
        """
        logger.info(f"[VideoQualityAgent] Validating {len(videos)} videos...")

        reports = []
        for video_data in videos:
            report = self.validate_video(
                video_path=video_data['path'],
                scene_number=video_data['scene_number'],
                character_references=character_references,
                scene_description=video_data.get('scene_description', {}),
                original_prompt=video_data['prompt'],
                expected_duration=video_data.get('duration', 8.0),
                retry_count=0
            )
            reports.append(report)

        self.state.validation_reports.extend(reports)
        self.state.total_validated += len(reports)
        self.state.total_passed += sum(1 for r in reports if r.decision.decision == "ACCEPT")

        logger.info(f"[VideoQualityAgent] Validation complete: "
                    f"{self.state.total_passed}/{len(reports)} passed on first attempt")

        return reports

    def generate_quality_report(self) -> Dict:
        """
        Generate human-readable quality report.

        Returns:
            Dictionary with quality statistics and summaries
        """
        reports = self.state.validation_reports

        if not reports:
            return {"summary": "No validations performed"}

        total = len(reports)
        passed = sum(1 for r in reports if r.decision.decision == "ACCEPT")
        retry = sum(1 for r in reports if r.decision.decision == "RETRY")
        failed = sum(1 for r in reports if r.decision.decision == "FAIL")

        avg_score = sum(r.decision.overall_score for r in reports) / total
        avg_anatomy = sum(r.anatomy.anatomy_score for r in reports) / total
        avg_consistency = sum(r.consistency.consistency_score for r in reports) / total
        avg_technical = sum(r.technical.technical_score for r in reports) / total

        return {
            "summary": f"{passed}/{total} scenes passed, {retry} need retry, {failed} failed",
            "statistics": {
                "total_validated": total,
                "passed": passed,
                "retry_needed": retry,
                "failed": failed,
                "pass_rate": f"{(passed/total*100):.1f}%",
                "average_scores": {
                    "overall": f"{avg_score:.1f}/10",
                    "anatomy": f"{avg_anatomy:.1f}/10",
                    "consistency": f"{avg_consistency:.1f}/10",
                    "technical": f"{avg_technical:.1f}/10"
                }
            },
            "detailed_reports": [
                {
                    "scene": r.scene_number,
                    "decision": r.decision.decision,
                    "overall_score": f"{r.decision.overall_score:.1f}",
                    "anatomy": f"{r.anatomy.anatomy_score:.1f}",
                    "consistency": f"{r.consistency.consistency_score:.1f}",
                    "technical": f"{r.technical.technical_score:.1f}",
                    "issues": len(r.anatomy.issues) + len(r.consistency.character_matches) + len(r.technical.issues)
                }
                for r in reports
            ]
        }

    def get_retry_scenes(self) -> List[Dict]:
        """
        Get list of scenes that need retry with improved prompts.

        Returns:
            List of dicts with scene info and improved prompts
        """
        retry_scenes = []

        for report in self.state.validation_reports:
            if report.decision.decision == "RETRY":
                retry_scenes.append({
                    "scene_number": report.scene_number,
                    "original_path": report.video_path,
                    "improved_prompt": report.decision.improved_prompt,
                    "improvement_notes": report.decision.improvement_notes,
                    "current_score": report.decision.overall_score,
                    "retry_count": report.decision.retry_count + 1
                })

        return retry_scenes
