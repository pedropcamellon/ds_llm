# DontStarve-AI: Hybrid Don't Starve Decision Agent

**A general AI playground for Don't Starve, combining rule-based logic, goal systems, and LLM-assisted planning.**

Current implementation status:

- The agent currently provides long-term and mid-term goal assistance.
- Mid-term goal selection is rule-guided and can be assisted by the LLM.
- The current LLM-assisted path uses Ollama running locally.
- The project is not yet a fully autonomous end-to-end Wilson controller.
- The broader direction is hybrid AI, not LLM-only control.

That broader framing matters because the planned system is expected to mix multiple approaches, including rule-based logic, GOAP-style planning, and LLM reasoning where each is a good fit.

## Repository Structure

The current top-level folder structure is intentionally shaped so the project can live directly inside the Don't Starve `mods` folder as a working mod.

That means the repository includes both mod-facing files at the root and the external Python agent implementation alongside them.

Most active development work is currently happening under the `agent/` folder. That is where the goal system, prompt building, state models, tests, and LLM or planner-side logic are being developed.

## Future Improvements

- Full integration between high-level goal selection and low-level action execution.
- GOAP-style planning for concrete action sequences and prerequisite handling.
- Stronger coordination between behavior-tree logic, goal planning, and LLM reasoning.
- Better world-state validation, recovery behavior, and debugging tools.
- Tighter in-game execution so Wilson can act on selected goals with less manual scaffolding.

## License

This project extends the "Artificial Wilson" mod (original author: KingofTown, v0.3).
Modifications for LLM integration: Public domain / MIT
