# statelock-seed Client Example

This directory contains the legacy `statelock-seed` TypeScript client example used
to test local-first model routing patterns.

It is a consumer example, not runtime server code.

The `statelock-seed` name is retained for provenance and continuity with the
earlier seed repo.

## Scope

- calls LiteLLM chat-completions (`http://localhost:4000/v1/chat/completions`)
- demonstrates local-first fallback model selection
- can be used alongside StateLock Core Track APIs

## Files

- `src/client.ts`
- `package.json`
- `tsconfig.json`

## Run

```bash
npm install
npx tsx src/client.ts "Say hi in one sentence"
```
