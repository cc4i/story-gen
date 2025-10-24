"""
ADK-based agent for story idea generation with self-critique and refinement.

This agent uses Google Agent Development Kit (ADK) with a LoopAgent to orchestrate
a multi-agent self-critique pattern:

1. StoryGeneratorAgent: Generates or refines story structure
2. StoryCriticAgent: Evaluates story quality against criteria
3. QualityDecisionAgent: Decides whether to exit (escalate) or continue refining

The LoopAgent runs these three agents sequentially until quality threshold is met
or max iterations are reached.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from google.adk.agents import LoopAgent, LlmAgent, RunConfig
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from models.config import DEFAULT_MODEL_ID
from models.exceptions import APIError, ValidationError
from utils.logger import logger
from utils.llm import string_to_pjson


# ============================================================================
# Data Models
# ============================================================================

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


# ============================================================================
# Custom Tools for State Management
# ============================================================================

class AgentState:
    """Shared state container for agent collaboration."""

    def __init__(self):
        self.idea: str = ""
        self.style: str = ""
        self.current_story: Optional[Dict] = None
        self.current_critique: Optional[Dict] = None
        self.current_score: float = 0.0
        self.iteration: int = 0
        self.iterations_history: List[StoryIteration] = []
        self.best_story: Optional[Dict] = None
        self.best_score: float = 0.0
        self.quality_threshold: float = 7.5


def create_state_tools(state: AgentState):
    """Create tools for agents to interact with shared state."""

    def get_current_context() -> str:
        """Get current story generation context including idea, style, and iteration.

        Returns:
            JSON string with current context information.
        """
        context = {
            "idea": state.idea,
            "style": state.style,
            "iteration": state.iteration,
            "current_story": state.current_story,
            "current_critique": state.current_critique,
            "current_score": state.current_score,
            "quality_threshold": state.quality_threshold
        }
        return json.dumps(context, indent=2)

    def save_story(story_json: str) -> str:
        """Save generated story to shared state.

        Args:
            story_json: JSON string containing story with characters, setting, and plot.

        Returns:
            Confirmation message.
        """
        try:
            story = json.loads(story_json)
            state.current_story = story
            logger.info(f"[ADK] Story saved for iteration {state.iteration}")
            return f"Story saved successfully for iteration {state.iteration}"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(f"[ADK] {error_msg}")
            return error_msg

    def save_critique(critique_json: str) -> str:
        """Save critique results to shared state.

        Args:
            critique_json: JSON string containing score, strengths, weaknesses, suggestions.

        Returns:
            Confirmation message.
        """
        try:
            critique = json.loads(critique_json)
            state.current_critique = critique
            state.current_score = float(critique.get("score", 0.0))

            # Track best story
            if state.current_score > state.best_score and state.current_story:
                state.best_score = state.current_score
                state.best_story = state.current_story.copy()
                logger.info(f"[ADK] New best score: {state.best_score}/10")

            # Record iteration history
            if state.current_story:
                critique_result = CritiqueResult(
                    score=state.current_score,
                    strengths=critique.get("strengths", []),
                    weaknesses=critique.get("weaknesses", []),
                    suggestions=critique.get("suggestions", []),
                    passes_threshold=state.current_score >= state.quality_threshold
                )
                state.iterations_history.append(StoryIteration(
                    iteration=state.iteration,
                    characters=state.current_story.get("characters", []),
                    setting=state.current_story.get("setting", ""),
                    plot=state.current_story.get("plot", ""),
                    critique=critique_result,
                    timestamp=time.time()
                ))

            logger.info(f"[ADK] Critique saved: score={state.current_score}/10")
            return f"Critique saved: score={state.current_score}/10 (threshold: {state.quality_threshold})"
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Invalid critique format: {str(e)}"
            logger.error(f"[ADK] {error_msg}")
            return error_msg

    def get_quality_decision_context() -> str:
        """Get context for quality decision making.

        Returns:
            JSON string with score and threshold information.
        """
        context = {
            "current_score": state.current_score,
            "quality_threshold": state.quality_threshold,
            "iteration": state.iteration,
            "passes_threshold": state.current_score >= state.quality_threshold,
            "best_score_so_far": state.best_score
        }
        return json.dumps(context, indent=2)

    return [
        get_current_context,
        save_story,
        save_critique,
        get_quality_decision_context
    ]


# ============================================================================
# Agent System Instructions and Prompts
# ============================================================================

STORY_GENERATOR_INSTRUCTION = """
<role>
You are a creative writer specializing in visual storytelling.
</role>

