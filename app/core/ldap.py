from ldap3 import Server, Connection, ALL, SIMPLE
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars
from app.core.config import settings


async def ldap_authenticate(username: str, password: str) -> dict | None:
    """
    Authentifie un utilisateur contre l'AD lecreusot.priv.
    Retourne un dict avec ses infos AD ou None si échec.
    """
    server = Server(settings.LDAP_HOST, port=settings.LDAP_PORT, get_info=ALL)

    # On tente un bind direct avec les credentials de l'utilisateur
    user_dn = f"{username}@lecreusot.priv"
    try:
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            authentication=SIMPLE,
            auto_bind=True,
        )
    except LDAPException:
        return None

    # Récupération des infos et groupes de l'utilisateur
    conn.search(
        search_base=settings.LDAP_BASE_DN,
        search_filter=f"(sAMAccountName={escape_filter_chars(username)})",
        attributes=["displayName", "mail", "memberOf", "department", "title"],
    )

    if not conn.entries:
        conn.unbind()
        return None

    entry = conn.entries[0]

    # Extraction des noms de groupes (CN=...,OU=...,DC=...)
    groups = []
    for dn in entry.memberOf.values if entry.memberOf else []:
        # On extrait juste le CN
        cn = dn.split(",")[0].replace("CN=", "")
        groups.append(cn)

    conn.unbind()

    return {
        "username": username,
        "display_name": str(entry.displayName) if entry.displayName else username,
        "email": str(entry.mail) if entry.mail else None,
        "department": str(entry.department) if entry.department else None,
        "title": str(entry.title) if entry.title else None,
        "groups": groups,
    }
