from .idea_agent_adk import IdeaGenerationAgentADK
from .scene_development_agent_adk import SceneDevelopmentAgentADK

# The ADK web server will look for this `root_agent` variable.
# We expose the internal ADK agent (SequentialAgent) rather than the wrapper class
# _scene_agent_wrapper = SceneDevelopmentAgentADK()
# root_agent = _scene_agent_wrapper.root_agent

idea_agent = IdeaGenerationAgentADK()
root_agent = idea_agent.root_agent
