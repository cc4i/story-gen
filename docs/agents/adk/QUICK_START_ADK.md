# Quick Start: Using the ADK Agent

## 🚀 The New UI Toggle

When you launch the app (`python main.py`), you'll now see **two checkboxes** in the "✨ The Spark" tab:

```
┌─────────────────────────────────────────────────────────────┐
│ ✨ The Spark                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ What's the Idea:                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Your story idea here...]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Style: [Studio Ghibli ▼]                                    │
│                                                             │
│ ☑ 🤖 Use AI Agent (Self-Critique & Refinement)              │
│   Enable automatic story improvement through iterative      │
│   refinement                                                │
│                                                             │
│ ☑ 🚀 Use Google ADK Agent (Advanced Multi-Agent System)     │
│   Enable ADK-based LoopAgent with specialized sub-agents    │
│   for higher quality results                                │
│                                                             │
│ [Generate Random Idea]  [Generate Story]                    │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Agent Selection Guide

### Option 1: ADK Agent (Recommended) ⭐
**When**: Default choice for best quality
**Checkboxes**:
- ✅ Use AI Agent
- ✅ Use Google ADK Agent

**What happens**:
- Uses `IdeaGenerationAgentADK`
- 3 specialized sub-agents (Generator, Critic, Decision)
- LoopAgent orchestration
- Iterative refinement (up to 3 iterations)
- Quality threshold: 7.5/10
- Average scores: 9.2-9.8/10
- Duration: ~2 minutes

**Best for**:
- Production-quality stories
- Important projects
- When you want the highest quality output
- When you have time for 2-minute generation

---

### Option 2: Original Agent
**When**: Want agent features with simpler implementation
**Checkboxes**:
- ✅ Use AI Agent
- ❌ Use Google ADK Agent

**What happens**:
- Uses original `IdeaGenerationAgent`
- Single agent with manual loop
- Iterative refinement (up to 3 iterations)
- Quality threshold: 7.5/10
- Lighter dependencies
- Duration: ~2 minutes

**Best for**:
- Testing and development
- When you prefer simpler architecture
- When ADK dependencies are unavailable

---

### Option 3: No Agent (Fastest)
**When**: Need quick results
**Checkboxes**:
- ❌ Use AI Agent
- (ADK checkbox hidden)

**What happens**:
- Single LLM call
- No refinement
- No quality checks
- Duration: ~10-20 seconds

**Best for**:
- Quick prototyping
- Draft ideas
- When speed is more important than quality

---

## 🎬 Example Workflow

### 1. Start the App
```bash
python main.py
```

### 2. Navigate to "✨ The Spark" Tab

### 3. Enter Your Idea
```
A young robot discovers emotions while exploring an abandoned garden
```

### 4. Choose Your Style
```
Studio Ghibli
```

### 5. Select Agent Mode (Default: ADK)
- Keep both checkboxes **checked** ✅

### 6. Click "Generate Story"

### 7. Watch the Magic Happen
You'll see in the logs:
```
[abc123] Generating story, use_agent=True, use_adk=True, style=Studio Ghibli
[abc123] Using IdeaGenerationAgentADK (Google ADK-based)
[ADK] Starting story generation (max_iterations=3)
[ADK] Starting LoopAgent execution via Runner...
[ADK] Story saved for iteration 0
[ADK] New best score: 9.2/10
[ADK] Critique saved: score=9.2/10
[ADK] Story generation completed in 115.70s
[ADK] Total iterations: 3
[ADK] Best score: 9.5/10
```

### 8. Review Results
The app will show:
- Generated characters with detailed descriptions
- Rich setting description
- Engaging plot
- Character images automatically generated

---

## 🔍 How to Know Which Agent Is Running

### Check the Logs

**ADK Agent Running:**
```
✓ Using IdeaGenerationAgentADK (Google ADK-based)
✓ [ADK] Starting story generation
✓ [ADK] Starting LoopAgent execution via Runner
```

**Original Agent Running:**
```
✓ Using IdeaGenerationAgent (original)
✓ [Agent] Starting story generation
```

**No Agent:**
```
✓ Using traditional single-shot generation
```

---

## 💡 Tips

### 1. Quality vs Speed
- **Need best quality?** → Use ADK Agent (default)
- **Need fast results?** → Disable agents
- **Middle ground?** → Use Original Agent

### 2. When ADK Checkbox Disappears
The ADK checkbox automatically hides when you uncheck "Use AI Agent" since ADK is only relevant when using agents.

### 3. First Time Using ADK?
The first run might take slightly longer as dependencies load. Subsequent runs are faster.

### 4. Monitoring Progress
Watch the terminal/logs to see:
- Current iteration (1, 2, or 3)
- Scores for each iteration
- Final best score achieved

### 5. Comparing Agents
Want to compare outputs? Run the comparison script:
```bash
python example_adk_comparison.py
```

---

## 🛠️ Troubleshooting

### ADK Checkbox Not Showing
- Make sure "Use AI Agent" is checked
- The ADK checkbox only appears when agents are enabled

### Generation Taking Long Time
- This is normal for agent-based generation
- ADK agent makes multiple LLM calls for quality
- Expect ~2 minutes for full refinement cycle

### Want Faster Generation?
1. Uncheck both checkboxes for single-shot mode (~20 seconds)
2. Or use the original agent instead of ADK

### Errors During Generation
- Check logs for specific error messages
- Ensure `google-adk` is installed: `uv pip install google-adk`
- Verify API keys are set in `.env` file

---

## 📊 Quality Comparison

Based on test results:

| Metric | No Agent | Original Agent | ADK Agent |
|--------|----------|----------------|-----------|
| **Speed** | ⚡⚡⚡ ~20s | ⚡ ~120s | ⚡ ~120s |
| **Quality** | ⭐⭐ 6-7/10 | ⭐⭐⭐ 7-9/10 | ⭐⭐⭐⭐ 9-10/10 |
| **Iterations** | 0 | 1-3 | 1-3 |
| **Refinement** | ❌ None | ✅ Self-critique | ✅ Multi-agent |
| **Modularity** | N/A | ⭐⭐ Moderate | ⭐⭐⭐ Excellent |
| **Observability** | ⭐ Basic logs | ⭐⭐ Agent logs | ⭐⭐⭐ ADK events |

---

## 🎯 Recommended Settings

### For Production
```
✅ Use AI Agent
✅ Use Google ADK Agent
Style: Studio Ghibli (or your preference)
```

### For Development/Testing
```
✅ Use AI Agent
❌ Use Google ADK Agent
Style: Studio Ghibli
```

### For Quick Prototypes
```
❌ Use AI Agent
(ADK hidden)
Style: Any
```

---

## 🚀 What's Next?

After generating your story:
1. **Review** characters, setting, and plot
2. **Adjust** character count if needed (will regenerate)
3. **Generate** character images (automatic)
4. **Develop** full scene breakdown (Tab 2: "🎭 The Cast")
5. **Create** videos from scenes (Tab 3: "🎬 The Shoot")

---

**Ready to create amazing stories?** Just check both boxes and click "Generate Story"! 🎉
