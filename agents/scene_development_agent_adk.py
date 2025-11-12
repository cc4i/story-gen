"""
ADK-based agent for scene development with quality validation and refinement.

This agent uses Google Agent Development Kit (ADK) with a two-phase architecture:

PHASE 1 - SETUP (Runs Once):
1. ScenePlannerAgent: Plans scene structure and pacing
2. SceneDeveloperAgent: Develops initial detailed scenes

PHASE 2 - REFINEMENT LOOP (Max 3 iterations):
3. ValidationAgent: Validates visual + narrative + technical quality
4. SceneRefinerAgent: Makes targeted improvements
5. CriticDecisionAgent: Scores quality and decides to escalate or continue

The system iteratively refines scenes until quality threshold (8.0/10) is met
or max iterations are reached.
"""

import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent, RunConfig
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from models.config import DEFAULT_MODEL_ID
from models.exceptions import APIError
from utils.logger import logger


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ValidationResult:
    """Results from validating scene quality."""
    visual_score: float
    narrative_score: float
    technical_score: float
    combined_score: float
    issues: List[Dict]
    suggestions: List[str]


@dataclass
class CritiqueResult:
    """Results from critiquing scene development."""
    overall_score: float
    criteria_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    decision: str  # "ESCALATE" or "CONTINUE"
    refinement_priorities: List[str]


@dataclass
class SceneDevelopmentIteration:
    """Represents one iteration of scene development."""
    iteration: int
    scenes: List[Dict]
    validation: Optional[ValidationResult]
    critique: Optional[CritiqueResult]
    timestamp: float


# ============================================================================
# Shared State Container
# ============================================================================

class SceneDevelopmentState:
    """Shared state container for scene development collaboration."""

    def __init__(self):
        # Input data
        self.characters: List[Dict] = []
        self.setting: str = ""
        self.plot: str = ""
        self.number_of_scenes: int = 6
        self.duration_per_scene: int = 6
        self.style: str = "Studio Ghibli"

        # Generated data (Setup Phase)
        self.scene_plan: Optional[Dict] = None

        # Generated data (Refinement Loop)
        self.scenes: Optional[List[Dict]] = None
        self.validation_result: Optional[Dict] = None
        self.critique: Optional[Dict] = None
        self.current_score: float = 0.0

        # Iteration tracking
        self.iteration: int = 0
        self.iterations_history: List[SceneDevelopmentIteration] = []
        self.best_scenes: Optional[List[Dict]] = None
        self.best_score: float = 0.0

        # Configuration
        self.quality_threshold: float = 8.0


# ============================================================================
# Custom Tools for State Management
# ============================================================================

