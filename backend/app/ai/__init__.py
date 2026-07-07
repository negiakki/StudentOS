"""AI layer (Phase 4.5).

Structure:
    interfaces/  — provider contracts (ports): VisionProvider, ChatProvider
    providers/   — concrete providers: gemini (vision), openrouter (stub)
    routers/     — the ONLY entry points the app may use; select a provider by config

Application code depends on the routers and interfaces, never on a concrete
provider. Provider selection is configuration (VISION_PROVIDER / CHAT_PROVIDER),
so switching providers requires editing only .env
(Docs/03_System_Architecture.md §13). Coco is built in Phase 6 on the chat router.

`timetable_parser.py` is preserved for V2 and runs through the vision router; V1
does not call it (gated by ENABLE_TIMETABLE_PARSING).
"""
