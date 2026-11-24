import unicodedata

from django import template

register = template.Library()

# Palavra-chave no nome da especialidade -> ícone do Phosphor Icons (https://phosphoricons.com)
ICONES_ESPECIALIDADE = [
    ("cardio", "ph-heartbeat"),
    ("pediatr", "ph-baby"),
    ("odonto", "ph-tooth"),
    ("dent", "ph-tooth"),
    ("ortodon", "ph-tooth"),
    ("gineco", "ph-gender-female"),
    ("obstet", "ph-gender-female"),
    ("dermat", "ph-hand-heart"),
    ("estet", "ph-sparkle"),
    ("harmoniz", "ph-sparkle"),
    ("ortoped", "ph-bone"),
    ("oftalm", "ph-eye"),
    ("psic", "ph-brain"),
    ("psiq", "ph-brain"),
    ("neuro", "ph-brain"),
    ("nutri", "ph-apple-logo"),
    ("exame", "ph-flask"),
    ("laborat", "ph-flask"),
    ("imagem", "ph-scan"),
    ("ultrass", "ph-scan"),
    ("clinic", "ph-stethoscope"),
]


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


@register.filter
def icone_especialidade(nome):
    nome = _sem_acento(nome or "")
    for chave, icone in ICONES_ESPECIALIDADE:
        if chave in nome:
            return icone
    return "ph-first-aid-kit"


@register.filter
def whatsapp_numero(telefone):
    """Transforma '89999998888' em '5589999998888' para usar no wa.me."""
    numero = "".join(c for c in str(telefone or "") if c.isdigit())
    if len(numero) in (10, 11):
        numero = "55" + numero
    return numero


@register.filter
def telefone_formatado(telefone):
    n = "".join(c for c in str(telefone or "") if c.isdigit())
    if len(n) == 11:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return telefone