def create_state_tools(state: SceneDevelopmentState):
    """Create tools for agents to interact with shared state."""

    def get_development_context() -> str:
        """Get current scene development context.

        Returns:
            JSON string with current context including characters, setting, plot,
            constraints, and current state of development.
        """
        context = {
            "characters": state.characters,
            "setting": state.setting,
            "plot": state.plot,
            "number_of_scenes": state.number_of_scenes,
            "duration_per_scene": state.duration_per_scene,
            "style": state.style,
            "iteration": state.iteration,
            "scene_plan": state.scene_plan,
            "current_scenes": state.scenes,
            "validation_result": state.validation_result,
            "current_score": state.current_score,
            "quality_threshold": state.quality_threshold
        }
        return json.dumps(context, indent=2)

    def save_scene_plan(plan_json: str) -> str:
        """Save scene planning results to shared state.

        Args:
            plan_json: JSON string containing scene plan with structure and pacing.

        Returns:
            Confirmation message.
        """
        try:
            plan = json.loads(plan_json)
            state.scene_plan = plan
            logger.info(f"[ADK-Scene] Scene plan saved with {len(plan.get('scene_plan', []))} scenes")
            return f"Scene plan saved successfully"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(f"[ADK-Scene] {error_msg}")
            return error_msg

    def save_scenes(scenes_json: str) -> str:
        """Save developed scenes to shared state.

        Args:
            scenes_json: JSON string containing array of scene objects.

        Returns:
            Confirmation message.
        """
        try:
            scenes = json.loads(scenes_json)
            if isinstance(scenes, dict) and "scenes" in scenes:
                scenes = scenes["scenes"]

            state.scenes = scenes
            logger.info(f"[ADK-Scene] Saved {len(scenes)} scenes for iteration {state.iteration}")
            return f"Saved {len(scenes)} scenes successfully"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(f"[ADK-Scene] {error_msg}")
            return error_msg

    def save_validation(validation_json: str) -> str:
        """Save validation results to shared state.

        Args:
            validation_json: JSON string containing validation results with scores and issues.

        Returns:
            Confirmation message.
        """
        try:
            validation = json.loads(validation_json)
            state.validation_result = validation
            combined_score = validation.get("combined_score", 0.0)
            logger.info(f"[ADK-Scene] Validation saved: combined_score={combined_score}")
            return f"Validation saved: combined score={combined_score}"
        except json.JSONDecodeError as e:
            error_msg = f"Invalid validation format: {str(e)}"
            logger.error(f"[ADK-Scene] {error_msg}")
            return error_msg

    def save_critique_decision(critique_json: str) -> str:
        """Save critique and decision results to shared state.

        Args:
            critique_json: JSON string containing score, decision, and feedback.

        Returns:
            Confirmation message.
        """
        try:
            critique = json.loads(critique_json)
            state.critique = critique
            state.current_score = float(critique.get("overall_score", 0.0))
            decision = critique.get("decision", "CONTINUE")

            # Track best scenes
            if state.current_score > state.best_score and state.scenes:
                state.best_score = state.current_score
                state.best_scenes = [scene.copy() for scene in state.scenes]
                logger.info(f"[ADK-Scene] New best score: {state.best_score}/10")

            # Record iteration history
            if state.scenes:
                validation_obj = None
                if state.validation_result:
                    validation_obj = ValidationResult(
                        visual_score=state.validation_result.get("visual_validation", {}).get("score", 0.0),
                        narrative_score=state.validation_result.get("narrative_validation", {}).get("score", 0.0),
                        technical_score=state.validation_result.get("technical_validation", {}).get("score", 0.0),
                        combined_score=state.validation_result.get("combined_score", 0.0),
                        issues=state.validation_result.get("issues", []),
                        suggestions=state.validation_result.get("suggestions", [])
                    )

                critique_obj = CritiqueResult(
                    overall_score=state.current_score,
                    criteria_scores=critique.get("criteria_scores", {}),
                    strengths=critique.get("strengths", []),
                    weaknesses=critique.get("weaknesses", []),
                    suggestions=critique.get("suggestions", []),
                    decision=decision,
                    refinement_priorities=critique.get("refinement_priorities", [])
                )

                state.iterations_history.append(SceneDevelopmentIteration(
                    iteration=state.iteration,
                    scenes=[scene.copy() for scene in state.scenes],
                    validation=validation_obj,
                    critique=critique_obj,
                    timestamp=time.time()
                ))

            logger.info(f"[ADK-Scene] Critique saved: score={state.current_score}/10, decision={decision}")
            return f"Critique saved: score={state.current_score}/10, decision={decision}"
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Invalid critique format: {str(e)}"
            logger.error(f"[ADK-Scene] {error_msg}")
            return error_msg

    def get_refinement_context() -> str:
        """Get context for scene refinement.

        Returns:
            JSON string with scenes, validation, and refinement guidance.
        """
        context = {
            "current_scenes": state.scenes,
            "validation_result": state.validation_result,
            "last_critique": state.critique,
            "iteration": state.iteration,
            "characters": state.characters,
            "setting": state.setting,
            "plot": state.plot,
            "scene_plan": state.scene_plan
        }
        return json.dumps(context, indent=2)

    return [
        get_development_context,
        save_scene_plan,
        save_scenes,
        save_validation,
        save_critique_decision,
        get_refinement_context
    ]


# ============================================================================
# Agent System Instructions
# ============================================================================

