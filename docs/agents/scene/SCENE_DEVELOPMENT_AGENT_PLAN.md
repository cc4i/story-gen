# Scene Development Agent Plan
## ADK-Based Multi-Agent System for "The Cast" → "The Shoot"

---

## 1. Current Workflow Analysis

### Current Implementation (`developing_story`)

**Input:**
- Characters (names, descriptions, voices, sex)
- Setting
- Plot
- Number of scenes (1-12)
- Duration per scene (5-8s)
- Visual style

**Process:**
1. Single LLM call with `develop_story_prompt`
2. Generates JSON with scene breakdown
3. Generates images for each scene (with character references)
4. Saves prompts and scripts

**Output Per Scene:**
```json
{
  "scene_number": 1,
  "location": "Physical environment description",
  "atmosphere": "Mood, time of day, weather",
  "characters": ["Character names in scene"],
  "dialogue": [{"character": "Name", "line": "Text"}],
  "key_actions": ["Step-by-step actions"],
  "key_visual_focus": "Hero shot description",
  "sound_design": "Audio description",
  "style": "Visual style"
}
```

### Issues with Current Approach

1. ❌ **No Quality Validation**: Single-shot generation, no refinement
2. ❌ **No Visual Continuity**: Doesn't check consistency across scenes
3. ❌ **No Pacing Analysis**: Might have uneven pacing
4. ❌ **No Character Consistency**: Characters might be inconsistent across scenes
5. ❌ **No Narrative Flow**: Doesn't validate scene-to-scene transitions
6. ❌ **No Technical Validation**: Doesn't check if scenes fit duration constraints

---

## 2. Proposed ADK Architecture

### Multi-Agent System Design

```
SceneDevelopmentAgentADK
└── LoopAgent (max_iterations=3, quality_threshold=8.0)
    ├── ScenePlannerAgent (LlmAgent)
    │   └── Plans overall scene structure and pacing
    │
    ├── SceneDeveloperAgent (LlmAgent)
    │   └── Develops detailed scene breakdowns
    │
    ├── VisualContinuityAgent (LlmAgent)
    │   └── Ensures visual consistency across scenes
    │
    ├── NarrativeFlowAgent (LlmAgent)
    │   └── Validates scene-to-scene transitions
    │
    ├── SceneCriticAgent (LlmAgent)
    │   └── Evaluates overall quality (0-10 score)
    │
    └── QualityDecisionAgent (LlmAgent)
        └── Escalates if score >= 8.0 or refines
```

### Agent Responsibilities

#### 1. **ScenePlannerAgent**
**Purpose**: Create high-level scene structure and pacing

**Responsibilities**:
- Divide story into appropriate number of scenes
- Plan pacing (intro, rising action, climax, resolution)
- Allocate duration to each scene type
- Identify key story beats per scene

**Output**:
```json
{
  "scene_plan": [
    {
      "scene_number": 1,
      "story_beat": "Introduction",
      "pacing_weight": "slow",
      "narrative_purpose": "Establish setting and protagonist",
      "recommended_duration": 7
    }
  ],
  "overall_pacing": {
    "intro_scenes": [1, 2],
    "rising_action": [3, 4, 5],
    "climax": [6, 7],
    "resolution": [8, 9]
  }
}
```

#### 2. **SceneDeveloperAgent**
**Purpose**: Develop detailed scene descriptions

**Responsibilities**:
- Create detailed scene breakdowns based on plan
- Ensure characters are well-distributed
- Create rich visual descriptions
- Write compelling dialogue
- Design key actions and visual focus
- Respect duration constraints

**Output**: Full scene JSON (same as current format)

#### 3. **VisualContinuityAgent**
**Purpose**: Ensure visual consistency across scenes

**Responsibilities**:
- Check character appearance consistency
- Validate location continuity
- Ensure lighting/atmosphere transitions make sense
- Verify visual style consistency
- Check for jarring visual jumps

**Output**:
```json
{
  "visual_consistency_score": 8.5,
  "issues": [
    {
      "scene_pair": [3, 4],
      "issue": "Character outfit changes without explanation",
      "severity": "medium",
      "suggestion": "Add transition or maintain outfit consistency"
    }
  ],
  "continuity_summary": "Good overall, minor issues in scenes 3-4"
}
```

