"""``init`` sub-command — write a commented econ-viz.toml template or migrate a legacy file."""

from __future__ import annotations

import argparse
import dataclasses
import re
from pathlib import Path

from mosaickit.econ_toml import LEGACY_SECTIONS, SHARED_COLORS

from utility_viz.cli.errors import CliConfigError
from utility_viz.core.config.settings import DEFAULT_FILE, LEGACY_FILE

_HEADER = re.compile(r"^(?P<indent>\s*)\[(?!\[)\s*(?P<name>[^\[\]#]+?)\s*\](?P<rest>.*)$")
_KEY = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_\-.\"' ]+?)\s*=")
_MIGRATED = "# Migrated from "


def cmd_init(args: argparse.Namespace) -> None:
    """Write the template to *args.path*, refusing to overwrite unless ``--force``.

    With ``--migrate`` the legacy ``utility-viz.toml`` next to *args.path* is rewritten into
    *args.path* (the old file is left in place); without one, *args.path* itself is rewritten.
    Either way utility-viz's top-level tables move under ``[utility]`` and comments are kept.
    """
    path = Path(args.path)
    if getattr(args, "migrate", False):
        _migrate(path, force=args.force)
        return
    if path.exists() and not args.force:
        raise CliConfigError(f"{path} already exists; pass --force to overwrite it")
    from utility_viz.core.config.settings import template

    path.write_text(template(), encoding="utf-8")
    print(f"Wrote {path}")


def _migrate(path: Path, *, force: bool) -> None:
    legacy = path.parent / LEGACY_FILE
    if legacy.is_file():
        source = legacy
        if path.exists() and not force:
            raise CliConfigError(f"{path} already exists; pass --force to overwrite it")
    elif path.is_file():
        source = path
    else:
        raise CliConfigError(f"nothing to migrate: neither {legacy} nor {path} exists")
    _check(source)
    text, moved = migrate_text(source.read_text(encoding="utf-8"))
    if source == path and not moved:
        print(f"{path} already keeps utility-viz's settings under [utility]; nothing to migrate")
        return
    origin = LEGACY_FILE if source == legacy else DEFAULT_FILE
    header = f"{_MIGRATED}{origin} by `utility-viz init --migrate`: utility-viz's settings now live under [utility].\n"
    _write_checked(path, header + text)
    if source == legacy:
        print(f"Wrote {path} (migrated from {legacy}; the old file was kept, you can delete it)")
    else:
        print(f"Rewrote {path}")
    for line in moved:
        print(f"  {line}")


def migrate_text(text: str) -> tuple[str, list[str]]:
    """*text* with utility-viz's top-level settings moved under ``[utility]``, and what moved.

    Works line by line so comments and layout are kept: ``[stroke.ic]`` becomes
    ``[utility.stroke.ic]``, and the keys of ``[color]`` that are not shared
    (background, axis, label) move to ``[utility.color]`` with the comments just above them.
    """
    migration = _Migration()
    for line in text.splitlines(keepends=True):
        if not line.startswith(_MIGRATED):
            migration.feed(line)
    return migration.finish(), migration.moved


class _Migration:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.moved: list[str] = []
        self.colours: list[str] = []  # lines moved from [color] to [utility.color]
        self.pending: list[str] = []  # comments in [color] waiting for the key they describe
        self.section: str | None = None
        self.colour_end: int | None = None
        self.has_utility_colour = False

    def feed(self, line: str) -> None:
        header = _HEADER.match(line)
        if header:
            self._header(line, header)
            return
        key = _KEY.match(line)
        if self.section == "color":
            self._colour_line(line, key)
        elif self.section is None and key is not None:
            self.out.append(_top_level_key(line, key, self.moved))
        else:
            self.out.append(line)

    def finish(self) -> str:
        self._leave_colour()
        if self.colours:
            _insert_colours(self.out, self.colours, self.colour_end, self.has_utility_colour)
        return "".join(self.out)

    def _leave_colour(self) -> None:
        if self.section == "color":
            self.colour_end = len(self.out)
            self.out.extend(self.pending)  # comments just above a table describe that table
            self.pending = []

    def _header(self, line: str, header: re.Match[str]) -> None:
        self._leave_colour()
        name = header["name"]
        self.section = ".".join(_segments(name))
        if self.section == "utility.color":
            self.has_utility_colour = True
        if _segments(name)[0] in LEGACY_SECTIONS:
            line = f"{header['indent']}[utility.{name}]{header['rest']}" + _eol(line)
            self.moved.append(f"[{name}] -> [utility.{name}]")
        self.out.append(line)

    def _colour_line(self, line: str, key: re.Match[str] | None) -> None:
        if key is None and line.strip().startswith("#"):
            self.pending.append(line)
            return
        name = _segments(key["key"])[0] if key is not None else None
        if name is None or name in SHARED_COLORS:
            self.out.extend(self.pending)
            self.out.append(line)
        else:
            self.colours.extend(self.pending)
            self.colours.append(line.lstrip())
            self.moved.append(f"[color] {name} -> [utility.color] {name}")
        self.pending = []