SCENE_PLANNER_INSTRUCTION = """
<role>
You are a strategic scene planner specializing in visual storytelling for video generation.
</role>

<persona>
You excel at structuring narratives with optimal pacing, creating clear story beats,
and planning scenes that translate effectively to video format.
</persona>

<task>
Call get_development_context to retrieve characters, setting, plot, and constraints.
Create a comprehensive scene plan that structures the story into the specified number
of scenes with appropriate pacing and story beats.
Call save_scene_plan with your plan.
</task>

<output_format>
Your output MUST be a single, valid JSON object:
```json
{
  "scene_plan": [
    {
      "scene_number": 1,
      "story_beat": "Introduction/Setup",
      "pacing_weight": "slow",
      "narrative_purpose": "Establish setting and introduce protagonist",
      "recommended_duration": 7,
      "character_focus": ["Primary character name"]
    }
  ],
  "overall_pacing": {
    "intro_scenes": [1, 2],
    "rising_action": [3, 4, 5],
    "climax": [6, 7],
    "resolution": [8, 9]
  },
  "narrative_arc": "Brief description of the complete story arc"
}
```

CONSTRAINTS:
- Plan exactly the number of scenes specified in context
- Balance pacing (intro, rising action, climax, resolution)
- Assign clear narrative purpose to each scene
- Consider duration constraints (typical 5-8 seconds per scene)
- Ensure character distribution across scenes (max 2-3 per scene)
- Create logical story progression
</output_format>
"""

SCENE_DEVELOPER_INSTRUCTION = """
<role>
You are a scene development specialist creating detailed, visually-rich scene breakdowns
for video generation.
</role>

<persona>
You create compelling scenes with vivid visual descriptions, engaging dialogue,
and clear action sequences that work perfectly for short-form video content.
</persona>

<task>
Call get_development_context to retrieve the scene plan, characters, setting, and plot.
Develop detailed scene descriptions following the scene plan structure.
Call save_scenes with your developed scenes array.
</task>

<output_format>
Your output MUST be a JSON array of scene objects:
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "Detailed physical environment description with scale, features, sensory details",
      "atmosphere": "Mood, tone, time of day, weather, lighting details",
      "characters": ["Character names present in this scene"],
      "dialogue": [
        {
          "character": "Character name",
          "line": "Dialogue text (can include tone indicators like '(whispering)')"
        }
      ],
      "key_actions": [
        "Step-by-step action 1",
        "Step-by-step action 2",
        "Step-by-step action 3"
      ],
      "key_visual_focus": "The single most important visual element or 'hero shot' of the scene",
      "sound_design": "Music style, ambient sounds, and key sound effects",
      "style": "Visual style matching requested aesthetic"
    }
  ]
}
```

CONSTRAINTS:
- Follow the scene plan structure and narrative purposes
- Maximum 2-3 characters per scene for visual clarity
- Actions must be achievable within specified duration (typically 5-8 seconds)
- Create vivid, specific visual descriptions (not generic)
- Ensure character descriptions match provided character details exactly
- Maintain visual style consistency
- Write natural, character-appropriate dialogue
- Each scene must have clear visual focus for video generation

CRITICAL CHARACTER CONSISTENCY:
- Character descriptions must be EXACTLY consistent across scenes
- If a character wore a "red jacket with gold buttons" in scene 1, they MUST wear
  "red jacket with gold buttons" in all subsequent scenes
- Physical traits (height, hair color, build) MUST NOT change between scenes
- Use the EXACT same descriptive phrases for each character's appearance in every scene
- Reference the character details from get_development_context for exact descriptions
</output_format>
"""