#### 4. **NarrativeFlowAgent**
**Purpose**: Validate story flow and transitions

**Responsibilities**:
- Check scene-to-scene narrative logic
- Validate character motivations across scenes
- Ensure plot progression makes sense
- Verify dialogue consistency
- Check pacing feels natural

**Output**:
```json
{
  "narrative_flow_score": 9.0,
  "transition_quality": [
    {"from": 1, "to": 2, "quality": "smooth", "score": 9},
    {"from": 2, "to": 3, "quality": "abrupt", "score": 6}
  ],
  "pacing_analysis": "Well-paced, builds tension naturally",
  "issues": ["Scene 2->3 transition needs smoothing"]
}
```

#### 5. **SceneCriticAgent**
**Purpose**: Comprehensive quality evaluation

**Responsibilities**:
- Score overall quality (0-10)
- Evaluate against 6 criteria:
  1. Visual Coherence (consistency)
  2. Narrative Flow (story logic)
  3. Character Consistency (behavior/appearance)
  4. Pacing Quality (timing and rhythm)
  5. Technical Feasibility (duration constraints)
  6. Style Alignment (matches requested style)
- Provide specific strengths and weaknesses
- Suggest actionable improvements

**Output**:
```json
{
  "overall_score": 8.5,
  "criteria_scores": {
    "visual_coherence": 9.0,
    "narrative_flow": 8.0,
    "character_consistency": 9.0,
    "pacing_quality": 8.5,
    "technical_feasibility": 8.0,
    "style_alignment": 9.0
  },
  "strengths": [
    "Excellent visual descriptions",
    "Characters are well-developed and consistent",
    "Strong narrative arc"
  ],
  "weaknesses": [
    "Scene 5 feels rushed given 5s duration",
    "Transition between scenes 7-8 is abrupt"
  ],
  "suggestions": [
    "Extend scene 5 to 7 seconds or simplify actions",
    "Add transitional element between scenes 7-8"
  ]
}
```

#### 6. **QualityDecisionAgent**
**Purpose**: Decide whether to escalate or continue refining

**Responsibilities**:
- Check if overall_score >= 8.0
- Consider iteration count
- Decide: ESCALATE or CONTINUE

**Output**: "ESCALATE" or "CONTINUE" with reasoning

---

## 3. State Management

### Shared State Container

```python
class SceneDevelopmentState:
    """Shared state for scene development collaboration."""

    # Input data
    characters: List[Dict]
    setting: str
    plot: str
    number_of_scenes: int
    duration_per_scene: int
    style: str

    # Generated data
    scene_plan: Optional[Dict]
    scenes: Optional[List[Dict]]

    # Quality tracking
    visual_continuity_check: Optional[Dict]
    narrative_flow_check: Optional[Dict]
    current_critique: Optional[Dict]
    current_score: float = 0.0

    # Iteration tracking
    iteration: int = 0
    iterations_history: List[SceneDevelopmentIteration] = []
    best_scenes: Optional[List[Dict]] = None
    best_score: float = 0.0

    # Configuration
    quality_threshold: float = 8.0
```

### Custom Tools

```python
def get_development_context() -> str:
    """Get current scene development context"""

def save_scene_plan(plan_json: str) -> str:
    """Save scene planning results"""

def save_scenes(scenes_json: str) -> str:
    """Save developed scenes"""

def save_visual_continuity_check(check_json: str) -> str:
    """Save visual continuity analysis"""

def save_narrative_flow_check(check_json: str) -> str:
    """Save narrative flow analysis"""

def save_critique(critique_json: str) -> str:
    """Save critique results"""

def get_quality_decision_context() -> str:
    """Get context for quality decision"""
```

---

## 4. Workflow

### Iteration Flow

