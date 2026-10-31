"""Pure filtering helpers shared by the data pages (no Qt imports)."""


def _words(text) -> str:
    return " ".join(str(text).casefold().split())


def name_matches(query: str, *names) -> bool:
    """True when ``query`` is the start of a name or surname.

    'as' matches 'asiye turan' and 'ahmet as', but not 'mehmet kirmizi'.
    An empty query matches everything.
    """
    q = _words(query)
    if not q:
        return True
    for name in names:
        if name and (" " + q) in (" " + _words(name)):
            return True
    return False


def duplicate_flags(rows, name_idx: int, email_idx: int):
    """Find records registered more than once (same name AND same e-mail).

    Returns two lists aligned with ``rows``:
      is_duplicate - the record belongs to a group of 2+ identical registrations
      is_first     - the first occurrence of its registration (what stays when
                     duplicates are filtered out)
    """
    def key(row):
        name = row[name_idx] if name_idx >= 0 else ""
        email = row[email_idx] if email_idx >= 0 else ""
        return _words(name or ""), _words(email or "")

    keys = [key(r) for r in rows]
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1

    seen, is_duplicate, is_first = set(), [], []
    for k in keys:
        is_duplicate.append(counts[k] > 1)
        is_first.append(k not in seen)
        seen.add(k)
    return is_duplicate, is_first


def _norm_option(text) -> str:
    return _words(text or "").rstrip(". ")


def same_option(option: str, value) -> bool:
    """Does a recommendation cell match a chosen category?

    Tolerant of a trailing full stop and of the shorter wording used in a few
    rows ('...straight to ITPH' vs '...straight to ITPH within the VIT project.').
    """
    a, b = _norm_option(option), _norm_option(value)
    if not a or not b:
        return False
    return a == b or a.startswith(b) or b.startswith(a)


def vit_cohort_names(rows, name_idx: int, group_idx: int):
    """Map explicit VIT1/VIT2 group labels to normalized candidate names."""
    cohorts = {"VIT1": set(), "VIT2": set()}
    if name_idx < 0 or group_idx < 0:
        return cohorts
    for row in rows:
        name = _words(row[name_idx] or "")
        group = "".join(str(row[group_idx] or "").casefold().split()).replace("-", "").upper()
        if name and group in cohorts:
            cohorts[group].add(name)
    return cohorts


def previous_vit_labels(rows, name_idx: int, cohorts: dict) -> list:
    """Return VIT1/VIT2 membership labels aligned with application rows."""
    labels = []
    for row in rows:
        name = _words(row[name_idx] or "") if name_idx >= 0 else ""
        hits = [label for label in ("VIT1", "VIT2") if name and name in cohorts.get(label, set())]
        labels.append(" + ".join(hits))
    return labels


def different_vit_records(rows, name_idx: int, email_idx: int, group_idx: int,
                          email_by_name=None):
    """Return unique VIT candidates found in exactly one of VIT1 or VIT2."""
    cohorts = vit_cohort_names(rows, name_idx, group_idx)
    exclusive = {
        "VIT1": cohorts["VIT1"] - cohorts["VIT2"],
        "VIT2": cohorts["VIT2"] - cohorts["VIT1"],
    }
    result, seen = [], set()
    for row in rows:
        name = _words(row[name_idx] or "") if name_idx >= 0 else ""
        if not name or name in seen:
            continue
        label = next((cohort for cohort in ("VIT1", "VIT2") if name in exclusive[cohort]), None)
        if label is None:
            continue
        seen.add(name)
        email = row[email_idx] if email_idx >= 0 else None
        if not email and email_by_name:
            email = email_by_name.get(name)
        result.append([row[name_idx], email, f"{label} only"])
    return result