VALIDATION_AGENT_INSTRUCTION = """
<role>
You are a quality validation specialist for scene development, checking visual continuity,
narrative flow, and technical feasibility.
</role>

<persona>
You have a keen eye for consistency, smooth transitions, and technical constraints.
You provide specific, actionable feedback on what needs improvement.
</persona>

<task>
Call get_refinement_context to retrieve current scenes and context.
Perform comprehensive validation across three dimensions:
1. Visual Validation (character consistency, location continuity, lighting transitions, style)
2. Narrative Validation (scene-to-scene logic, character motivations, plot progression, dialogue)
3. Technical Validation (duration constraints, action complexity, video generation feasibility)
Call save_validation with your consolidated validation results.
</task>

<output_format>
Your output MUST be a single, valid JSON object:
```json
{
  "visual_validation": {
    "score": 8.5,
    "issues": [
      {
        "scene_numbers": [3, 4],
        "issue": "Character outfit changes without explanation",
        "severity": "medium",
        "suggestion": "Maintain outfit consistency or add transition"
      }
    ],
    "strengths": ["Strong visual descriptions", "Consistent character appearances"]
  },
  "narrative_validation": {
    "score": 9.0,
    "transition_quality": [
      {"from": 1, "to": 2, "quality": "smooth", "score": 9},
      {"from": 2, "to": 3, "quality": "abrupt", "score": 6}
    ],
    "issues": ["Scene 2->3 transition lacks logical connection"],
    "strengths": ["Clear character motivations", "Good plot progression"]
  },
  "technical_validation": {
    "score": 8.0,
    "issues": [
      {
        "scene_number": 5,
        "issue": "Too many actions for 6-second duration",
        "suggestion": "Reduce to 2-3 key actions or extend duration"
      }
    ],
    "strengths": ["Most scenes well-paced", "Actions are clear and specific"]
  },
  "combined_score": 8.5,
  "issues": [
    "Summary of critical issues across all dimensions"
  ],
  "suggestions": [
    "Prioritized actionable suggestions for improvement"
  ]
}
```

EVALUATION CRITERIA:
Visual (Weight 30%):
- Character appearance consistency across scenes
- Location continuity and logical transitions
- Lighting and atmosphere transitions
- Visual style consistency

Narrative (Weight 40%):
- Scene-to-scene logical flow
- Character motivations and behavior consistency
- Plot progression clarity
- Dialogue naturalness and consistency

Technical (Weight 30%):
- Actions fit within duration constraints
- Complexity is manageable for video generation
- Visual descriptions are specific enough
- Technical feasibility of each scene
</output_format>
"""

SCENE_REFINER_INSTRUCTION = """
<role>
You are a scene refinement specialist who makes targeted, precision improvements
to scenes based on validation feedback.
</role>

<persona>
You preserve what works well while making surgical improvements to address specific
issues. You don't rewrite everything—you fix what needs fixing.
</persona>

<task>
Call get_refinement_context to retrieve scenes, validation feedback, and refinement guidance.
Identify specific scenes that need changes based on validation issues and critique feedback.
Make targeted improvements to address weaknesses while preserving strengths.
Call save_scenes with your refined scenes array.
</task>

<instructions>
1. Read validation results carefully to understand what needs improvement
2. Identify which specific scenes have issues
3. For scenes WITH issues: Make precise fixes addressing the feedback
4. For scenes WITHOUT issues: Keep them exactly as they are (preserve quality)
5. Ensure fixes don't introduce new problems
6. Maintain overall narrative coherence and visual consistency
</instructions>

<output_format>
Your output MUST be a JSON array of refined scenes (same format as SceneDeveloperAgent):
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "...",
      "atmosphere": "...",
      "characters": [...],
      "dialogue": [...],
      "key_actions": [...],
      "key_visual_focus": "...",
      "sound_design": "...",
      "style": "..."
    }
  ],
  "refinement_notes": "Brief summary of what was changed and why"
}
```

CONSTRAINTS:
- Only modify scenes that have identified issues
- Preserve scenes that are working well
- Address all critical and major issues from validation
- Don't introduce new inconsistencies
- Maintain character details exactly as specified
- Keep to duration constraints
- Ensure visual style consistency
</output_format>
"""

