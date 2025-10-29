# UI Update: ADK Agent Toggle

## Summary

Added a user-facing checkbox in the Gradio UI to allow users to choose between the ADK-based agent and the original agent.

## Changes Made

### 1. Updated `ui/idea_tab.py`

**Added:**
```python
cb_use_adk = gr.Checkbox(
    label="🚀 Use Google ADK Agent (Advanced Multi-Agent System)",
    value=True,
    info="Enable ADK-based LoopAgent with specialized sub-agents for higher quality results"
)
```

**Returns**: Now includes `cb_use_adk` in the return tuple.

### 2. Updated `main.py`

**Line 97**: Added `cb_use_adk` to unpacking from `idea_tab()`
```python
ta_idea, dd_style, cb_use_agent, cb_use_adk, btn_random_idea, btn_generate_story = idea_tab()
```

**Added UI Interaction**: ADK checkbox automatically hides/disables when agent checkbox is unchecked
```python
def toggle_adk_visibility(use_agent):
    return gr.update(visible=use_agent, interactive=use_agent)

cb_use_agent.change(
    toggle_adk_visibility,
    inputs=[cb_use_agent],
    outputs=[cb_use_adk]
)
```

**Updated Functions**:
- `populate_characters()`: Now accepts `use_adk` parameter
- `update_character_count()`: Now accepts `use_adk` parameter

**Updated Event Handlers**:
- `btn_generate_story.click`: Added `cb_use_adk` to inputs
- `sl_number_of_characters.release`: Added `cb_use_adk` to inputs

### 3. Backend Already Configured

`handlers/story_handlers.py` already has the `use_adk` parameter implemented:
```python
def generate_story(idea, style="Studio Ghibli", use_agent=True, use_adk=True):
    if use_agent:
        if use_adk:
            agent = IdeaGenerationAgentADK(model_id=DEFAULT_MODEL_ID)  # ✨ ADK agent
        else:
            agent = IdeaGenerationAgent(model_id=DEFAULT_MODEL_ID)  # Original
```

## User Experience

### Default Behavior
1. ✅ **Use AI Agent** - Checked (enabled)
2. ✅ **Use Google ADK Agent** - Checked (enabled) and visible
3. Result: Uses `IdeaGenerationAgentADK` with LoopAgent orchestration

### Disable Agent
1. ❌ **Use AI Agent** - Unchecked
2. 🔒 **Use Google ADK Agent** - Hidden/disabled
3. Result: Uses simple single-shot LLM generation (no agent)

### Use Original Agent
1. ✅ **Use AI Agent** - Checked
2. ❌ **Use Google ADK Agent** - Unchecked
3. Result: Uses original `IdeaGenerationAgent` (manual loop)

### Use ADK Agent (Default)
1. ✅ **Use AI Agent** - Checked
2. ✅ **Use Google ADK Agent** - Checked
3. Result: Uses `IdeaGenerationAgentADK` (Google ADK with LoopAgent)

## UI Flow Diagram

```
┌─────────────────────────────────────────┐
│ ✨ The Spark Tab                        │
├─────────────────────────────────────────┤
│                                         │
│ [Story Idea Text Area]                  │
│                                         │
│ Style: [Studio Ghibli ▼]                │
│                                         │
│ ☑ 🤖 Use AI Agent                       │
│   (Self-Critique & Refinement)          │
│                                         │
│ ☑ 🚀 Use Google ADK Agent               │
│   (Advanced Multi-Agent System)         │
│   ↑ Only visible when agent enabled     │
│                                         │
│ [Generate Random Idea] [Generate Story] │
└─────────────────────────────────────────┘
```

## Benefits

1. **User Control**: Users can now choose their preferred agent
2. **Transparency**: Clear indication of which agent is being used
3. **Backward Compatibility**: Can still use original agent if needed
4. **Smart Defaults**: ADK agent is default for best quality
5. **Clean UX**: ADK option hides when agents are disabled

## Testing

To test the UI:

```bash
python main.py
```

Then in the browser:
1. Navigate to "✨ The Spark" tab
2. You should see both checkboxes
3. Try unchecking "Use AI Agent" - ADK checkbox should disappear
4. Re-check "Use AI Agent" - ADK checkbox should reappear
5. Generate a story with both checked (ADK agent)
6. Uncheck ADK, generate again (Original agent)
7. Uncheck both, generate again (Simple LLM)

## Log Messages

When generating stories, the logs will show which agent is being used:

**ADK Agent:**
```
[abc123] Generating story, use_agent=True, use_adk=True, style=Studio Ghibli
[abc123] Using IdeaGenerationAgentADK (Google ADK-based) for enhanced story generation
[ADK] IdeaGenerationAgentADK initialized with model=gemini-2.5-flash
[ADK] Starting story generation (max_iterations=3)
```

**Original Agent:**
```
[abc123] Generating story, use_agent=True, use_adk=False, style=Studio Ghibli
[abc123] Using IdeaGenerationAgent (original) for enhanced story generation
```

**No Agent:**
```
[abc123] Generating story, use_agent=False, use_adk=False, style=Studio Ghibli
[abc123] Using traditional single-shot generation
```

---

**Status**: ✅ Complete
**Date**: October 24, 2025