```
Iteration N:
┌─────────────────────────────────────────────────┐
│ 1. ScenePlannerAgent                            │
│    - Reads: characters, setting, plot           │
│    - Creates: high-level scene plan             │
│    - Saves: scene_plan                          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. SceneDeveloperAgent                          │
│    - Reads: scene_plan, characters, setting     │
│    - Creates: detailed scene descriptions       │
│    - Saves: scenes                              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. VisualContinuityAgent                        │
│    - Reads: scenes                              │
│    - Analyzes: visual consistency               │
│    - Saves: visual_continuity_check             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 4. NarrativeFlowAgent                           │
│    - Reads: scenes, scene_plan                  │
│    - Analyzes: story flow and transitions       │
│    - Saves: narrative_flow_check                │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 5. SceneCriticAgent                             │
│    - Reads: everything                          │
│    - Evaluates: overall quality                 │
│    - Saves: critique + score                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 6. QualityDecisionAgent                         │
│    - Reads: score, threshold, iteration         │
│    - Decides: ESCALATE or CONTINUE              │
│    - Action: Exit loop or refine                │
└─────────────────────────────────────────────────┘
```

### Decision Logic

```python
if score >= 8.0:
    ESCALATE  # Exit loop, scenes are good enough
elif iteration >= 3:
    ESCALATE  # Max iterations reached, use best
else:
    CONTINUE  # Refine scenes based on critique
```

---

## 5. Quality Criteria

### Evaluation Dimensions

1. **Visual Coherence (20%)**
   - Character appearance consistency
   - Location continuity
   - Lighting/atmosphere transitions
   - Style consistency

2. **Narrative Flow (20%)**
   - Scene-to-scene logic
   - Character motivations
   - Plot progression
   - Dialogue consistency

3. **Character Consistency (15%)**
   - Personality alignment
   - Behavior consistency
   - Voice/dialogue patterns
   - Appearance across scenes

4. **Pacing Quality (20%)**
   - Rhythm and timing
   - Story beat distribution
   - Tension building
   - Scene length appropriateness

5. **Technical Feasibility (15%)**
   - Duration constraints respected
   - Actions fit timeframe
   - Complexity manageable
   - Video generation feasibility

6. **Style Alignment (10%)**
   - Matches requested style
   - Consistent aesthetic
   - Appropriate tone
   - Visual style keywords

---

## 6. Implementation Plan

### Phase 1: Core Agent Structure ✨
**Files to Create:**
- `agents/scene_development_agent_adk.py`
- `test_scene_development_adk.py`

**Components:**
1. `SceneDevelopmentState` class
2. Custom tools (6 functions)
3. Agent system instructions (6 agents)
4. `SceneDevelopmentAgentADK` main class
5. LoopAgent orchestration

**Estimated Lines**: ~800-1000 lines

### Phase 2: Agent Instructions 📝
**For Each Agent:**
- System instruction with role, persona, task
- Output format specifications
- Tool usage instructions
- Quality criteria definitions

**Estimated Lines**: ~400 lines (system instructions)

### Phase 3: Integration 🔌
**Files to Modify:**
- `handlers/story_handlers.py` - Add `use_scene_adk` parameter
- `ui/story_tab.py` - Add checkbox for scene ADK agent
- `main.py` - Wire up new checkbox

**Estimated Changes**: ~100 lines

### Phase 4: Testing & Documentation 🧪
**Files to Create:**
- `SCENE_DEVELOPMENT_AGENT_GUIDE.md`
- `test_scene_development_adk.py`
- `example_scene_comparison.py`

**Estimated Lines**: ~500 lines

---

## 7. Key Differences from Story Agent

| Aspect | Story Agent | Scene Development Agent |
|--------|-------------|-------------------------|
| **Input** | User idea + style | Characters + setting + plot |
| **Output** | Characters, setting, plot | Detailed scene breakdowns |
| **Agents** | 3 (Generator, Critic, Decision) | 6 (Planner, Developer, 2 Validators, Critic, Decision) |
| **Complexity** | Moderate | High |
| **Validation** | Content quality | Visual + narrative + technical |
| **Iterations** | Max 3 | Max 3 |
| **Threshold** | 7.5/10 | 8.0/10 (higher standard) |

---

## 8. Benefits of ADK Approach

### vs Current Single-Shot