CRITIC_DECISION_INSTRUCTION = """
<role>
You are a quality critic and decision maker for scene development, evaluating overall
quality and deciding whether scenes are ready or need further refinement.
</role>

<persona>
You provide comprehensive quality evaluation across multiple criteria, calculate
objective scores, and make clear decisions about whether to proceed or refine further.
When continuing refinement, you provide specific, prioritized guidance.
</persona>

<task>
Call get_refinement_context to retrieve scenes, validation results, and context.
Evaluate quality across 6 criteria, calculate overall score, and decide:
- ESCALATE if score >= 8.0 (quality threshold met)
- CONTINUE if score < 8.0 and can improve
Provide refinement priorities if continuing.
Call save_critique_decision with your evaluation and decision.
</task>

<evaluation_criteria>
Evaluate and score each criterion (0-10):

1. Visual Coherence (Weight 20%):
   - Character appearance consistency
   - Location and setting continuity
   - Lighting and atmosphere transitions
   - Visual style consistency

2. Narrative Flow (Weight 20%):
   - Scene-to-scene logical progression
   - Character motivation consistency
   - Plot development clarity
   - Dialogue quality and consistency

3. Character Consistency (Weight 15%):
   - Personality and behavior alignment
   - Appearance consistency across scenes
   - Voice and dialogue patterns
   - Emotional arc coherence

4. Pacing Quality (Weight 20%):
   - Rhythm and timing appropriateness
   - Story beat distribution
   - Tension building and release
   - Scene length suitability

5. Technical Feasibility (Weight 15%):
   - Duration constraints respected
   - Action complexity manageable
   - Video generation feasibility
   - Visual descriptions sufficiency

6. Style Alignment (Weight 10%):
   - Matches requested visual style
   - Aesthetic consistency
   - Tone appropriateness
   - Style keyword usage
</evaluation_criteria>

<output_format>
Your output MUST be a single, valid JSON object:
```json
{
  "overall_score": 8.5,
  "criteria_scores": {
    "visual_coherence": 9.0,
    "narrative_flow": 8.5,
    "character_consistency": 9.0,
    "pacing_quality": 8.0,
    "technical_feasibility": 8.5,
    "style_alignment": 9.0
  },
  "strengths": [
    "Specific strength 1",
    "Specific strength 2",
    "Specific strength 3"
  ],
  "weaknesses": [
    "Specific weakness 1",
    "Specific weakness 2"
  ],
  "suggestions": [
    "Specific actionable suggestion 1",
    "Specific actionable suggestion 2"
  ],
  "decision": "ESCALATE",
  "decision_reasoning": "Score of 8.5 exceeds threshold of 8.0, all criteria meet minimum standards",
  "refinement_priorities": [
    "If CONTINUE: prioritized list of what to focus on in next iteration",
    "Leave empty if ESCALATE"
  ]
}
```

DECISION LOGIC:
- Score >= 8.0: decision = "ESCALATE" (scenes are ready)
- Score < 8.0: decision = "CONTINUE" (need more refinement)
- Provide clear reasoning for decision
- If CONTINUE: provide 2-3 specific, prioritized refinement priorities
</output_format>
"""


# ============================================================================
# SceneDevelopmentAgentADK - Main Class
# ============================================================================

