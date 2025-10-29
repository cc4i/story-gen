"""
ADK-based agent for story idea generation with self-critique and refinement.

This agent uses a self-critique pattern to iteratively improve story generation:
1. Generate initial story structure (characters, setting, plot)
2. Critique the output against quality criteria
3. Refine based on critique
4. Repeat until quality threshold is met (max iterations)
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from google import genai
from google.genai import types

from models.config import DEFAULT_MODEL_ID, GEMINI_API_KEY
from models.exceptions import APIError, ValidationError
from utils.logger import logger
from utils.llm import string_to_pjson


@dataclass
class CritiqueResult:
    """Results from critiquing a story generation."""
    score: float  # 0-10 score
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    passes_threshold: bool


@dataclass
class StoryIteration:
    """Represents one iteration of story generation."""
    iteration: int
    characters: List[Dict]
    setting: str
    plot: str
    critique: Optional[CritiqueResult]
    timestamp: float


class IdeaGenerationAgent:
    """
    Self-critique agent for story idea generation.

    This agent generates story ideas and automatically refines them through
    iterative critique cycles until quality standards are met.
    """

    # Agent configuration
    QUALITY_THRESHOLD = 7.5  # Score out of 10
    MAX_ITERATIONS = 3
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 64
    MAX_OUTPUT_TOKENS = 65536

    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        """
        Initialize the idea generation agent.

        Args:
            model_id: Gemini model ID to use for generation
        """
        self.model_id = model_id
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={'api_version': 'v1alpha'}
        )
        self.iterations: List[StoryIteration] = []

    def _call_llm(self, system_instruction: str, prompt: str) -> str:
        """
        Internal method to call LLM with consistent configuration.

        Args:
            system_instruction: System-level instruction
            prompt: User prompt

        Returns:
            Generated response text
        """
        config = types.GenerateContentConfig(
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_CIVIC_INTEGRITY",
                    threshold="OFF",
                ),
            ],
            response_mime_type="text/plain",
            system_instruction=[types.Part.from_text(text=system_instruction)],
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config
        )

        if not response or not response.text:
            raise APIError("No response received from Gemini API")

        return response.text

    def _generate_initial_story(self, idea: str, style: str) -> Dict:
        """
        Generate initial story structure from user idea.

        Args:
            idea: User's story idea
            style: Visual style for the story

        Returns:
            Dictionary with characters, setting, and plot
        """
        system_instruction = """
        <role>
        You are a creative writer specializing in visual storytelling.
        </role>
        <persona>
        Your goal is to create compelling story structures optimized for video generation.
        You excel at creating vivid, visually-rich narratives with memorable characters.
        </persona>
        <constraints>
        1. Your output MUST be a single, valid JSON object.
        2. The JSON object must strictly follow this structure:
        ```json
        {
            "characters": [
                {
                    "name": "Character name",
                    "sex": "Female or Male",
                    "voice": "High-pitched, Low, Deep, Squeaky, or Booming",
                    "description": "Detailed visual description including appearance, clothing, distinctive features, personality traits"
                }
            ],
            "setting": "Rich description of the world, time period, and environment with visual details",
            "plot": "Engaging narrative arc with clear beginning, middle, and end, focused on visual storytelling"
        }
        ```
        3. Create MAXIMUM 3 characters with rich, distinctive visual characteristics
        4. Each character should be visually unique and memorable
        5. Setting should be vivid and cinematically interesting
        6. Plot should be concise but engaging, suitable for short video format
        7. IMPORTANT: The "sex" field MUST be EXACTLY "Female" or "Male" - no other values are allowed
        8. IMPORTANT: The "voice" field MUST be one of: "High-pitched", "Low", "Deep", "Squeaky", or "Booming"
        </constraints>
        """

        prompt = f"""
        Create a story structure for the following idea:

        Idea: ***{idea}***
        Visual Style: ***{style}***

        Focus on creating visually distinctive characters and a setting that will translate beautifully to {style} video.
        """

        logger.info(f"[Agent] Generating initial story for idea: {idea[:50]}...")
        response = self._call_llm(system_instruction, prompt)

        json_str = string_to_pjson(response)
        if json_str is None:
            raise ValidationError("LLM did not return valid JSON")

        return json.loads(json_str)

    def _critique_story(self, story: Dict, idea: str, style: str) -> CritiqueResult:
        """
        Critique the generated story against quality criteria.

        Args:
            story: Generated story structure
            idea: Original user idea
            style: Visual style

        Returns:
            CritiqueResult with score and feedback
        """
        system_instruction = """
        <role>
        You are an expert story critic specializing in visual storytelling and video generation.
        </role>
        <persona>
        You provide constructive, specific feedback on story structures.
        You evaluate stories based on visual storytelling potential, character depth, and narrative coherence.
        </persona>
        <constraints>
        1. Your output MUST be a single, valid JSON object.
        2. The JSON object must follow this structure:
        ```json
        {
            "score": 8.5,
            "strengths": ["Specific strength 1", "Specific strength 2"],
            "weaknesses": ["Specific weakness 1", "Specific weakness 2"],
            "suggestions": ["Specific actionable suggestion 1", "Specific actionable suggestion 2"]
        }
        ```
        3. Score must be between 0-10 (decimals allowed)
        4. Provide 2-4 specific strengths, weaknesses, and suggestions each
        </constraints>
        """

        prompt = f"""
        Critique this story structure based on the original idea and visual style:

        Original Idea: ***{idea}***
        Visual Style: ***{style}***

        Generated Story:
        ```json
        {json.dumps(story, indent=2)}
        ```

        Evaluate based on:
        1. **Character Quality** (visual distinctiveness, depth, memorability)
        2. **Setting Richness** (visual interest, specificity, atmosphere)
        3. **Plot Coherence** (clear arc, engaging narrative, suitable for video format)
        4. **Visual Storytelling Potential** (how well it will translate to video)
        5. **Alignment with Idea** (faithful to original concept)
        6. **Style Compatibility** (works well with {style})

        Be specific and constructive. A score of 7.5+ indicates excellent quality.
        """

        logger.info("[Agent] Critiquing story structure...")
        response = self._call_llm(system_instruction, prompt)

        json_str = string_to_pjson(response)
        if json_str is None:
            raise ValidationError("Critique did not return valid JSON")

        critique_data = json.loads(json_str)

        score = float(critique_data["score"])
        passes = score >= self.QUALITY_THRESHOLD

        logger.info(f"[Agent] Critique score: {score}/10 (threshold: {self.QUALITY_THRESHOLD})")

        return CritiqueResult(
            score=score,
            strengths=critique_data["strengths"],
            weaknesses=critique_data["weaknesses"],
            suggestions=critique_data["suggestions"],
            passes_threshold=passes
        )

    def _refine_story(self, story: Dict, critique: CritiqueResult, idea: str, style: str) -> Dict:
        """
        Refine the story based on critique feedback.

        Args:
            story: Current story structure
            critique: Critique results with suggestions
            idea: Original user idea
            style: Visual style

        Returns:
            Refined story structure
        """
        system_instruction = """
        <role>
        You are a creative writer specializing in visual storytelling refinement.
        </role>
        <persona>
        You excel at taking good stories and making them great by incorporating specific feedback.
        You maintain the core vision while addressing weaknesses.
        </persona>
        <constraints>
        1. Your output MUST be a single, valid JSON object.
        2. The JSON must follow the same structure as before:
        ```json
        {
            "characters": [...],
            "setting": "...",
            "plot": "..."
        }
        ```
        3. MAINTAIN the core concept and strong elements
        4. ADDRESS all weaknesses and incorporate suggestions
        5. Keep character limit at maximum 3
        6. Preserve character names unless specifically problematic
        7. IMPORTANT: Each character's "sex" field MUST be EXACTLY "Female" or "Male" - no other values allowed
        8. IMPORTANT: Each character's "voice" field MUST be one of: "High-pitched", "Low", "Deep", "Squeaky", or "Booming"
        </constraints>
        """

        weaknesses_str = "\n".join(f"- {w}" for w in critique.weaknesses)
        suggestions_str = "\n".join(f"- {s}" for s in critique.suggestions)
        strengths_str = "\n".join(f"- {s}" for s in critique.strengths)

        prompt = f"""
        Refine this story structure based on the critique feedback:

        Original Idea: ***{idea}***
        Visual Style: ***{style}***

        Current Story:
        ```json
        {json.dumps(story, indent=2)}
        ```

        Critique Score: {critique.score}/10

        Strengths (PRESERVE these):
        {strengths_str}

        Weaknesses (ADDRESS these):
        {weaknesses_str}

        Suggestions (INCORPORATE these):
        {suggestions_str}

        Create an improved version that addresses the weaknesses while maintaining the strengths.
        """

        logger.info(f"[Agent] Refining story based on critique (score: {critique.score})...")
        response = self._call_llm(system_instruction, prompt)

        json_str = string_to_pjson(response)
        if json_str is None:
            raise ValidationError("Refinement did not return valid JSON")

        return json.loads(json_str)

    def generate_story(self, idea: str, style: str = "Studio Ghibli") -> Tuple[List[Dict], str, str]:
        """
        Generate and refine story structure using self-critique agent pattern.

        This is the main entry point for the agent. It will:
        1. Generate initial story
        2. Critique it
        3. Refine based on critique
        4. Repeat until quality threshold is met or max iterations reached

        Args:
            idea: User's story idea
            style: Visual style for the story

        Returns:
            Tuple of (characters, setting, plot) for the best story
        """
        operation_start = time.time()
        logger.info(f"[Agent] Starting story generation with self-critique (max iterations: {self.MAX_ITERATIONS})")

        try:
            # Generate initial story
            current_story = self._generate_initial_story(idea, style)

            best_story = current_story
            best_score = 0.0

            # Iterative refinement loop
            for iteration in range(1, self.MAX_ITERATIONS + 1):
                logger.info(f"[Agent] === Iteration {iteration}/{self.MAX_ITERATIONS} ===")

                # Critique current story
                critique = self._critique_story(current_story, idea, style)

                # Store iteration
                self.iterations.append(StoryIteration(
                    iteration=iteration,
                    characters=current_story["characters"],
                    setting=current_story["setting"],
                    plot=current_story["plot"],
                    critique=critique,
                    timestamp=time.time()
                ))

                # Track best version
                if critique.score > best_score:
                    best_score = critique.score
                    best_story = current_story
                    logger.info(f"[Agent] New best score: {best_score}/10")

                # Log critique details
                logger.info(f"[Agent] Strengths: {', '.join(critique.strengths[:2])}...")
                logger.info(f"[Agent] Weaknesses: {', '.join(critique.weaknesses[:2])}...")

                # Check if we've met quality threshold
                if critique.passes_threshold:
                    logger.info(f"[Agent] ✓ Quality threshold met (score: {critique.score} >= {self.QUALITY_THRESHOLD})")
                    break

                # Refine if not final iteration
                if iteration < self.MAX_ITERATIONS:
                    logger.info(f"[Agent] Score {critique.score} below threshold, refining...")
                    current_story = self._refine_story(current_story, critique, idea, style)
                else:
                    logger.info(f"[Agent] Max iterations reached, using best result (score: {best_score})")

            duration = time.time() - operation_start
            logger.info(f"[Agent] Story generation completed in {duration:.2f}s with {len(self.iterations)} iterations")
            logger.info(f"[Agent] Final score: {best_score}/10")

            # Return best story in the expected format
            return (
                best_story["characters"],
                best_story["setting"],
                best_story["plot"]
            )

        except Exception as e:
            logger.error(f"[Agent] Story generation failed: {str(e)}", exc_info=True)
            raise APIError(f"Agent-based story generation failed: {str(e)}")

    def get_iteration_history(self) -> List[StoryIteration]:
        """
        Get the history of all iterations.

        Returns:
            List of StoryIteration objects
        """
        return self.iterations

    def get_critique_summary(self) -> str:
        """
        Get a human-readable summary of all critiques.

        Returns:
            Formatted string with critique history
        """
        if not self.iterations:
            return "No iterations yet"

        lines = ["=== Story Generation Iterations ===\n"]
        for it in self.iterations:
            if it.critique:
                lines.append(f"Iteration {it.iteration}: Score {it.critique.score}/10")
                lines.append(f"  Strengths: {', '.join(it.critique.strengths)}")
                lines.append(f"  Weaknesses: {', '.join(it.critique.weaknesses)}")
                lines.append("")

        return "\n".join(lines)
