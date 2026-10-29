"""``python -m kellermap``, the same program as ``kellermap``, CLI-4."""

from .cli import main

if __name__ == "__main__":  # pragma: no cover - the module runs as a script only
    raise SystemExit(main())
