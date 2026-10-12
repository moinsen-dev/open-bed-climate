"""Render hardware/parts.toml to hardware/PARTS.md.  Usage: python -m obc.render_parts"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "hardware" / "parts.toml"
DST = ROOT / "hardware" / "PARTS.md"
BADGE = {"datasheet": "✅ datasheet", "listing": "🟡 listing", "unverified": "❔ unverified", "rejected": "❌ rejected"}


def render(src: Path = SRC) -> str:
    data = tomllib.loads(src.read_text())
    out = [
        "# Parts catalog",
        "",
        "<!-- GENERATED from parts.toml by `python -m obc.render_parts`. Edit parts.toml, not this file. -->",
        "",
        "Roles first, then example parts. **Safety-relevant** roles (🛡) affect the limits in [SAFETY.md](../SAFETY.md).",
        "Status: ✅ key specs confirmed in the datasheet · 🟡 only seen in a listing · ❔ please verify · ❌ checked and rejected.",
        "Found a better or local part? Open a *Part substitution* issue or edit `parts.toml`.",
        "",
    ]
    for role in data["role"]:
        shield = " 🛡" if role.get("safety") else ""
        out += [f"## `{role['id']}`{shield} · {role['module']}", "", f"**Requirement:** {role['requirement']}", ""]
        if role.get("notes"):
            out += [role["notes"], ""]
        out += ["| Example | Status | Notes |", "|---|---|---|"]
        for ex in role.get("example", []):
            name = f"[{ex['name']}]({ex['source']})" if ex.get("source") else ex["name"]
            when = f" ({ex['verified_on']})" if ex.get("verified_on") else ""
            notes = ex.get("notes", "").replace("|", "\\|")
            out.append(f"| {name} | {BADGE[ex['status']]}{when} | {notes} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    DST.write_text(render())
    print(f"wrote {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
