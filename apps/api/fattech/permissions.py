"""Application roles remain tenant-scoped, including root. Unknown roles fail closed."""
ROLES = ("root", "super_admin", "admin", "member", "viewer")
LABELS = {"root": "Root", "super_admin": "Super Admin", "owner": "Super Admin (legado)",
          "admin": "Admin", "member": "Integrante", "viewer": "Somente leitura"}
ADMIN_ROLES = frozenset(("root", "super_admin", "owner", "admin"))
ELEVATED_ROLES = frozenset(("root", "super_admin", "owner"))
RANK = {"root": 50, "super_admin": 40, "owner": 40, "admin": 30, "member": 20, "viewer": 10}


def can_manage(actor_role: str, target_role: str) -> bool:
    if actor_role not in ADMIN_ROLES or target_role not in RANK:
        return False
    return actor_role == "root" or RANK[actor_role] > RANK[target_role]


def assignable_roles(role: str) -> list[str]:
    return [target for target in ROLES if can_manage(role, target)]


def capabilities(role: str) -> dict:
    return {"manage_team": role in ADMIN_ROLES, "manage_integrations": role in ADMIN_ROLES,
            "view_audit": role in ADMIN_ROLES, "approve_sensitive": role in ELEVATED_ROLES,
            "write_records": role in RANK and role != "viewer", "assignable_roles": assignable_roles(role)}
