# AI Agent-Based Story Generation Guide

## Overview

The Story-Gen application now includes an **ADK-based self-critique agent** for automated story improvement. This agent uses an iterative refinement process to generate higher-quality story structures.

## How It Works

### Traditional Approach (Single-Shot)
```
User Idea → LLM → Characters + Setting + Plot
```

### Agent-Based Approach (Self-Critique)
```
User Idea → Generate → Critique → Refine → Quality Check → Best Result
                ↑                              ↓
                └──────────────────────────────┘
                    (Up to 3 iterations)
```

## The Self-Critique Pattern

The agent implements a three-phase cycle:

### 1. **Generation Phase**
- Creates initial story structure from user idea
- Generates characters, setting, and plot
- Optimized for visual storytelling and video generation

### 2. **Critique Phase**
Evaluates the story against 6 quality criteria:
- **Character Quality**: Visual distinctiveness, depth, memorability
- **Setting Richness**: Visual interest, specificity, atmosphere
- **Plot Coherence**: Clear narrative arc, engaging story
- **Visual Storytelling Potential**: How well it translates to video
- **Alignment with Idea**: Faithful to original concept
- **Style Compatibility**: Works well with chosen visual style

Outputs:
- **Score** (0-10): Overall quality score
- **Strengths**: What works well (preserve these)
- **Weaknesses**: What needs improvement
- **Suggestions**: Specific, actionable improvements

### 3. **Refinement Phase**
- Incorporates critique feedback
- Addresses weaknesses while preserving strengths
- Maintains core concept and character names
- Produces improved version

### Quality Threshold
- **Target Score**: 7.5/10
- **Max Iterations**: 3
- Agent stops when threshold is met or max iterations reached
- Returns the **best version** from all iterations

## Using the Agent

### In the UI

1. Navigate to **"✨ The Spark"** tab
2. Enter your story idea
3. Select visual style (Studio Ghibli, Anime, etc.)
4. **Toggle "🤖 Use AI Agent"** checkbox:
   - ✅ **Enabled** (default): Uses self-critique agent for automatic improvement
   - ⬜ **Disabled**: Uses traditional single-shot generation
5. Click "Generate story"

### Programmatic Usage

```python
from agents import IdeaGenerationAgent

# Initialize agent
agent = IdeaGenerationAgent(model_id="gemini-2.0-flash")

# Generate story with automatic refinement
characters, setting, plot = agent.generate_story(
    idea="Your story idea here",
    style="Studio Ghibli"
)

# View iteration history
print(agent.get_critique_summary())
```

### Handler Usage

```python
from handlers.story_handlers import generate_story

# With agent (recommended)
characters, setting, plot = generate_story(
    idea="Your idea",
    style="Studio Ghibli",
    use_agent=True  # Uses self-critique agent
)

# Without agent (traditional)
characters, setting, plot = generate_story(
    idea="Your idea",
    style="Studio Ghibli",
    use_agent=False  # Single LLM call
)
```

## Configuration

Edit `agents/idea_agent.py` to customize:

```python
class IdeaGenerationAgent:
    # Quality threshold (score out of 10)
    QUALITY_THRESHOLD = 7.5

    # Maximum refinement iterations
    MAX_ITERATIONS = 3

    # LLM parameters
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 64
    MAX_OUTPUT_TOKENS = 65536
```

## Benefits

### Automatic Improvement
- No manual revision needed
- Consistent quality across generations
- Learns from critique patterns

### Better Visual Storytelling
- Characters optimized for visual distinctiveness
- Settings rich in visual details
- Plots suitable for video format

### Transparency
- View all iterations and scores
- Understand what improved
- Access critique feedback

### Flexibility
- Can disable for faster generation
- Configurable quality standards
- Adjustable iteration limits

## Performance

| Metric | Single-Shot | Agent (3 iterations) |
|--------|-------------|----------------------|
| **Time** | ~5-10 seconds | ~20-40 seconds |
| **LLM Calls** | 1 | 2-6 (generate + critique pairs) |
| **Quality** | Variable | Consistently higher |
| **Token Usage** | ~2-4K | ~8-16K |

## Example Output

```
=== Story Generation Iterations ===

Iteration 1: Score 6.5/10
  Strengths: Clear protagonist, Magical realism element, Environmental theme
  Weaknesses: Generic character descriptions, Setting lacks visual specificity, Plot needs stronger conflict

Iteration 2: Score 7.8/10
  Strengths: Vivid character details, Atmospheric setting with Studio Ghibli aesthetic, Strong emotional arc
  Weaknesses: Minor pacing issue in third act

✓ Quality threshold met (score: 7.8 >= 7.5)
```

## Testing

Run the test script to verify the agent:

```bash
python test_agent.py
```

This will:
1. Generate a story using the agent
2. Display all iterations and scores
3. Show the final story structure
4. Print critique history

## Future Enhancements

Potential extensions for the agent system:

1. **Multi-Agent System**: Separate generator, critic, and refiner agents
2. **Scene Development Agent**: Apply same pattern to scene-by-scene development
3. **Image Prompt Agent**: Optimize image generation prompts through critique
4. **Video Prompt Agent**: Refine Veo prompts for better video quality
5. **Custom Criteria**: User-defined quality metrics
6. **Learning from Feedback**: Store and learn from user ratings

## Architecture

```
agents/
├── __init__.py              # Agent module exports
└── idea_agent.py            # IdeaGenerationAgent implementation

handlers/
└── story_handlers.py        # Updated to use agent

ui/
└── idea_tab.py              # UI with agent toggle

main.py                      # Gradio app integration
```

## Troubleshooting

### Agent takes too long
- Reduce `MAX_ITERATIONS` in `idea_agent.py`
- Increase `QUALITY_THRESHOLD` to accept lower scores faster

### Quality not improving
- Check logs for critique feedback patterns
- Adjust `TEMPERATURE` for more creative refinements
- Review prompt templates in agent code

### API errors
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota limits
- Review error logs for specific issues

## Related Files

- **Agent Implementation**: `agents/idea_agent.py`
- **Handler Integration**: `handlers/story_handlers.py`
- **UI Component**: `ui/idea_tab.py`
- **Main App**: `main.py`
- **Test Script**: `test_agent.py`

---

**Questions or issues?** Check the logs for detailed agent execution traces including scores, feedback, and iteration details.
