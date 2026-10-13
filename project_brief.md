# My agent: greenhouse-agent
One-liner: A conversational agent that helps plant parents choose, care for, and troubleshoot houseplants with a catalog of plants, care guides, and diagnostic tools.

Tool coverage:
- Memory: Remembers the user's home lighting conditions (e.g. low light, south-facing), pet ownership (cat/dog toxicity filters), watering habits, and current plant collection.
- Tools: Look up plant catalog, check watering/care schedules, filter plants by light/pet toxicity, record plant adoption.
- Catalog/UI: Houseplant catalog with care difficulty, light requirements, watering frequency, and pet safety (rendered as A2UI cards/tables).
- Image gen: Generates visuals of healthy plants, visual care diagrams, or room placement previews.
- Sandbox: Calculates custom soil mix ratios or days until next watering based on ambient temperature/season.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): code sandbox for soil calculation, Cloud Trace for latency tracking
