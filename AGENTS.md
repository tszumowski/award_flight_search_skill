# Agent Guidance for Flight Hunter

This repository provides a Python library and CLI for searching award flight availability on PointsYeah.com.

## Skill Activation

When a user asks about **flights, miles, points, award availability, or cheap redemptions**, activate the `flight-search` skill (`skills/flight-search/SKILL.md`).

When a user asks about **destinations, itineraries, trip planning, or travel advice**, activate the `travel-planning` skill (`skills/travel-planning/SKILL.md`).

## Quick Reference

- **Live flight search**: `src.search.search_flights()` — real-time, airport-to-airport
- **Explorer search**: `src.explorer.explore_flights()` — cached data, regions/countries/states
- **CLI entry point**: `main.py`
- **Tests**: `uv run pytest tests/ -v`
