# E2E Tests — Full Agent Pipeline Validation

End-to-end tests validate the complete agent decision flow using realistic game state fixtures. These tests treat the agent as a **black box**: provide state → get action decision.

## Test Organization

| File | Focus |
|------|-------|
| `test_emergency_overrides.py` | Critical situations bypass LLM (health<20, threats, night) |
| `test_strategic_goals.py` | LLM picks appropriate high-level goals based on context |
| `test_goap_execution.py` | GOAP resolves prerequisites and returns correct next action |
| `test_integration.py` | Full multi-tick scenarios (day 1 → day 3 progression) |

## Fixtures (in `fixtures/`)

- `day1_fresh.json` — Game start: empty inventory, basic resources nearby
- `day2_spring_inventory.json` — Early game: some tools, moderate resources
- `low_health_hostile.json` — Emergency: health 15, spider at 8m
- `night_no_fire.json` — Urgent: night phase, no equipped light
- `winter_stocked.json` — Late game: winter, full inventory, strategic planning

## Running E2E Tests

```bash
# All e2e tests
uv run pytest tests/e2e/

# Specific test file
uv run pytest tests/e2e/test_emergency_overrides.py

# Single test case
uv run pytest tests/e2e/test_emergency_overrides.py::test_low_health_forces_eat_food

# With verbose output
uv run pytest tests/e2e/ -v

# Skip slow LLM tests (run only mocked)
uv run pytest tests/e2e/ -m "not slow"
```

## Test Strategy

**Unit tests** (`tests/test_*.py`):
- Fast, isolated, mocked dependencies
- Test individual module logic
- Run on every commit

**E2E tests** (`tests/e2e/test_*.py`):
- Slower, full integration, real modules (except LLM can be mocked)
- Test agent behavior across realistic scenarios
- Run before merge/release

## Adding New E2E Tests

1. **Create fixture** (if needed):
   ```json
   // fixtures/my_scenario.json
   {
     "day": 5,
     "phase": "dusk",
     "health": 80,
     "inventory": ["axe", "log x10"],
     ...
   }
   ```

2. **Add fixture loader** to `conftest.py`:
   ```python
   @pytest.fixture
   def my_scenario(load_fixture):
       return load_fixture("my_scenario.json")
   ```

3. **Write test**:
   ```python
   def test_my_behavior(agent, my_scenario):
       inv = agent.inventory_tracker.update(my_scenario)
       action = agent.decide(my_scenario, inv)
       
       assert action["action"] == "expected_action"
   ```

## Troubleshooting

**Test fails with "module not found":**
- Ensure `PYTHONPATH` includes agent directory
- Run from `agent/` directory: `cd agent && pytest tests/e2e/`

**Test hangs (LLM timeout):**
- Use mock LLM client for most tests
- Mark real LLM tests with `@pytest.mark.slow`
- Ensure Ollama running: `ollama serve`

**Fixture validation error:**
- Check fixture matches `GameState` Pydantic model
- Validate JSON: `python -c "from models.state import GameState; GameState(**json.load(open('fixtures/file.json')))"`
