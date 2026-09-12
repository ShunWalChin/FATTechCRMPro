"""Messaging eligibility, outbound destination policy and commercial risk: pure rules, no database."""
from datetime import datetime, timedelta, timezone

import pytest

from fattech import compliance
from fattech.outbound import OutboundUrlError, assert_safe_outbound_url, is_public_address
from fattech.services import classify_risk, score_band

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


def test_opt_out_takes_precedence_over_a_valid_window():
    inside = NOW - timedelta(hours=1)
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=inside,
                               moment=NOW).policy == "standard_24h"
    # The order of checks is the contract: a stop request wins over an otherwise perfect window.
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=inside, opted_out_at=NOW,
                               moment=NOW).reason == "opted_out"
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=NOW - timedelta(hours=30),
                               moment=NOW).reason == "outside_24h"
    assert compliance.evaluate(message="oi", is_automated=True, moment=NOW).reason == "no_inbound_interaction"


def test_invisible_characters_do_not_defeat_the_blocklist():
    hidden = "compre ag\u200bora"
    assert compliance.evaluate(message=hidden, is_automated=True, last_inbound_at=NOW - timedelta(hours=1),
                               moment=NOW, blocklist=["agora"]).reason == "blocked_content"


def test_opt_out_footer_is_added_once_and_counted_inside_the_limit():
    assert compliance.with_opt_out("Oi").endswith("\n\nResponda PARAR")
    assert compliance.with_opt_out("Oi\n\nresponda parar").count("Responda PARAR") == 1
    assert len(compliance.with_opt_out("x" * 5000)) <= compliance.MAX_TEXT_CHARS
    assert compliance.with_opt_out("x" * 5000).endswith("Responda PARAR")
    assert compliance.is_opt_out_keyword("  PARE ") and compliance.is_opt_out_keyword("Descadastrar")
    assert not compliance.is_opt_out_keyword("parar de vez")


def test_human_agent_extension_is_never_available_to_automation():
    older = NOW - timedelta(days=3)
    assert compliance.evaluate(message="oi", is_automated=False, last_inbound_at=older,
                               requested_tag="HUMAN_AGENT", moment=NOW).policy == "human_agent_7d"
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=older,
                               requested_tag="HUMAN_AGENT", moment=NOW).reason == "human_agent_is_not_automation"
    assert compliance.evaluate(message="oi", is_automated=False, last_inbound_at=NOW - timedelta(days=9),
                               requested_tag="HUMAN_AGENT", moment=NOW).reason == "outside_7d"


def test_whatsapp_requires_an_approved_template_outside_the_window():
    old = NOW - timedelta(hours=40)
    assert compliance.evaluate_whatsapp(message="oi", is_automated=True, last_inbound_at=old,
                                        moment=NOW).reason == "whatsapp_template_required"
    template = {"name": "retomada", "language": "pt_BR", "status": "PENDING", "has_opt_out": True}
    assert compliance.evaluate_whatsapp(message="oi", is_automated=True, last_inbound_at=old, moment=NOW,
                                        template=template).reason == "whatsapp_template_not_approved"
    template = {**template, "status": "APPROVED", "has_opt_out": False}
    assert compliance.evaluate_whatsapp(message="oi", is_automated=True, last_inbound_at=old, moment=NOW,
                                        template=template).reason == "whatsapp_template_missing_opt_out"
    assert compliance.evaluate_whatsapp(message="oi", is_automated=True, last_inbound_at=old, moment=NOW,
                                        template={**template, "has_opt_out": True}).allowed
    # There is no human-agent extension on WhatsApp; inside the window plain text is enough.
    assert compliance.evaluate_whatsapp(message="oi", is_automated=False, last_inbound_at=NOW - timedelta(hours=2),
                                        moment=NOW).policy == "standard_24h"


def test_clock_skew_and_trigger_cooldown():
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=NOW + timedelta(hours=1),
                               moment=NOW).reason == "invalid_interaction_time"
    assert compliance.evaluate(message="oi", is_automated=True, last_inbound_at=NOW - timedelta(hours=1),
                               trigger_last_fired_at=NOW - timedelta(hours=2), moment=NOW).reason == "trigger_cooldown"
    # A human reply is not subject to the automation cooldown.
    assert compliance.evaluate(message="oi", is_automated=False, last_inbound_at=NOW - timedelta(hours=1),
                               trigger_last_fired_at=NOW - timedelta(hours=2), moment=NOW).allowed


def test_private_reply_is_a_separate_permission_from_the_direct_message_window():
    comment = NOW - timedelta(days=2)
    assert compliance.evaluate(message="oi", is_automated=True, comment_id="c1", comment_created_at=comment,
                               moment=NOW).policy == "private_reply_7d"
    assert compliance.evaluate(message="oi", is_automated=True, comment_id="c1", comment_created_at=comment,
                               comment_already_replied=True, moment=NOW).reason == "comment_already_replied"
    assert compliance.evaluate(message="oi", is_automated=True, comment_id="c1",
                               comment_created_at=NOW - timedelta(days=9),
                               moment=NOW).reason == "outside_private_reply_window"


@pytest.mark.parametrize("address", ["10.0.0.1", "127.0.0.1", "169.254.169.254", "192.168.1.1", "172.16.0.1",
                                     "100.64.0.1", "192.0.2.1", "198.18.0.1", "203.0.113.1", "::1", "fd00::1",
                                     "fe80::1", "::ffff:127.0.0.1", "0.0.0.0", "nao-e-um-ip", ""])
def test_reserved_and_invalid_addresses_are_never_public(address):
    assert not is_public_address(address)


@pytest.mark.parametrize("address", ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111", "::ffff:8.8.8.8"])
def test_routable_addresses_are_public(address):
    assert is_public_address(address)


def test_outbound_url_policy_rejects_scheme_credentials_and_private_hosts():
    def public(host, port, **_):
        return [(None, None, None, None, ("93.184.216.34", port))]

    def internal(host, port, **_):
        return [(None, None, None, None, ("10.1.2.3", port))]

    assert assert_safe_outbound_url("https://n8n.example.com/hook", resolver=public)
    for bad in ("http://n8n.example.com/hook", "https://user:senha@n8n.example.com/hook",
                "https://n8n.example.com/hook#frag", "nao-e-url"):
        with pytest.raises(OutboundUrlError):
            assert_safe_outbound_url(bad, resolver=public)
    with pytest.raises(OutboundUrlError):
        assert_safe_outbound_url("https://169.254.169.254/latest/meta-data")
    with pytest.raises(OutboundUrlError):
        assert_safe_outbound_url("https://interno.example.com/hook", resolver=internal)


def test_risk_classification_respects_a_scheduled_next_action():
    assert classify_risk(NOW - timedelta(hours=200), None, 72, NOW)["bucket"] == "critico"
    # Whoever already booked the next step is in flight rather than abandoned.
    assert classify_risk(NOW - timedelta(hours=80), NOW + timedelta(days=1), 72, NOW)["bucket"] == "em_voo"
    assert classify_risk(NOW - timedelta(hours=80), None, 72, NOW)["bucket"] == "em_risco"
    assert classify_risk(NOW - timedelta(hours=1), None, 72, NOW)["bucket"] == "em_dia"
    # A past next action stops holding the deal in flight.
    assert classify_risk(NOW - timedelta(hours=80), NOW - timedelta(hours=1), 72, NOW)["bucket"] == "em_risco"
    assert classify_risk(None, None, 72, NOW) == {"bucket": "critico", "elapsed_hours": None, "ratio": None}
    assert (score_band(90), score_band(50), score_band(10), score_band(None)) == ("quente", "morno", "frio", None)
