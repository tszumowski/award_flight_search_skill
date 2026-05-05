---
name: travel-planning
description: Destination recommendations, itineraries, and trip planning. Use when user asks about where to travel, trip planning, itineraries, destination comparisons, or travel advice.
---

# Travel Planning Skill

Help users plan trips by researching destinations, creating itineraries, and providing practical travel advice.

## When to Use

- User asks for destination recommendations
- User wants itinerary suggestions
- User asks about attractions, weather, or packing for a trip
- User wants to compare destinations
- User asks about visa requirements, currency, or local customs

## Workflow

1. **Understand Requirements**
   - Trip goals (beach, city, adventure, relaxation, culture)
   - Group type (solo, couple, family with children's ages)
   - Budget level
   - Travel dates and duration
   - Constraints (visa, distance, climate preferences)

2. **Research Destinations**
   - Use WebSearch to find current information
   - Compare 2-3 destinations that match criteria
   - Consider seasonality and weather for travel dates

3. **Present Recommendations**

   For each destination, provide:
   - Why it matches their goals
   - Top 5 attractions and activities
   - Day-by-day itinerary outline
   - Weather expectations and packing tips
   - Practical info (visa, currency, transport)
   - Best neighborhoods to stay in

4. **Pair with Flight Search**

    After destination recommendations, suggest searching for award flights using the flight-search skill or the `flight_hunter` Python library to find the best point redemptions.

## Group-Specific Advice

- **Families**: family-friendly activities, safety, age-appropriate attractions, stroller-friendly transport
- **Couples**: romantic settings, dining recommendations, couple activities
- **Solo travelers**: safety tips, social opportunities, flexible itineraries

## Practical Details to Include

- Visa requirements for the traveler's nationality
- Currency and tipping customs
- Local transportation options
- Safety considerations and neighborhoods to avoid
- Best time to visit vs. when they're planning to go