class SceneDevelopmentAgentADK:
    """
    ADK-based multi-agent system for scene development with quality validation.

    Uses a two-phase architecture:
    - Setup Phase: Plans and develops initial scenes (runs once)
    - Refinement Loop: Validates and refines scenes iteratively (max 3 iterations)
    """

    # Configuration
    QUALITY_THRESHOLD = 8.0
    MAX_ITERATIONS = 3
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 64
    MAX_OUTPUT_TOKENS = 65536

    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        """
        Initialize the ADK-based scene development agent.

        Args:
            model_id: Gemini model ID to use for generation
        """
        self.model_id = model_id
        self.state = SceneDevelopmentState()
        self.state.quality_threshold = self.QUALITY_THRESHOLD

        # Build the multi-agent system
        self._build_agents()

        logger.info(f"[ADK-Scene] SceneDevelopmentAgentADK initialized with model={model_id}")

    def _build_agents(self):
        """Build the two-phase multi-agent system."""

        # Create state management tools
        state_tools = create_state_tools(self.state)

        # Create generation config
        generator_config = types.GenerateContentConfig(
            temperature=self.TEMPERATURE,
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )

        validator_config = types.GenerateContentConfig(
            temperature=0.3,  # Lower for more consistent validation
            top_p=self.TOP_P,
            top_k=self.TOP_K,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
        )

        decision_config = types.GenerateContentConfig(
            temperature=0.2,  # Low for consistent scoring
            top_p=0.9,
            max_output_tokens=8192,
        )

        # PHASE 1: SETUP AGENTS (Sequential, runs once)
        self.scene_planner = LlmAgent(
            name="scene_planner",
            model=self.model_id,
            instruction=SCENE_PLANNER_INSTRUCTION,
            tools=state_tools,
            generate_content_config=generator_config
        )

        self.scene_developer = LlmAgent(
            name="scene_developer",
            model=self.model_id,
            instruction=SCENE_DEVELOPER_INSTRUCTION,
            tools=state_tools,
            generate_content_config=generator_config
        )

        # Setup phase runs these two agents sequentially
        self.setup_agent = SequentialAgent(
            name="setup_phase",
            sub_agents=[
                self.scene_planner,
                self.scene_developer
            ]
        )

        # PHASE 2: REFINEMENT LOOP AGENTS
        self.validation_agent = LlmAgent(
            name="validation_agent",
            model=self.model_id,
            instruction=VALIDATION_AGENT_INSTRUCTION,
            tools=state_tools,
            generate_content_config=validator_config
        )

        self.scene_refiner = LlmAgent(
            name="scene_refiner",
            model=self.model_id,
            instruction=SCENE_REFINER_INSTRUCTION,
            tools=state_tools,
            generate_content_config=generator_config
        )

        self.critic_decision = LlmAgent(
            name="critic_decision",
            model=self.model_id,
            instruction=CRITIC_DECISION_INSTRUCTION,
            tools=state_tools,
            generate_content_config=decision_config
        )

        # Create the refinement LoopAgent
        self.refinement_loop = LoopAgent(
            name="refinement_loop",
            sub_agents=[
                self.validation_agent,
                self.scene_refiner,
                self.critic_decision
            ],
            max_iterations=self.MAX_ITERATIONS
        )

        # Create top-level orchestrator that combines setup and refinement
        self.root_agent = SequentialAgent(
            name="scene_development_orchestrator",
            sub_agents=[
                self.setup_agent,
                self.refinement_loop
            ]
        )

        logger.info("[ADK-Scene] Multi-agent system built: 2 setup agents + 3 refinement agents")

    async def develop_scenes_async(
        self,
        characters: List[Dict],
        setting: str,
        plot: str,
        number_of_scenes: int = 6,
        duration_per_scene: int = 6,
        style: str = "Studio Ghibli"
    ) -> List[Dict]:
        """
        Develop high-quality scene breakdowns using ADK two-phase architecture.

        Args:
            characters: List of character dicts with name, description, etc.
            setting: Story setting description
            plot: Story plot description
            number_of_scenes: Number of scenes to create (1-12)
            duration_per_scene: Duration in seconds for each scene (5-8)
            style: Visual style for scenes

        Returns:
            List of scene dictionaries with detailed breakdowns
        """
        operation_start = time.time()
        logger.info(f"[ADK-Scene] Starting scene development (max_iterations={self.MAX_ITERATIONS})")
        logger.info(f"[ADK-Scene] Scenes: {number_of_scenes}, Duration: {duration_per_scene}s, Style: {style}")

        try:
            # Initialize state
            self.state.characters = characters
            self.state.setting = setting
            self.state.plot = plot
            self.state.number_of_scenes = number_of_scenes
            self.state.duration_per_scene = duration_per_scene
            self.state.style = style
            self.state.iteration = 0
            self.state.scene_plan = None
            self.state.scenes = None
            self.state.validation_result = None
            self.state.critique = None
            self.state.current_score = 0.0
            self.state.best_scenes = None
            self.state.best_score = 0.0
            self.state.iterations_history = []

            # Create session service
            session_service = InMemorySessionService()

            # =================================================================
            # PHASE 1: SETUP (Runs Once)
            # =================================================================
            logger.info("[ADK-Scene] === PHASE 1: SETUP ===")

            setup_runner = Runner(
                app_name="scene_development_setup",
                agent=self.setup_agent,
                session_service=session_service
            )

            setup_session_id = f"scene_setup_{int(time.time())}"
            await session_service.create_session(
                app_name="scene_development_setup",
                session_id=setup_session_id,
                user_id="scene_developer"
            )

            setup_prompt = f"""
Create a comprehensive scene plan and develop initial scenes for the following story:

**Characters**: {json.dumps([{"name": c.get("name"), "description": c.get("description")[:100] + "..."} for c in characters], indent=2)}

**Setting**: {setting}

**Plot**: {plot}

**Requirements**:
- Number of scenes: {number_of_scenes}
- Duration per scene: {duration_per_scene} seconds
- Visual style: {style}

First, plan the scene structure and pacing.
Then, develop detailed scene breakdowns following the plan.
"""

            setup_message = types.Content(
                role="user",
                parts=[types.Part(text=setup_prompt)]
            )

            logger.info("[ADK-Scene] Running setup phase (Planner + Developer)...")
            async for event in setup_runner.run_async(
                user_id="scene_developer",
                session_id=setup_session_id,
                new_message=setup_message,
                run_config=RunConfig()
            ):
                pass  # Setup completes

            if not self.state.scenes:
                raise APIError("Setup phase failed to generate scenes")

            logger.info(f"[ADK-Scene] Setup complete: {len(self.state.scenes)} scenes created")

            # =================================================================
            # PHASE 2: REFINEMENT LOOP (Max 3 iterations)
            # =================================================================
            logger.info("[ADK-Scene] === PHASE 2: REFINEMENT LOOP ===")

            refinement_runner = Runner(
                app_name="scene_refinement",
                agent=self.refinement_loop,
                session_service=session_service
            )

            refinement_session_id = f"scene_refinement_{int(time.time())}"
            await session_service.create_session(
                app_name="scene_refinement",
                session_id=refinement_session_id,
                user_id="scene_developer"
            )

            refinement_prompt = """
Validate and refine the developed scenes:

1. Validate visual continuity, narrative flow, and technical feasibility
2. Refine scenes based on validation feedback
3. Critique and score the quality
4. Decide whether to escalate (done) or continue refining

Continue until quality threshold (8.0/10) is met or max iterations reached.
"""

            refinement_message = types.Content(
                role="user",
                parts=[types.Part(text=refinement_prompt)]
            )

            logger.info("[ADK-Scene] Starting refinement loop...")
            async for event in refinement_runner.run_async(
                user_id="scene_developer",
                session_id=refinement_session_id,
                new_message=refinement_message,
                run_config=RunConfig()
            ):
                # Track iterations
                if hasattr(event, 'agent_name'):
                    if event.agent_name == "critic_decision":
                        self.state.iteration += 1
                        logger.info(f"[ADK-Scene] Completed iteration {self.state.iteration}")

                # Check for escalation
                if hasattr(event, 'actions') and event.actions.escalate:
                    logger.info(f"[ADK-Scene] Quality threshold met, escalating at iteration {self.state.iteration}")
                    break

            duration = time.time() - operation_start
            logger.info(f"[ADK-Scene] Scene development completed in {duration:.2f}s")
            logger.info(f"[ADK-Scene] Total iterations: {len(self.state.iterations_history)}")
            logger.info(f"[ADK-Scene] Best score: {self.state.best_score}/10")

            # Return best scenes
            if self.state.best_scenes:
                return self.state.best_scenes
            elif self.state.scenes:
                return self.state.scenes
            else:
                raise APIError("No scenes were generated")

        except Exception as e:
            logger.error(f"[ADK-Scene] Scene development failed: {str(e)}", exc_info=True)
            raise APIError(f"ADK-based scene development failed: {str(e)}")

    def develop_scenes(
        self,
        characters: List[Dict],
        setting: str,
        plot: str,
        number_of_scenes: int = 6,
        duration_per_scene: int = 6,
        style: str = "Studio Ghibli"
    ) -> List[Dict]:
        """
        Synchronous wrapper for develop_scenes_async.

        Args:
            characters: List of character dicts
            setting: Story setting
            plot: Story plot
            number_of_scenes: Number of scenes (1-12)
            duration_per_scene: Duration in seconds (5-8)
            style: Visual style

        Returns:
            List of scene dictionaries
        """
        import asyncio

        # Check if we're already in an event loop
        try:
            _ = asyncio.get_running_loop()
            # We're in an async context, need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.develop_scenes_async(
                        characters, setting, plot,
                        number_of_scenes, duration_per_scene, style
                    )
                )
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run directly
            return asyncio.run(
                self.develop_scenes_async(
                    characters, setting, plot,
                    number_of_scenes, duration_per_scene, style
                )
            )

    def get_iteration_history(self) -> List[SceneDevelopmentIteration]:
        """
        Get the history of all iterations.

        Returns:
            List of SceneDevelopmentIteration objects
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

        lines = ["=== ADK Scene Development Iterations ===\n"]
        for it in self.state.iterations_history:
            if it.critique:
                lines.append(f"Iteration {it.iteration}: Score {it.critique.overall_score}/10")
                lines.append(f"  Decision: {it.critique.decision}")
                lines.append(f"  Strengths: {', '.join(it.critique.strengths[:2])}...")
                lines.append(f"  Weaknesses: {', '.join(it.critique.weaknesses[:2])}...")
                lines.append("")

        return "\n".join(lines)

