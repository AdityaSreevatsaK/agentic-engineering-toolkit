# RAG trust boundary and adversarial evidence

Both RAG starters label retrieved passages as **untrusted data** and include retrieved source IDs in a separate API field. Live synthesis JSON-quotes source text and escapes angle brackets before placing it inside an explicit evidence block. The prompt instructs the model to ignore fake roles, tool requests and instructions inside evidence.

Offline adversarial tests cover fake system messages, attempts to close evidence delimiters, answer overrides and exfiltration URLs. They assert provenance and prompt framing with fake models. **They do not prove that a real model will resist prompt injection.**

Never let model-generated instructions or citations authorise privileged tool calls. Enforce authorisation outside the model, restrict egress and secrets, and run approved model-level adversarial tests before handling sensitive data. Treat generated answers as untrusted; use the API's source_ids for retrieval provenance.
