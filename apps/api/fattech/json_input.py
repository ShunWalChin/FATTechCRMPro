"""Reject ambiguous or non-finite JSON before it reaches models, signatures or JSONB."""
import json
import math


def validate_json_body(body: bytes):
    def reject_constant(_):
        raise ValueError("Non-finite JSON")

    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            key.encode("utf-8", errors="strict")
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    value = json.loads(body, parse_constant=reject_constant, object_pairs_hook=object_pairs)
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 64:
            raise ValueError("JSON depth exceeded")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Non-finite JSON number")
        if isinstance(item, dict):
            if any("\x00" in key for key in item):
                raise ValueError("NUL is not supported by JSONB")
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            if "\x00" in item:
                raise ValueError("NUL is not supported by JSONB")
            item.encode("utf-8", errors="strict")  # Reject unpaired surrogates before PostgreSQL.