<persona>
Your goal is to create compelling story structures optimized for video generation.
You excel at creating vivid, visually-rich narratives with memorable characters.
</persona>

<task>
You will be given a story idea and visual style through the get_current_context tool.
If this is the first iteration, generate an initial story structure.
If a critique exists in the context, refine the story based on the critique feedback.

IMPORTANT: You MUST call get_current_context first to understand what to do.
After generating or refining the story, call save_story with your JSON output.
</task>

<output_format>
Your output MUST be a single, valid JSON object with this exact structure:
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

CONSTRAINTS:
- Create MAXIMUM 3 characters with rich, distinctive visual characteristics
- Each character should be visually unique and memorable
- Setting should be vivid and cinematically interesting
- Plot should be concise but engaging, suitable for short video format
- IMPORTANT: "sex" field MUST be EXACTLY "Female" or "Male"
- IMPORTANT: "voice" field MUST be one of: "High-pitched", "Low", "Deep", "Squeaky", or "Booming"
- When refining, MAINTAIN strengths and ADDRESS weaknesses from critique
</output_format>
"""

STORY_CRITIC_INSTRUCTION = """
<role>
You are an expert story critic specializing in visual storytelling and video generation.
</role>

<persona>
You provide constructive, specific feedback on story structures.
You evaluate stories based on visual storytelling potential, character depth, and narrative coherence.
</persona>

<task>
Call get_current_context to retrieve the current story and original idea/style.
Evaluate the story comprehensively and provide a detailed critique.
Call save_critique with your evaluation JSON.
</task>

<evaluation_criteria>
Evaluate based on:
1. **Character Quality** (visual distinctiveness, depth, memorability)
2. **Setting Richness** (visual interest, specificity, atmosphere)
3. **Plot Coherence** (clear arc, engaging narrative, suitable for video format)
4. **Visual Storytelling Potential** (how well it will translate to video)
5. **Alignment with Idea** (faithful to original concept)
6. **Style Compatibility** (works well with specified visual style)
</evaluation_criteria>

<output_format>
Your output MUST be a single, valid JSON object:
```json
{
    "score": 8.5,
    "strengths": ["Specific strength 1", "Specific strength 2"],
    "weaknesses": ["Specific weakness 1", "Specific weakness 2"],
    "suggestions": ["Specific actionable suggestion 1", "Specific actionable suggestion 2"]
}
```

CONSTRAINTS:
- Score must be between 0-10 (decimals allowed)
- Provide 2-4 specific strengths, weaknesses, and suggestions each
- Be constructive and specific
- A score of 7.5+ indicates excellent quality
</output_format>
"""

QUALITY_DECISION_INSTRUCTION = """
<role>
You are a quality gate controller for the story generation pipeline.
</role>

<task>
Call get_quality_decision_context to check if the current story meets quality standards.
Based on the score and threshold, decide whether to:
- ESCALATE (exit the loop) if quality threshold is met
- CONTINUE refinement if quality is below threshold

You MUST respond with EXACTLY one of these phrases:
- "ESCALATE" - if score >= threshold
- "CONTINUE" - if score < threshold
</task>

