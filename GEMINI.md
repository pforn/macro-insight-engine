# Development Guidelines for macro-insight-engine
- **Architecture:** Separate external API calls (like Google GenAI) from core business logic.
- **Typing:** Enforce strict Python type hinting. Always account for `Optional` types to satisfy Pylance.
- **Testing:** Always write unit tests using `pytest`. Use mocking for any external API requests.