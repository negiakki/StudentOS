"""StudentOS backend — FastAPI modular monolith.

Layering (see Docs/03_System_Architecture.md):
    api → services → repositories → database
Coco (ai) orchestrates tools; it never touches the database directly.
"""

__version__ = "1.0.0"
