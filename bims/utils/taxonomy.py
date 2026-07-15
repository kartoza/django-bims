import re as _re


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
