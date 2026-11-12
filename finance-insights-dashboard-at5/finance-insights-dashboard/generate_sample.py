"""Gera um extrato bancário fictício (jul–out/2026) em formato brasileiro.

Uso:
    python generate_sample.py

Cria sample_data/extrato_exemplo.csv (separador ';', datas dd/mm/aaaa e
valores com vírgula decimal), o formato mais comum nos bancos do Brasil.
"""
from __future__ import annotations

import random
from datetime import date
from pathlib import Path

import pandas as pd

random.seed(42)

MONTHS = [(2026, 7), (2026, 8), (2026, 9), (2026, 10)]
LAST_DATE = date(2026, 10, 28)  # o último mês fica "aberto" para testar a projeção


def brl(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build() -> pd.DataFrame:
    rows: list[tuple[date, str, float]] = []

    def add(year: int, month: int, day: int, desc: str, value: float) -> None:
        d = date(year, month, min(day, 28))
        if d <= LAST_DATE:
            rows.append((d, desc, round(value, 2)))

    for year, month in MONTHS:
        add(year, month, 5, "SALARIO EMPRESA XYZ", 7800.00)
        if month in (8, 10):
            add(year, month, 18, "PIX RECEBIDO FREELA SITE", random.choice([950, 1200, 1500]))

        add(year, month, 8, "ALUGUEL APTO 302", -2100.00)
        add(year, month, 9, "CONDOMINIO RESIDENCIAL", -480.00)
        add(year, month, 12, "ENERGIA ENEL", -random.uniform(170, 260))
        add(year, month, 15, "INTERNET VIVO FIBRA", -119.90)

        add(year, month, 3, "NETFLIX", -55.90)
        add(year, month, 3, "SPOTIFY", -21.90)
        add(year, month, 6, "ACADEMIA SMARTFIT", -109.90)
        add(year, month, 10, "CURSO ALURA", -89.00)

        for _ in range(random.randint(5, 7)):
            add(year, month, random.randint(1, 28),
                random.choice(["SUPERMERCADO ASSAI", "CARREFOUR HIPER", "HORTIFRUTI CENTRAL"]),
                -random.uniform(130, 320))
        for _ in range(random.randint(6, 9)):
            add(year, month, random.randint(1, 28), "IFOOD *PEDIDO", -random.uniform(32, 85))
        for _ in range(random.randint(5, 8)):
            add(year, month, random.randint(1, 28), "UBER *TRIP", -random.uniform(14, 46))
        for _ in range(2):
            add(year, month, random.randint(1, 28), "POSTO IPIRANGA", -random.uniform(150, 230))
        for _ in range(random.randint(1, 3)):
            add(year, month, random.randint(1, 28), "DROGASIL FARMACIA", -random.uniform(25, 140))
        for _ in range(random.randint(1, 2)):
            add(year, month, random.randint(1, 28),
                random.choice(["AMAZON MARKETPLACE", "SHOPEE", "RENNER"]), -random.uniform(60, 190))
        for _ in range(random.randint(1, 2)):
            add(year, month, random.randint(1, 28),
                random.choice(["CINEMA CENTER", "BAR DO ZE", "INGRESSO.COM"]), -random.uniform(40, 120))

    # Um gasto fora do padrão para o alerta de "gastos atípicos" ter o que mostrar
    add(2026, 10, 21, "MAGALU TV 55 POLEGADAS", -1899.00)

    df = pd.DataFrame(rows, columns=["Data", "Descrição", "Valor"]).sort_values("Data")
    df["Data"] = df["Data"].map(lambda d: d.strftime("%d/%m/%Y"))
    df["Valor"] = df["Valor"].map(brl)
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_data" / "extrato_exemplo.csv"
    out.parent.mkdir(exist_ok=True)
    data = build()
    data.to_csv(out, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(data)} transações salvas em {out}")