1. ✅ **Quality Assurance**: Automatic validation and refinement
2. ✅ **Visual Consistency**: Dedicated agent for continuity
3. ✅ **Narrative Coherence**: Dedicated agent for flow
4. ✅ **Better Pacing**: Dedicated planning phase
5. ✅ **Higher Scores**: 8-9/10 vs 6-7/10
6. ✅ **Fewer Errors**: Catches issues before generation

### Production Benefits

1. 📈 **Better Video Quality**: More coherent scenes = better videos
2. 🎯 **Fewer Retakes**: Scenes work first time
3. ⚡ **Time Savings**: Less manual correction needed
4. 🎨 **Style Consistency**: Better adherence to visual style
5. 📊 **Quality Tracking**: Detailed metrics and history

---

## 9. Expected Performance

### Quality Metrics
- **Target Score**: 8.5-9.5/10 (vs current ~6-7/10)
- **Visual Consistency**: 90%+ (vs ~70%)
- **Narrative Flow**: Smooth transitions 95%+ (vs ~80%)
- **Character Consistency**: 95%+ (vs ~85%)

### Performance Metrics
- **Generation Time**: ~3-4 minutes (6 agents × 3 iterations)
- **Success Rate**: 95%+ (threshold met in 1-2 iterations)
- **Iterations**: Average 1.5-2 (most reach threshold early)

---

## 10. Example Output

### Input
```
Characters: ["Robot 734", "Lumina"]
Setting: "Abandoned garden"
Plot: "Robot discovers emotions"
Scenes: 6
Duration: 6s each
Style: "Studio Ghibli"
```

### Output (After ADK Processing)
```json
{
  "scene_plan": {...},
  "scenes": [
    {
      "scene_number": 1,
      "location": "Entrance of overgrown garden with rusted gates",
      "atmosphere": "Dawn, soft golden light filtering through leaves",
      "characters": ["Robot 734"],
      "dialogue": [],
      "key_actions": [
        "Robot 734 awakens, optical sensors flickering",
        "Slowly stands, brushing off moss",
        "Looks around in wonder at the garden"
      ],
      "key_visual_focus": "Robot's blue glowing eyes reflecting garden beauty",
      "sound_design": "Gentle mechanical whirring, birds chirping, wind in leaves",
      "style": "Studio Ghibli"
    },
    {...}
  ],
  "critique": {
    "overall_score": 9.2,
    "visual_coherence": 9.5,
    "narrative_flow": 9.0,
    "character_consistency": 9.5,
    "pacing_quality": 9.0,
    "technical_feasibility": 9.0,
    "style_alignment": 9.5
  }
}
```

---

## 11. Implementation Roadmap

### Week 1: Core Development
- [ ] Create `SceneDevelopmentAgentADK` class structure
- [ ] Implement state management and tools
- [ ] Write agent system instructions
- [ ] Build LoopAgent orchestration

### Week 2: Validation Agents
- [ ] Implement VisualContinuityAgent logic
- [ ] Implement NarrativeFlowAgent logic
- [ ] Test validation accuracy

### Week 3: Integration & Testing
- [ ] Integrate with UI
- [ ] Write comprehensive tests
- [ ] Performance optimization
- [ ] Documentation

### Week 4: Polish & Launch
- [ ] User testing
- [ ] Bug fixes
- [ ] Final documentation
- [ ] Launch! 🚀

---

## 12. Success Criteria

✅ **Quality**: Average score 8.5+/10
✅ **Consistency**: Visual continuity 90%+
✅ **Performance**: Generation time < 5 minutes
✅ **Reliability**: Success rate 95%+
✅ **User Satisfaction**: Better than current approach
✅ **Integration**: Seamless UI experience

---

## 13. Next Steps

1. **Get Approval**: Review this plan
2. **Prototype**: Build minimal viable agent
3. **Test**: Validate with sample stories
4. **Iterate**: Refine based on results
5. **Deploy**: Integrate into main app

---

**Ready to build this?** This will be an even more sophisticated multi-agent system than the story agent! 🚀

---

**Status**: 📋 Planning Complete - Awaiting Approval
**Date**: October 24, 2025
**Complexity**: High (6 agents, complex validation)
**Estimated Effort**: 2-3 weeks full implementation
