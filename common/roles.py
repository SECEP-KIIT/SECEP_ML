"""
common/roles.py — Enron custodian -> SRS RoleCategory, for the training pool and analysis.

The recipient's role is a model feature, so the mapping must be consistent:
  * GOLD_ROLES   the 19 custodians used for the gold set, copied exactly from
                 build_gold_sheet.py. Never change these: gold labels were made with them.
  * APPROX_ROLES the other custodians, mapped from public Enron job titles (approximate).
                 Same convention as gold: CEO / President / C-level / chief of staff ->
                 Executive; VP or director running a function -> Manager; lawyers and
                 legal specialists -> Consultant; traders -> ClientFacing; analysts and
                 specialists -> Analyst; everyone else -> Other.
  * anything not listed -> Other.

If the team corrects a title, change it here, bump ROLES_VERSION and rebuild the pool.
Only the live system's notion of "recipient role" matters at inference time; custodian
names are never model features.
"""
ROLES_VERSION = "1.0"
ROLES = ("Executive", "Manager", "Consultant", "ClientFacing", "Analyst", "Other")

GOLD_ROLES = {
    "kean-s": "Executive", "kitchen-l": "Executive", "delainey-d": "Executive",
    "lavorato-j": "Executive", "beck-s": "Executive",
    "kaminski-v": "Manager", "shapiro-r": "Manager", "steffes-j": "Manager", "presto-k": "Manager",
    "jones-t": "Consultant", "shackleton-s": "Consultant", "mann-k": "Consultant",
    "germany-c": "ClientFacing", "arnold-j": "ClientFacing", "bass-e": "ClientFacing",
    "dasovich-j": "Analyst", "symes-k": "Analyst",
    "farmer-d": "Other", "lokay-m": "Other",
}

_E, _M, _C, _T, _A, _O = ROLES
APPROX_ROLES = {
    # Executives
    "lay-k": _E, "skilling-j": _E, "whalley-g": _E, "buy-r": _E, "derrick-j": _E,
    "haedicke-m": _E, "hayslett-r": _E, "horton-s": _E, "mcconnell-m": _E, "shankman-j": _E,
    # Managers (VPs / directors / managers running a function, not trading desks)
    "blair-l": _M, "corman-s": _M, "gang-l": _M, "gay-r": _M, "harris-s": _M, "hyatt-k": _M,
    "lokey-t": _M, "lucci-p": _M, "mccarty-d": _M, "richey-c": _M, "schoolcraft-d": _M,
    "white-s": _M, "zipper-a": _M,
    # Legal -> Consultant
    "bailey-s": _C, "cash-m": _C, "dickson-s": _C, "fossum-d": _C, "hain-m": _C, "heard-m": _C,
    "hodge-j": _C, "hyvl-d": _C, "nemec-g": _C, "panus-s": _C, "perlingiere-d": _C, "rapp-b": _C,
    "sager-e": _C, "sanders-r": _C, "stclair-c": _C, "taylor-m": _C,
    # Traders -> ClientFacing
    "allen-p": _T, "arora-h": _T, "badeer-r": _T, "baughman-d": _T, "benson-r": _T,
    "brawner-s": _T, "carson-m": _T, "crandell-s": _T, "cuilla-m": _T, "davis-d": _T,
    "dean-c": _T, "dorland-c": _T, "ermis-f": _T, "forney-j": _T, "gilbertsmith-d": _T,
    "griffith-j": _T, "grigsby-m": _T, "guzman-m": _T, "hendrickson-s": _T, "holst-k": _T,
    "keavey-p": _T, "king-j": _T, "kuykendall-t": _T, "lenhart-m": _T, "lewis-a": _T,
    "linder-e": _T, "maggi-m": _T, "martin-t": _T, "may-l": _T, "mckay-b": _T, "mckay-j": _T,
    "meyers-a": _T, "motley-m": _T, "neal-s": _T, "parks-j": _T, "platter-p": _T,
    "quenet-j": _T, "quigley-d": _T, "reitmeyer-j": _T, "ring-a": _T, "ruscitti-k": _T,
    "saibi-e": _T, "salisbury-h": _T, "sanchez-m": _T, "scholtes-d": _T, "schwieger-j": _T,
    "shively-h": _T, "slinger-r": _T, "smith-m": _T, "south-s": _T, "staab-t": _T,
    "stepenovitch-j": _T, "storey-g": _T, "sturm-f": _T, "swerzbin-m": _T, "tholt-j": _T,
    "thomas-p": _T, "townsend-j": _T, "tycholiz-b": _T, "ward-k": _T, "whitt-m": _T,
    "williams-w3": _T, "wolfe-j": _T, "zufferli-j": _T,
    # Analysts / specialists
    "campbell-l": _A, "causholli-m": _A, "rodrique-r": _A, "semperger-c": _A,
}


def role_for(custodian: str) -> tuple[str, str]:
    """custodian folder name -> (role, source) where source is gold | approx | default."""
    c = custodian.lower()
    if c in GOLD_ROLES:
        return GOLD_ROLES[c], "gold"
    if c in APPROX_ROLES:
        return APPROX_ROLES[c], "approx"
    return "Other", "default"
