"""
Languages a patient can choose. Staff screens stay in English.

Adding a language means adding its text everywhere a patient reads something AND its red-flag rules in safety.py,
then test phrasings in tests/safety_cases.py. Never offer a language the safety screen cannot read.
"""

LANGUAGES = {          # code: (English name, name in that language)
    "en": ("English", "English"),
    "es": ("Spanish", "Español"),
    "fr": ("French", "Français"),
}


def code(language) -> str:
    return language if language in LANGUAGES else "en"


def english_name(language) -> str:
    return LANGUAGES[code(language)][0]


def pick(table: dict, language):
    """table[language], falling back to English."""
    return table.get(code(language), table["en"])
