# whatnext

Surveyor and next-action recommender: answer "what should I work on next here?" by surveying
the repo's plans, staged prompts, comms inbox (headers only), TODO, and the current session's
chat history (labeled ephemeral), then returning a brief "what to consider" list plus a 1-3
item ranked recommendation. The survey and recommendation are read-only; the only write is an
opt-in, confirmed save of uncaptured findings to `TODO.md`. Run `/whatnext` (optionally with a
focus like `/whatnext release`), or from any agent: "read and execute
`.agents/workflows/whatnext/whatnext.md`". See `.agents/workflows/index.md` for the full catalog.
