# Layer 5: Context Serializer

## Purpose
LLMs are highly sensitive to prompt formatting. The ContextSerializer formats the final context into structured Markdown.

## How It Works
It takes the structured ReviewContext (Callers, Callees, Changed Symbols, Snippets) and translates it into strict Markdown headers.

## Crucial Implementation Details
It explicitly formats code snippets like this:
`
**Source code for generateOtp in file src/OtpGenerator.java:**
`
By explicitly providing the real file path in the prompt header, we force the LLM to include the real file path in its JSON output. This ensures that the GitHub publisher can map the findings to the correct lines in the PR diff for inline comments.
