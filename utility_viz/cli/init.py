"""``init`` sub-command — write a commented econ-viz.toml template or migrate a legacy file."""

from __future__ import annotations

import argparse
from pathlib import Path

from utility_viz.cli.errors import CliConfigError
from utility_viz.core.config.settings import LEGACY_FILE, tomllib


def cmd_init(args: argparse.Namespace) -> None:
    """Write the template to *args.path*, refusing to overwrite unless ``--force``.

    With ``--migrate`` the legacy ``utility-viz.toml`` next to *args.path* is copied
    to *args.path* (section names are unchanged) and the old file is left in place.
    """
    path = Path(args.path)
    if path.exists() and not args.force:
        raise CliConfigError(f"{path} already exists; pass --force to overwrite it")
    if getattr(args, "migrate", False):
        _migrate(path)
        return
    from utility_viz.core.config.settings import template

    path.write_text(template(), encoding="utf-8")
    print(f"Wrote {path}")


def _migrate(path: Path) -> None:
    legacy = path.parent / LEGACY_FILE
    if not legacy.is_file():
        raise CliConfigError(f"nothing to migrate: {legacy} does not exist")
    text = legacy.read_text(encoding="utf-8")
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise CliConfigError(f"{legacy}: invalid TOML: {error}") from None
    header = f"# Migrated from {LEGACY_FILE} by `utility-viz init --migrate`. Section names are unchanged.\n"
    path.write_text(header + text, encoding="utf-8")
    print(f"Wrote {path} (migrated from {legacy}; the old file was kept, you can delete it)")
