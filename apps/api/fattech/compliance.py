"""Deterministic messaging eligibility: a contact snapshot in, an auditable decision out.

This module touches neither network nor database, so a decision can be tested and replayed. Every
automatic sender evaluates at the moment of sending and never when the message is queued: consent,
the service window and the blocklist all change between scheduling and delivery.
"""
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

OPT_OUT_FOOTER = "Responda PARAR"
MAX_TEXT_CHARS = 1000
STANDARD_WINDOW = timedelta(hours=24)
HUMAN_AGENT_WINDOW = timedelta(days=7)
DEFAULT_COOLDOWN = timedelta(hours=24)
MAX_CLOCK_SKEW = timedelta(minutes=5)
# Normalized stop variants; a contact writing "pare" is opting out as much as one writing "PARAR".
OPT_OUT_KEYWORDS = frozenset({"parar", "pare", "sair", "cancelar", "descadastrar", "remover",
                              "stop", "unsubscribe"})
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"))
_FOOTER_AT_END = re.compile(rf"\s*{re.escape(OPT_OUT_FOOTER)}\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    policy: str
    body: str
    reason: str | None = None
    tag: str | None = None
    seconds_left: int = 0

    def as_dict(self):
        return {"allowed": self.allowed, "policy": self.policy, "reason": self.reason,
                "tag": self.tag, "seconds_left": self.seconds_left}


def normalize_text(value: str) -> str:
    """NFKC plus invisible-character removal: a zero-width space between letters must not defeat the blocklist."""
    folded = unicodedata.normalize("NFKC", value or "").translate(_INVISIBLE)
    return " ".join(folded.split()).lower()


def is_opt_out_keyword(value: str) -> bool:
    return normalize_text(value) in OPT_OUT_KEYWORDS


def with_opt_out(message: str) -> str:
    """Truncate counting the footer, never after appending it, and never repeat a footer already present."""
    suffix = f"\n\n{OPT_OUT_FOOTER}"
    base = _FOOTER_AT_END.sub("", (message or "").strip()).strip()
    return base[: MAX_TEXT_CHARS - len(suffix)].rstrip() + suffix


def instant(value) -> datetime | None:
    if not value:
        return None
    moment = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


def _blocked(body: str, blocklist) -> bool:
    haystack = normalize_text(body)
    return any(term and term in haystack for term in (normalize_text(item) for item in blocklist or ()))


def evaluate(*, message: str, is_automated: bool, last_inbound_at=None, opted_out_at=None, moment=None,
             requested_tag: str | None = None, trigger_last_fired_at=None, cooldown=DEFAULT_COOLDOWN,
             comment_id: str | None = None, comment_created_at=None, comment_already_replied=False,
             blocklist=()) -> Decision:
    """Instagram and internal channels.

    The order of the checks is deliberate rather than incidental: opt-out and a missing inbound take
    precedence over content, cooldown and windows, so the audited reason stays the same for the same state.
    """
    now = instant(moment) or datetime.now(timezone.utc)
    inbound = instant(last_inbound_at)
    body = with_opt_out(message) if is_automated else (message or "").strip()
    elapsed = None if inbound is None else now - inbound
    left = 0 if elapsed is None else max(0, int((STANDARD_WINDOW - elapsed).total_seconds()))

    def deny(reason: str, policy: str = "blocked") -> Decision:
        return Decision(False, policy, body, reason=reason, seconds_left=left)

    if opted_out_at:
        return deny("opted_out")
    if inbound is not None and inbound > now + MAX_CLOCK_SKEW:
        return deny("invalid_interaction_time")
    if _blocked(body, blocklist):
        return deny("blocked_content")
    if comment_id and comment_already_replied:
        return deny("comment_already_replied")

    # A Private Reply is its own Meta permission: one message per comment, within seven days, and it
    # never converts that comment into a standard direct-message window.
    if comment_id:
        commented = instant(comment_created_at) or inbound
        if commented is None:
            return deny("no_inbound_interaction")
        if commented > now + MAX_CLOCK_SKEW:
            return deny("invalid_interaction_time")
        if now - commented > HUMAN_AGENT_WINDOW:
            return deny("outside_private_reply_window")
        return Decision(True, "private_reply_7d", body, seconds_left=left)

    if inbound is None:
        return deny("no_inbound_interaction")
    fired = instant(trigger_last_fired_at)
    if is_automated and fired and now - fired < cooldown:
        return deny("trigger_cooldown")
    if elapsed <= STANDARD_WINDOW:
        return Decision(True, "standard_24h", body, seconds_left=left)
    if requested_tag == "HUMAN_AGENT":
        if is_automated:
            return deny("human_agent_is_not_automation")
        if elapsed <= HUMAN_AGENT_WINDOW:
            return Decision(True, "human_agent_7d", body, tag="HUMAN_AGENT")
        return deny("outside_7d")
    return deny("outside_24h")


def evaluate_whatsapp(*, message: str, is_automated: bool, last_inbound_at=None, opted_out_at=None,
                      moment=None, trigger_last_fired_at=None, cooldown=DEFAULT_COOLDOWN,
                      template: dict | None = None, blocklist=()) -> Decision:
    """WhatsApp has no HUMAN_AGENT extension: free text only inside 24h, otherwise an approved template."""
    now = instant(moment) or datetime.now(timezone.utc)
    inbound = instant(last_inbound_at)
    elapsed = None if inbound is None else now - inbound
    left = 0 if elapsed is None else max(0, int((STANDARD_WINDOW - elapsed).total_seconds()))
    text = with_opt_out(message) if is_automated else (message or "").strip()
    body = f"[Template WhatsApp: {template['name']}/{template['language']}]" if template else text

    def deny(reason: str) -> Decision:
        return Decision(False, "blocked", body, reason=reason, seconds_left=left)

    if opted_out_at:
        return deny("opted_out")
    if inbound is not None and inbound > now + MAX_CLOCK_SKEW:
        return deny("invalid_interaction_time")
    if not template and _blocked(text, blocklist):
        return deny("blocked_content")
    fired = instant(trigger_last_fired_at)
    if is_automated and fired and now - fired < cooldown:
        return deny("trigger_cooldown")
    if template:
        if str(template.get("status", "")).upper() != "APPROVED":
            return deny("whatsapp_template_not_approved")
        if is_automated and not template.get("has_opt_out"):
            return deny("whatsapp_template_missing_opt_out")
        return Decision(True, "whatsapp_template", body, seconds_left=left)
    if elapsed is None or elapsed > STANDARD_WINDOW:
        return deny("whatsapp_template_required")
    return Decision(True, "standard_24h", text, seconds_left=left)
