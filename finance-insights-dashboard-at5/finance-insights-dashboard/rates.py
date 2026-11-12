"""Taxas de referência do Banco Central do Brasil (API pública SGS), com valores de reserva sem conexão.

Séries: 432 = meta Selic (% a.a.) e 13522 = IPCA acumulado em 12 meses (%).
Sem internet ou com a API fora do ar, o app usa os valores de reserva abaixo e avisa o usuário.
"""
from __future__ import annotations

import json
import urllib.request

SERIES = {"selic": 432, "ipca12": 13522}
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json"
FALLBACK = {"selic": 13.75, "ipca12": 4.1, "selic_date": "04/11/2026", "ipca12_date": ""}
CDI_SPREAD = 0.10  # o CDI costuma ficar cerca de 0,10 ponto abaixo da Selic meta
REAL_RATE = 7.0    # premissa de juro real do Tesouro IPCA+ (editável na tela)


def parse_last(payload: str) -> tuple[float, str]:
    """Último ponto de uma série SGS: [{'data': '04/11/2026', 'valor': '13.75'}, ...] -> (13.75, '04/11/2026')."""
    row = json.loads(payload)[-1]
    return float(str(row["valor"]).replace(",", ".")), str(row["data"])


def fetch(timeout: float = 3.0) -> dict:
    """Taxas atuais. 'live' diz se todas vieram do Banco Central; as que falharem usam a reserva."""
    out, live = dict(FALLBACK), True
    for key, code in SERIES.items():
        try:
            with urllib.request.urlopen(URL.format(code=code), timeout=timeout) as resp:
                out[key], out[f"{key}_date"] = parse_last(resp.read().decode("utf-8"))
        except Exception:  # sem rede, timeout, API fora do ar ou resposta inesperada
            live = False
    out["live"] = live
    out["cdi"] = round(out["selic"] - CDI_SPREAD, 2)
    out["ipca_plus"] = round(out["ipca12"] + REAL_RATE, 2)
    return out
