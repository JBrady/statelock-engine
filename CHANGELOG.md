# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Changed
- documentation updates for launcher, track boundaries, CI checks, and canonical repo path

---

## [0.4.0] - 2026-03-06

### Added
- Humane product UI
- Product navigation: Overview, Conversations, Highlights, Memory, Relationships, Runs, Learning Mode
- Overview continuity funnel visualization
- Relationships inspector for provenance and contradictions
- Learning Mode UI exposing stable conversation settings

### Architecture
- Product UI added alongside existing operator/debug routes
- Core vs Observability boundaries preserved
- Humane labels used across product UI with technical detail drawers

### Known Limitations
- No first-class candidate-memory read model yet
- Runs remain conversation-scoped
- Relationship graph visualization deferred until a stable read model exists

---

## [0.3.0] - 2026-02-17

### Added
- Hybrid query endpoint
- Snapshot/restore
- Structured error envelope
