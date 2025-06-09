# Open Warp

This repository contains the early scaffolding for **Open Warp**, an MIT licensed terminal with optional AI assistance. The project is organized as a Cargo workspace with multiple crates and a Tauri application.

## Workspace Layout

- `crates/terminal-core` – cross-platform PTY wrapper and block model.
- `crates/llm-client` – asynchronous HTTP client for various LLM providers.
- `crates/plugin-sdk` – WASM based plugin API.
- `app` – Tauri + React front-end (to be implemented).
- `docs` – Documentation built with MkDocs or similar.

Run `cargo test --workspace` to verify the Rust crates build correctly.
