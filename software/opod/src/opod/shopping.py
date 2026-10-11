"""Render hardware/shopping/*.toml to Markdown shopping lists.  Usage: python -m opod.shopping

A shopping list names one concrete, orderable product per line for a kit (hardware/kits/*.toml). Each line's
`role` is a role id from hardware/parts.toml, or one of EXTRA_ROLES. Prices are a snapshot (`checked_on`).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SHOP_DIR = ROOT / "hardware" / "shopping"
PARTS = ROOT / "hardware" / "parts.toml"
KITS_DIR = ROOT / "hardware" / "kits"
EXTRA_ROLES = {"consumable": "Consumables", "bench": "Bench rig", "tool": "Tools"}
STAGES = ("bench", "bed", "tool")
STAGE_TITLE = {
    "bench": "Stage 1: bench build (no bed, 10 l water container as thermal load)",
    "bed": "Stage 2: bed (add to the bench build)",
    "tool": "Tools (not in the totals; qty 0 = you probably own it)",
}
STATUSES = {"listing", "estimate"}


@dataclass(frozen=True)
class Item:
    role: str
    name: str
    qty: int
    pack: int
    unit_eur: float
    shop: str
    url: str
    status: str
    stage: str
    notes: str

    @property
    def total_eur(self) -> float:
        return self.qty * self.unit_eur

    @property
    def units(self) -> int:
        return self.qty * self.pack


@dataclass(frozen=True)
class ShoppingList:
    kit: str
    currency: str
    checked_on: str
    region: str
    notes: str
    items: tuple[Item, ...]

    def subtotal(self, stage: str) -> float:
        return sum(i.total_eur for i in self.items if i.stage == stage)

    @property
    def total(self) -> float:
        return self.subtotal("bench") + self.subtotal("bed")

    def units(self, role: str) -> int:
        return sum(i.units for i in self.items if i.role == role)


def role_modules(parts: Path = PARTS) -> dict[str, str]:
    return {r["id"]: r["module"] for r in tomllib.loads(parts.read_text())["role"]}


def load(path: Path, parts: Path = PARTS) -> ShoppingList:
    raw = tomllib.loads(path.read_text())
    meta = raw["list"]
    if not (KITS_DIR / f"{meta['kit']}.toml").exists():
        raise ValueError(f"{path.name}: unknown kit {meta['kit']!r}")
    known = set(role_modules(parts)) | set(EXTRA_ROLES)
    items = []
    for n, it in enumerate(raw["item"], 1):
        item = Item(
            role=it["role"],
            name=it["name"],
            qty=it["qty"],
            pack=it.get("pack", 1),
            unit_eur=float(it["unit_eur"]),
            shop=it["shop"],
            url=it["url"],
            status=it["status"],
            stage=it["stage"],
            notes=it.get("notes", ""),
        )
        where = f"{path.name} item {n} ({item.name})"
        if item.role not in known:
            raise ValueError(f"{where}: unknown role {item.role!r}")
        if not isinstance(item.qty, int) or item.qty < 0:
            raise ValueError(f"{where}: qty must be an integer >= 0")
        if not isinstance(item.pack, int) or item.pack < 1:
            raise ValueError(f"{where}: pack must be an integer >= 1")
        if item.unit_eur < 0:
            raise ValueError(f"{where}: unit_eur must be >= 0")
        if not item.url.startswith("https://"):
            raise ValueError(f"{where}: url must be https")
        if item.status not in STATUSES:
            raise ValueError(f"{where}: status must be one of {sorted(STATUSES)}")
        if item.stage not in STAGES:
            raise ValueError(f"{where}: stage must be one of {STAGES}")
        if (item.role == "tool") != (item.stage == "tool"):
            raise ValueError(f"{where}: tools (and only tools) go in stage 'tool'")
        items.append(item)
    return ShoppingList(meta["kit"], meta["currency"], meta["checked_on"], meta["region"], meta["notes"].strip(), tuple(items))


def _eur(x: float) -> str:
    return f"{x:,.2f}"


def _cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render(path: Path, parts: Path = PARTS) -> str:
    sl = load(path, parts)
    modules = role_modules(parts)
    estimates = sum(1 for i in sl.items if i.status == "estimate" and i.stage != "tool")
    out = [
        f"# Shopping list: {sl.kit}",
        "",
        f"<!-- GENERATED from shopping/{path.name} by `python -m opod.shopping`. Edit the .toml, not this file. -->",
        "",
        f"> **Prices change. Checked on {sl.checked_on}** ({sl.region}, {sl.currency}). Shipping not included.",
        f"> 🟡 listing = price seen on the shop page · ❔ estimate = not confirmed, reasoned guess ({estimates} lines).",
        "> Read [SAFETY.md](../../SAFETY.md) and [WIRING.md](../WIRING.md) before ordering. Role ids link to [PARTS.md](../PARTS.md).",
        "",
        "| | EUR |",
        "|---|---:|",
        f"| Subtotal stage 1 (bench) | {_eur(sl.subtotal('bench'))} |",
        f"| Subtotal stage 2 (bed) | {_eur(sl.subtotal('bed'))} |",
        f"| **Total (bench + bed)** | **{_eur(sl.total)}** |",
        f"| Lines marked estimate | {estimates} |",
        "",
        "Tools are listed with qty 0 and are not in the totals.",
        "",
        "## Notes",
        "",
        sl.notes,
        "",
    ]
    for stage in STAGES:
        lines = [i for i in sl.items if i.stage == stage]
        if not lines:
            continue
        out += [f"## {STAGE_TITLE[stage]}", ""]
        groups: dict[str, list[Item]] = {}
        for i in lines:
            groups.setdefault(modules.get(i.role) or EXTRA_ROLES[i.role], []).append(i)
        for module, group in groups.items():
            out += [f"### {module}", "", "| Role | Item | Qty | Unit | Line | Shop | Status | Notes |", "|---|---|---:|---:|---:|---|---|---|"]
            for i in group:
                role = f"[`{i.role}`](../PARTS.md)" if i.role in modules else i.role
                qty = f"{i.qty} × {i.pack}" if i.pack > 1 else str(i.qty)
                badge = "🟡 listing" if i.status == "listing" else "❔ estimate"
                out.append(
                    f"| {role} | {_cell(i.name)} | {qty} | {_eur(i.unit_eur)} | {_eur(i.total_eur)} | "
                    f"[{_cell(i.shop)}]({i.url}) | {badge} | {_cell(i.notes)} |"
                )
            out.append("")
        if stage != "tool":
            out += [f"**Subtotal {stage}: {_eur(sl.subtotal(stage))} EUR**", ""]
    return "\n".join(out)


def lists() -> list[Path]:
    return sorted(SHOP_DIR.glob("*.toml"))


def main() -> None:
    for src in lists():
        dst = src.with_suffix(".md")
        dst.write_text(render(src))
        print(f"wrote {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
