import re as _re

from bims.enums.taxon_addendum import TaxonAddendum

ADDENDUM_ABBREVIATIONS = {
    TaxonAddendum.SENSU_LATO.name: 's.l.',
}

ADDENDUM_FULL_TEXT = {
    TaxonAddendum.SENSU_LATO.name: TaxonAddendum.SENSU_LATO.value,
}


def get_addendum_display(addendum_code: str, abbreviate: bool = True) -> str:
    """
    Return the display text for an addendum code, e.g. 's.l.' or
    'sensu lato' for TaxonAddendum.SENSU_LATO.name. Returns '' when the
    code is empty or unrecognised.
    """
    if not addendum_code:
        return ''
    mapping = ADDENDUM_ABBREVIATIONS if abbreviate else ADDENDUM_FULL_TEXT
    return mapping.get(addendum_code, '')


def build_name_with_addendum(
        canonical: str, author: str = '',
        addendum_code: str = '', abbreviate: bool = True) -> str:
    """
    Build a 'canonical [addendum] author' string, e.g.:
      ('Aquanothrus montanus', 'Engelbrecht, 1975', 'SENSU_LATO', True)
        -> 'Aquanothrus montanus s.l. Engelbrecht, 1975'
    """
    parts = [
        (canonical or '').strip(),
        get_addendum_display(addendum_code, abbreviate=abbreviate),
        (author or '').strip(),
    ]
    return ' '.join(p for p in parts if p)


def canonical_with_subgenus(canonical: str, genus: str, subgenus: str) -> str:
    """
    Return canonical_name with a subgenus parenthetical inserted when needed.

    Examples:
      ('Aedes aegypti', 'Aedes', 'Stegomyia')       -> 'Aedes (Stegomyia) aegypti'
      ('Stegomyia',    'Aedes', 'Stegomyia')        -> 'Aedes (Stegomyia)'
      ('Aedes (Stegomyia) aegypti', 'Aedes', 'Stegomyia') -> unchanged
    """
    canonical = (canonical or '').strip()
    if not subgenus or not genus:
        return canonical

    # Accept "Genus (BareSubgenus)" or bare "BareSubgenus" as the subgenus value.
    m = _re.search(r'\((.+?)\)', subgenus)
    sg_name = m.group(1) if m else subgenus

    if f'({sg_name})' in canonical:
        return canonical

    genus_cap = genus[:1].upper() + genus[1:].lower()

    # Bare subgenus name as canonical (subgenus-rank taxon) — no epithet.
    if canonical.lower() == sg_name.lower():
        return f'{genus_cap} ({sg_name})'

    # Strip genus prefix and any existing parenthetical tokens.
    tokens = canonical.split()
    non_paren = [t for t in tokens if not (t.startswith('(') and t.endswith(')'))]
    if non_paren and non_paren[0].lower() == genus.lower():
        epithet_tokens = non_paren[1:]
    else:
        epithet_tokens = non_paren

    epithet = ' '.join(w.lower() for w in epithet_tokens)
    if epithet:
        return f'{genus_cap} ({sg_name}) {epithet}'
    return f'{genus_cap} ({sg_name})'