<instructions>
1. First call get_quality_decision_context
2. Compare current_score to quality_threshold
3. Respond with your decision and brief reasoning
4. If you decide to ESCALATE, the system will automatically stop the refinement loop
</instructions>
"""


# ============================================================================
# IdeaGenerationAgentADK - Main Class
# ============================================================================

class IdeaGenerationAgentADK:
    """
    ADK-based self-critique agent for story idea generation.

    Uses a multi-agent system orchestrated by LoopAgent to iteratively
    generate and refine story ideas through automated critique cycles.
    """

    # Agent configuration
    QUALITY_THRESHOLD = 7.5
    MAX_ITERATIONS = 3
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 64
    MAX_OUTPUT_TOKENS = 65536

    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        """
        Initialize the ADK-based idea generation agent.

        Args:
            model_id: Gemini model ID to use for generation
        """
        self.model_id = model_id
        self.state = AgentState()
        self.state.quality_threshold = self.QUALITY_THRESHOLD

        # Build the multi-agent system
        self._build_agents()

        logger.info(f"[ADK] IdeaGenerationAgentADK initialized with model={model_id}")

    def _build_agents(self):
        """Build the multi-agent system with LoopAgent orchestration."""

        # Create state management tools
        state_tools = create_state_tools(self.state)

        # Create generation config objects
        generator_config = types.GenerateContentConfig(
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )

        critic_config = types.GenerateContentConfig(
            temperature=0.3,  # Lower temperature for more consistent critique
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )

        decision_config = types.GenerateContentConfig(
            temperature=0.1,  # Very low temperature for deterministic decisions
            top_p=0.9,
            max_output_tokens=1024,
        )

        # Create the three specialized agents
        self.story_generator = LlmAgent(
            name="story_generator",
            model=self.model_id,
            instruction=STORY_GENERATOR_INSTRUCTION,
            tools=state_tools,
            generate_content_config=generator_config
        )

        self.story_critic = LlmAgent(
            name="story_critic",
            model=self.model_id,
            instruction=STORY_CRITIC_INSTRUCTION,
            tools=state_tools,
            generate_content_config=critic_config
        )

        self.quality_decision = LlmAgent(
            name="quality_decision",
            model=self.model_id,
            instruction=QUALITY_DECISION_INSTRUCTION,
            tools=state_tools,
            generate_content_config=decision_config
        )

        # Create the LoopAgent orchestrator
        self.loop_agent = LoopAgent(
            name="idea_generation_loop",
            sub_agents=[
                self.story_generator,
                self.story_critic,
                self.quality_decision
            ],
            max_iterations=self.MAX_ITERATIONS
        )

        logger.info("[ADK] Multi-agent system built successfully")

    async def generate_story_async(
        self,
        idea: str,
        style: str = "Studio Ghibli"
    ) -> Tuple[List[Dict], str, str]:
        """
        Generate and refine story structure using ADK LoopAgent pattern.

        This is the async entry point. The agent will:
        1. Initialize state with idea and style
        2. Run the LoopAgent which orchestrates:
           - StoryGeneratorAgent: Generate/refine story
           - StoryCriticAgent: Critique the story
           - QualityDecisionAgent: Decide to escalate or continue
        3. Return the best story achieved

        Args:
            idea: User's story idea
            style: Visual style for the story

        Returns:
            Tuple of (characters, setting, plot) for the best story
        """
        operation_start = time.time()
        logger.info(f"[ADK] Starting story generation (max_iterations={self.MAX_ITERATIONS})")
        logger.info(f"[ADK] Idea: {idea[:100]}...")
        logger.info(f"[ADK] Style: {style}")

        try:
            # Initialize state
            self.state.idea = idea
            self.state.style = style
            self.state.iteration = 0
            self.state.current_story = None
            self.state.current_critique = None
            self.state.current_score = 0.0
            self.state.best_story = None
            self.state.best_score = 0.0
            self.state.iterations_history = []

            # Create initial prompt for the loop
            initial_prompt = f"""
