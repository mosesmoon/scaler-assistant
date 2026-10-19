"""What a running game's upscaler is doing, in words: shared by the window, the overlay
and the Steam Deck (Decky) plugin. No UI toolkit here."""

from __future__ import annotations

from typing import Optional

from .i18n import tr
from .runtime import RunningGame


def way_label(route: str) -> str:
    return tr("way_" + route)


def choice_label(choice: Optional[str]) -> str:
    return tr("choice_" + (choice or "none").replace(":", "_"))


def wave32_problem(entry, game: RunningGame, rdna3: bool) -> bool:
    """HelixSR the OptiScaler way on RDNA 3+ running its network with wave32."""
    return bool(entry and entry.status.route == "optiscaler" and rdna3
                and game.log and game.log.wave == 32)


def describe(entry, game: RunningGame,
             rdna3: bool) -> tuple[str, str, list[tuple[str, str, bool]], list[str]]:
    """(headline, tone 'ok' / 'warn' / 'orange', [(label, detail, active)], notes)."""
    status = entry.status
    lines: list[tuple[str, str, bool]] = []
    notes: list[str] = []
    if status.upscaler != "helixsr":
        label = choice_label(status.choice)
        if game.helixsr_loaded:
            headline, tone = tr("rt_loaded_fsr", choice=label), "ok"
        else:
            headline, tone = tr("rt_not_loaded_fsr", choice=label), "warn"
        lines.append((f"OptiScaler ({status.opti_name})", tr("rt_menu_hint"), game.helper_loaded))
        if entry.launch_missing:
            notes.append(tr("is_launch_missing_short"))
        return headline, tone, lines, notes
    route = status.route or "direct"
    if game.helixsr_loaded:
        headline, tone = tr("rt_loaded", version=status.version or "?", way=way_label(route)), "ok"
    else:
        headline, tone = tr("rt_not_loaded_" + route), "warn"
    if route == "optiscaler":
        lines.append((f"OptiScaler ({status.opti_name})", tr("rt_menu_hint"), game.helper_loaded))
    elif route == "dlss":
        lines.append((tr("rt_loader"), "", game.helper_loaded))
    log = game.log
    if log:
        if log.wave:
            lines.append((tr("rt_wave"), f"wave{log.wave}", True))
        if log.version and status.version and log.version != status.version:
            notes.append(tr("rt_log_version", version=log.version))
        notes += log.problems
        if log.problems and game.helixsr_loaded:
            tone = "orange"
    if wave32_problem(entry, game, rdna3):
        notes.append(tr("rt_wave32"))
    return headline, tone, lines, notes
