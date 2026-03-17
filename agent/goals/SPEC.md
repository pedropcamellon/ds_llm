# Goals Spec

This folder defines the current high-level goal system used by the agent.

The long-term layer describes season-scale survival pressure. It explains what the world is asking from the player over many days.

The mid-term layer is rule-based for now. It gathers several relevant tactical goals from the current state, assigns them fixed internal priority, removes goals that are already complete, and returns a small option set for the LLM.

Mid-term priority exists to keep important goals visible under the current option limit. Early progression, base establishment, seasonal preparation, and specific food plans should not disappear just because exploration is always available.

Exploration remains a universal option. Even when more specific goals are available, the system should still leave room for map discovery and resource scouting.

The short-term layer handles immediate survival pressure such as critical health, threats, darkness, hunger, cold, and sanity loss.

The intended design is fail-fast on broken or unknown state, not silent fallback. Goal selection should surface invalid assumptions early so the exporter and rules can be corrected.