def _top_level_key(line: str, key: re.Match[str], moved: list[str]) -> str:
    """A dotted top-level key such as ``stroke.ic.width = 2`` or ``color.ic = "#000"``."""
    parts = _segments(key["key"])
    legacy = parts[0] in LEGACY_SECTIONS or (parts[0] == "color" and len(parts) > 1 and parts[1] not in SHARED_COLORS)
    if not legacy:
        return line
    moved.append(f"{key['key'].strip()} -> utility.{key['key'].strip()}")
    return f"{key['indent']}utility.{line[len(key['indent']) :]}"


def _insert_colours(out: list[str], colours: list[str], end: int | None, existing: bool) -> None:
    if existing:
        index = next(i for i, line in enumerate(out) if _is_header(line, "utility.color")) + 1
        out[index:index] = colours
        return
    index = len(out) if end is None else end
    # Blank lines and comments just before the next table belong to that table.
    while index > 0 and (not out[index - 1].strip() or out[index - 1].lstrip().startswith("#")):
        index -= 1
    if index > 0 and not out[index - 1].endswith("\n"):
        out[index - 1] += "\n"
    block = ["\n", "[utility.color]\n", *colours]
    if not block[-1].endswith("\n"):
        block[-1] += "\n"
    out[index:index] = block
    _drop_empty_colour_table(out)


def _drop_empty_colour_table(out: list[str]) -> None:
    """Remove a ``[color]`` header left with nothing under it."""
    for i, line in enumerate(out):
        if not _is_header(line, "color"):
            continue
        j = i + 1
        while j < len(out) and not out[j].strip():
            j += 1
        if j == len(out) or _HEADER.match(out[j]):
            del out[i:j]
        return


def _is_header(line: str, name: str) -> bool:
    match = _HEADER.match(line)
    return match is not None and ".".join(_segments(match["name"])) == name


def _segments(key: str) -> list[str]:
    return [part.strip().strip("\"'") for part in key.split(".")]


def _eol(line: str) -> str:
    return "\n" if line.endswith("\n") else ""


def _check(path: Path) -> None:
    from utility_viz.core.config.settings import read_file
    from utility_viz.core.errors.exceptions import InvalidParameterError

    try:
        read_file(path)
    except InvalidParameterError as error:
        raise CliConfigError(str(error)) from None


def _write_checked(path: Path, text: str) -> None:
    """Write *text* to *path* only if it is valid TOML; report settings still left behind."""
    from mosaickit import ConfigurationError

    from utility_viz.core.config.settings import SCHEMA, read_file
    from utility_viz.core.errors.exceptions import InvalidParameterError

    scratch = path.with_name(path.name + ".migrating")
    scratch.write_text(text, encoding="utf-8")
    try:
        data = read_file(scratch)
    except InvalidParameterError as error:
        scratch.unlink()
        raise CliConfigError(f"could not migrate automatically ({error}); please edit the file by hand") from None
    scratch.replace(path)
    left: list[str] = []
    try:
        dataclasses.replace(SCHEMA, legacy_warning=left.append).build(data, source=str(path), base_dir=path.parent)
    except ConfigurationError as error:
        print(f"Note: {error}")
    if left:
        print(f"Note: some settings are still at the top level; move them by hand: {left[0]}")
