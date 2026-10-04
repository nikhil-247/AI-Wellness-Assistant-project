# Architecture

## System overview

Self Love follows a small client/server architecture:

```text
┌───────────────────────────┐
│        React Client       │
│                           │
│ Chat · Mood · Voice       │
│ Stories · Wellness UI     │
└─────────────┬─────────────┘
              │ REST / JSON
              ▼
┌───────────────────────────┐
│       Flask Backend       │
│                           │
│ Request validation        │
│ Prompt construction       │
│ Conversation context      │
│ Error handling            │
└─────────────┬─────────────┘
              │ HTTPS
              ▼
┌───────────────────────────┐
│       OpenRouter API      │
│         LLM Provider      │
└───────────────────────────┘
```

## AI interaction design

The backend keeps the model-facing logic separate from the UI. A request contains:

- current user message
- current mood
- recent conversation history

The backend then adds a system instruction that keeps the assistant supportive, concise, non-clinical, and transparent about its limitations.

Only a bounded number of previous messages are sent with each request so context remains predictable.

## Voice interaction

Voice input is handled client-side through the browser Speech Recognition API when supported. The transcript is placed into the normal chat composer, so voice and text share the same backend path.

## Wellness features

The UI exposes lightweight wellness-oriented experiences around the core conversation loop:

- mood-based music direction
- short AI-generated bedtime stories
- simple reset/reminder prompts

These features are intentionally separated from the chat API so the core conversational service remains small and easy to test.

## Reliability considerations

The implementation includes:

- input validation
- bounded conversation history
- request timeouts for provider calls
- explicit provider error handling
- environment-based secret configuration
- CORS restricted to the configured frontend origin

## Extension ideas

For a production deployment, useful next steps would include persistent user preferences, structured event logging, rate limiting, authentication, model/evaluation tracking, and automated safety evaluations.