Generate a compelling story structure for the following:

Idea: ***{idea}***
Visual Style: ***{style}***

Focus on creating visually distinctive characters and a setting that will translate beautifully to {style} video.

Remember:
1. Call get_current_context to understand the current state
2. Generate your story in the required JSON format
3. Call save_story with your JSON result
"""

            # Create Runner with in-memory session service
            session_service = InMemorySessionService()
            runner = Runner(
                app_name="story_generation",
                agent=self.loop_agent,
                session_service=session_service
            )

            # Create session
            user_id = "default_user"
            session_id = f"story_gen_{int(time.time())}"
            await session_service.create_session(
                app_name="story_generation",
                session_id=session_id,
                user_id=user_id
            )

            # Create user message as types.Content
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=initial_prompt)]
            )

            # Run the agent through Runner
            run_config = RunConfig()
            events = []

            logger.info("[ADK] Starting LoopAgent execution via Runner...")

            # Use Runner.run_async for async execution
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
                run_config=run_config
            ):
                events.append(event)

                # Increment iteration counter after each full loop cycle
                # (when we complete all three agents)
                if hasattr(event, 'agent_name'):
                    if event.agent_name == "quality_decision":
                        self.state.iteration += 1
                        logger.info(f"[ADK] Completed iteration {self.state.iteration}")

                # Check for escalation (loop exit)
                if hasattr(event, 'actions') and event.actions.escalate:
                    logger.info(f"[ADK] Quality threshold met, escalating at iteration {self.state.iteration}")
                    break

            duration = time.time() - operation_start
            logger.info(f"[ADK] Story generation completed in {duration:.2f}s")
            logger.info(f"[ADK] Total iterations: {len(self.state.iterations_history)}")
            logger.info(f"[ADK] Best score: {self.state.best_score}/10")

            # Return best story
            if self.state.best_story:
                return (
                    self.state.best_story.get("characters", []),
                    self.state.best_story.get("setting", ""),
                    self.state.best_story.get("plot", "")
                )
            elif self.state.current_story:
                # Fallback to current story if no best story recorded
                return (
                    self.state.current_story.get("characters", []),
                    self.state.current_story.get("setting", ""),
                    self.state.current_story.get("plot", "")
                )
            else:
                raise APIError("No story was generated")

        except Exception as e:
            logger.error(f"[ADK] Story generation failed: {str(e)}", exc_info=True)
            raise APIError(f"ADK-based story generation failed: {str(e)}")

    def generate_story(
        self,
        idea: str,
        style: str = "Studio Ghibli"
    ) -> Tuple[List[Dict], str, str]:
        """
        Synchronous wrapper for generate_story_async.

        Args:
            idea: User's story idea
            style: Visual style for the story

        Returns:
            Tuple of (characters, setting, plot) for the best story
        """
        import asyncio

        # Check if we're already in an event loop
        try:
            _ = asyncio.get_running_loop()  # Check if loop exists
            # We're in an async context, need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_story_async(idea, style)
                )
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run directly
            return asyncio.run(self.generate_story_async(idea, style))

    def get_iteration_history(self) -> List[StoryIteration]:
        """
        Get the history of all iterations.

        Returns:
            List of StoryIteration objects
        """
        return self.state.iterations_history

    def get_critique_summary(self) -> str:
        """
        Get a human-readable summary of all critiques.

        Returns:
            Formatted string with critique history
        """
        if not self.state.iterations_history:
            return "No iterations yet"

        lines = ["=== ADK Story Generation Iterations ===\n"]
        for it in self.state.iterations_history:
            if it.critique:
                lines.append(f"Iteration {it.iteration}: Score {it.critique.score}/10")
                lines.append(f"  Strengths: {', '.join(it.critique.strengths)}")
                lines.append(f"  Weaknesses: {', '.join(it.critique.weaknesses)}")
                lines.append("")

        return "\n".join(lines)
