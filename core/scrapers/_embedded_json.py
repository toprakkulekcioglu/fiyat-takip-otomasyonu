"""Bazı sitelerin sayfa HTML'ine gömdüğü JS nesnelerini (dataLayer.push({...}),
window["x"]={...} gibi) ayrıştırmak için ortak yardımcı.

Neden regex ile tüm objeyi yakalamak yerine bu yöntem: iç içe süslü parantezli
büyük JSON'larda regex'in ".*?" ile "en yakın kapanışı" bulması güvenilir değil
(objenin içinde başka "}" karakterleri de var). Bunun yerine süslü parantez
sayacıyla gerçekten dengeli (balanced) kapanışı buluyoruz.
"""
import json


def extract_balanced_json(text: str, start_marker: str) -> dict | list | None:
    """`start_marker`den sonraki ilk '{'den başlayıp dengeli kapanışa kadar olan
    JSON'u ayrıştırır. Bulamazsa veya bozuksa None döner."""
    marker_idx = text.find(start_marker)
    if marker_idx == -1:
        return None

    start = text.find("{", marker_idx)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
