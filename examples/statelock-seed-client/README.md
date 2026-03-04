# statelock-seed Client Example

This directory is the canonical home for the seed TypeScript client used to test local-first model routing patterns.

It is a consumer example, not runtime server code.

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
