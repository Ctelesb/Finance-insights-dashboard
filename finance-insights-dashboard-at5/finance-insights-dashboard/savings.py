"""Lógica de economia e investimento (sem Streamlit, fácil de testar).

Trabalha sobre o DataFrame do extrato: colunas date, description, amount
(despesa < 0), category e month (pandas Period).
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

NEEDS = ("Moradia", "Mercado", "Saúde", "Transporte", "Educação")  # base da reserva
WANTS = ("Alimentação", "Lazer", "Compras")                          # regra 50/30/20

# Premissas anuais (editáveis na página). Selic 13,75% (Copom, 04/11/2026).
CDI = 13.65           # % a.a., aproximadamente a Selic
POUPANCA = 8.3        # % a.a. (0,5% a.m. + TR, acumulado em 12 meses)
RV_RETURN = 15.0      # % a.a., premissa para ações e fundos de índice (NÃO é garantia)
IPCA_PLUS = 11.5      # % a.a., premissa: inflação (~4,1%) + juro real (~7%) do Tesouro IPCA+
FII_RETURN = 11.0     # % a.a., premissa de retorno total de fundos imobiliários



def closed_months(df: pd.DataFrame, last_is_open: bool) -> list[pd.Period]:
    """Meses do extrato; descarta o último se estiver em andamento (use core.project_month para saber)."""
    months = sorted(df["month"].unique())
    return months[:-1] if last_is_open and len(months) > 1 else months


def avg_by_category(df: pd.DataFrame, months: list[pd.Period]) -> pd.Series:
    """Gasto médio mensal por categoria (valores positivos)."""
    exp = df[(df["amount"] < 0) & df["month"].isin(months)]
    return (-exp.groupby("category")["amount"].sum() / max(len(months), 1)).sort_values(ascending=False)


def recurring(df: pd.DataFrame, months: list[pd.Period], tol: float = 0.03) -> pd.DataFrame:
    """Gastos fixos que se repetem todo mês com o mesmo valor (assinaturas, academia, cursos, internet)."""
    exp = df[(df["amount"] < 0) & df["month"].isin(months) & (df["category"] != "Moradia")]
    per = exp.groupby(["description", "category", "month"])["amount"].agg(total="sum", times="size").reset_index()
    per["total"] = per["total"].abs()
    g = per.groupby(["description", "category"]).agg(mean=("total", "mean"), std=("total", "std"),
                                                     count=("total", "size"), times=("times", "max")).reset_index()
    need = max(min(3, len(months)), 2)
    g = g[(g["count"] >= need) & (g["times"] <= 2) & (g["std"].fillna(0) <= g["mean"] * tol)]
    return (g.rename(columns={"mean": "monthly"})[["description", "category", "monthly"]]
             .sort_values("monthly", ascending=False).reset_index(drop=True))


def plan_savings(avg: pd.Series, rec: pd.DataFrame, cancelled: list[str], cuts: dict[str, int]) -> dict:
    """Economia mensal = recorrentes cancelados + % de corte sobre o que sobra de cada categoria."""
    by_cat = {c: 0.0 for c in avg.index}
    cancel_cat = rec[rec["description"].isin(cancelled)].groupby("category")["monthly"].sum()
    for cat, val in cancel_cat.items():
        by_cat[cat] = by_cat.get(cat, 0) + float(val)
    for cat, pct in cuts.items():
        base = max(float(avg.get(cat, 0)) - float(cancel_cat.get(cat, 0)), 0)
        by_cat[cat] = by_cat.get(cat, 0) + base * pct / 100
    monthly = sum(by_cat.values())
    return {"by_category": by_cat, "monthly": monthly, "yearly": monthly * 12}


def rule_503020(avg: pd.Series, income: float) -> dict:
    """Quanto da renda vai para necessidades, desejos e o que sobra (meta 50/30/20)."""
    needs = float(avg.reindex(NEEDS).fillna(0).sum())
    wants = float(avg.reindex(WANTS).fillna(0).sum())
    if income <= 0:
        return {"needs": 0, "wants": 0, "save": 0}
    return {"needs": needs / income * 100, "wants": wants / income * 100,
            "save": max(100 - (needs + wants) / income * 100, 0)}


def health_score(save_rate: float, over_share: float, reserve_months: float) -> int:
    """Score 0-100: poupança (50 pts, meta 20% da renda), orçamento (30 pts) e reserva (20 pts, meta 6 meses)."""
    s = min(max(save_rate, 0) / 20, 1) * 50
    b = (1 - min(max(over_share, 0), 1)) * 30
    r = min(reserve_months / 6, 1) * 20
    return round(s + b + r)


def future_value(monthly: float, annual_pct: float, years: int, initial: float = 0.0) -> list[float]:
    """Saldo ao fim de cada ano (índice 0 = hoje) com aportes mensais e juros compostos."""
    i = (1 + annual_pct / 100) ** (1 / 12) - 1
    bal, out = initial, [initial]
    for m in range(1, years * 12 + 1):
        bal = bal * (1 + i) + monthly
        if m % 12 == 0:
            out.append(bal)
    return out


def snapshot(df: pd.DataFrame, budgets: dict, reserve: float, last_is_open: bool) -> dict:
    """Retrato financeiro médio dos meses fechados: renda, gasto, taxa de poupança, reserva e score."""
    months = closed_months(df, last_is_open)
    avg = avg_by_category(df, months)
    income = float(df[(df["amount"] > 0) & df["month"].isin(months)]["amount"].sum() / len(months))
    spend = float(avg.sum())
    save_rate = (income - spend) / income * 100 if income else 0.0
    with_budget = [c for c in avg.index if budgets.get(c, 0) > 0]
    over_share = sum(avg[c] > budgets[c] for c in with_budget) / len(with_budget) if with_budget else 0.0
    essential = float(avg.reindex(NEEDS).fillna(0).sum())
    reserve_months = reserve / essential if essential else 0.0
    return {"months": months, "avg": avg, "income": income, "spend": spend, "save_rate": save_rate,
            "reserve_months": reserve_months, "score": health_score(save_rate, over_share, reserve_months)}


# --------------------------------------------------------------------------
# Hábitos de consumo (nome, padrão na descrição, corte sugerido em %, dica)
# --------------------------------------------------------------------------
HABITS = [
    ("Delivery de comida", r"\b(IFOOD|RAPPI|UBER EATS|99 ?FOOD|DELIVERY)\b", 40, "Cozinhar 2 ou 3 refeições a mais por semana corta quase metade."),
    ("Transporte por app", r"\b(UBER|99|CABIFY|INDRIVE)\b", 30, "Combine corridas curtas a pé ou de transporte público."),
    ("Cafés e lanches", r"\b(CAFE|PADARIA|STARBUCKS|LANCHONETE|MCDONALDS|BURGER\w*|SUBWAY)\b", 30, "Levar o café de casa já faz diferença no fim do mês."),
    ("Bares, cinema e eventos", r"\b(BAR|BOTEQUIM|PUB|BALADA|CINEMA|INGRESSO\w*|SHOW|TEATRO)\b", 30, "Escolha as saídas que realmente valem a pena."),
    ("Compras online e por impulso", r"\b(AMAZON|SHOPEE|SHEIN|ALIEXPRESS|MERCADO ?LIVRE|MAGALU|RENNER|ZARA|KABUM)\b", 30, "Espere 48 horas antes de comprar o que não estava planejado."),
    ("Streaming e música", r"\b(NETFLIX|SPOTIFY|DISNEY\w*|HBO|PRIME VIDEO|YOUTUBE|DEEZER|GLOBOPLAY|APPLE|ICLOUD)\b", 0, "Mantenha só os serviços que você usa toda semana."),
    ("Jogos e apps", r"\b(STEAM|PLAYSTATION|XBOX|NINTENDO|GOOGLE PLAY|APP STORE)\b", 50, "Compras dentro de jogos e apps somem sem você perceber."),
    ("Tarifas e juros", r"\b(TARIFA|ANUIDADE|JUROS|IOF|MULTA)\b", 100, "Quase sempre dá para negociar ou trocar de banco e zerar."),
]
_HABIT_RE = [(n, re.compile(p)) for n, p, _, _ in HABITS]


def _plain(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(text)) if unicodedata.category(c) != "Mn").upper()


def habit_of(description: str) -> str | None:
    """Hábito de consumo da descrição (a primeira regra que casar vence) ou None."""
    t = _plain(description)
    return next((n for n, rx in _HABIT_RE if rx.search(t)), None)


def habit_stats(df: pd.DataFrame, months: list[pd.Period]) -> pd.DataFrame:
    """Por hábito: gasto médio mensal, vezes por mês e valor médio por compra (maiores primeiro)."""
    exp = df[(df["amount"] < 0) & df["month"].isin(months)].copy()
    exp["habit"] = exp["description"].map(habit_of)
    exp = exp.dropna(subset=["habit"])
    g = exp.groupby("habit")["amount"].agg(total=lambda x: -x.sum(), n="size")
    n = max(len(months), 1)
    out = pd.DataFrame({"monthly": g["total"] / n, "times": g["n"] / n, "ticket": g["total"] / g["n"]})
    return out.sort_values("monthly", ascending=False)


def default_plan(df: pd.DataFrame, months: list[pd.Period]) -> float:
    """Economia mensal ao aplicar o corte sugerido em cada hábito (sem cancelar assinaturas)."""
    hs = habit_stats(df, months)
    cuts = {n: pct for n, _, pct, _ in HABITS}
    empty = pd.DataFrame(columns=["description", "category", "monthly"])
    return plan_savings(hs["monthly"], empty, [], cuts)["monthly"]


def month_score(df: pd.DataFrame, month: pd.Period, budgets: dict, reserve: float,
                projected: pd.Series | None = None) -> dict:
    """Score 0-100 do MÊS escolhido: poupança (50), orçamento (30) e reserva (20).

    `projected` é o gasto por categoria já projetado até o fim do mês (core.projected_spending);
    sem ele, usa o que foi gasto de fato.
    """
    m = df[df["month"] == month]
    income = float(m[m["amount"] > 0]["amount"].sum())
    spent = projected if projected is not None else -m[m["amount"] < 0].groupby("category")["amount"].sum()
    save_rate = (income - float(spent.sum())) / income * 100 if income else 0.0
    wb = [c for c, b in budgets.items() if b > 0]
    over = sum(spent.get(c, 0) > budgets[c] for c in wb) / len(wb) if wb else 0.0
    essential = float(spent.reindex(NEEDS).fillna(0).sum())
    rm = reserve / essential if essential else 0.0
    parts = {"Poupança": min(max(save_rate, 0) / 20, 1) * 50, "Orçamento": (1 - over) * 30, "Reserva": min(rm / 6, 1) * 20}
    return {"score": round(sum(parts.values())), "parts": parts, "save_rate": save_rate,
            "within_budget": (1 - over) * 100, "reserve_months": rm}


# --------------------------------------------------------------------------
# Produtos de investimento conhecidos (taxas = premissas editáveis, brutas, sem IR)
# --------------------------------------------------------------------------
PRODUCTS = [
    {"name": "Poupança", "ir": 'isento', "base": "poup", "factor": 1.0, "examples": "Caderneta de qualquer banco", "risk": "Baixo",
     "who": "Quem está começando e quer total simplicidade."},
    {"name": "Tesouro Selic", "ir": 'regressivo', "base": "cdi", "factor": 1.0, "examples": "Tesouro Direto (LFT)", "risk": "Baixo",
     "who": "Reserva de emergência: segurança do governo e resgate rápido."},
    {"name": "CDB 100% do CDI", "ir": 'regressivo', "base": "cdi", "factor": 1.0, "examples": "CDBs com liquidez diária", "risk": "Baixo",
     "who": "Reserva e metas de curto prazo, com garantia do FGC até R$ 250 mil."},
    {"name": "LCI / LCA", "ir": 'isento', "base": "cdi", "factor": 0.85, "examples": "LCI e LCA de bancos", "risk": "Baixo",
     "who": "Quem aceita prazo fixo e quer renda fixa isenta de IR."},
    {"name": "Tesouro IPCA+", "ir": 'regressivo', "base": "ipca", "factor": 1.0, "examples": "Tesouro IPCA+ 2035", "risk": "Médio",
     "who": "Metas de longo prazo: protege da inflação, mas oscila se vender antes."},
    {"name": "Fundos imobiliários", "ir": 'isento', "base": "fii", "factor": 1.0, "examples": "MXRF11, HGLG11, KNRI11", "risk": "Médio-alto",
     "who": "Quem busca renda mensal e topa oscilação da bolsa."},
    {"name": "Fundos de índice (ETFs)", "ir": 0.15, "base": "rv", "factor": 1.0, "examples": "BOVA11, IVVB11", "risk": "Alto",
     "who": "Longo prazo (10 anos ou mais): acompanha a bolsa brasileira ou a americana."},
]


def product_rate(p: dict, rates: dict) -> float:
    """Retorno anual (%) do produto a partir das premissas {'cdi','poup','ipca','fii','rv'}."""
    return rates[p["base"]] * p["factor"]


def principal_series(monthly: float, years: int, initial: float = 0.0) -> list[float]:
    """Quanto você colocou do próprio bolso ao fim de cada ano (índice 0 = hoje)."""
    return [initial + monthly * 12 * y for y in range(years + 1)]


# --------------------------------------------------------------------------
# Simulação com imposto de renda e inflação
# --------------------------------------------------------------------------
IR_LABEL = {"isento": "Isento de IR", "regressivo": "IR regressivo (22,5% a 15%)", 0.15: "15% sobre o ganho"}


def simulate(monthly: float, annual_pct: float, years: int, initial: float = 0.0,
             ir: str | float = "regressivo", inflation_pct: float = 0.0) -> dict:
    """Evolução ano a ano com aportes mensais, juros compostos, IR e (opcional) inflação.

    - ir: 'regressivo' (tabela por prazo de cada aporte, como CDB e Tesouro), 'isento' ou uma alíquota fixa (0.15).
    - inflation_pct > 0 mostra tudo em valores de hoje (poder de compra).
    Cada aporte paga IR pela sua própria idade: o dinheiro colocado há 3 anos e o de ontem não têm a mesma alíquota.
    Retorna {'balance', 'principal', 'interest'}, listas com um valor por ano (índice 0 = hoje).
    """
    i = (1 + annual_pct / 100) ** (1 / 12) - 1
    months = years * 12
    amounts = np.concatenate([[initial], np.full(months, float(monthly))])  # inicial hoje; aportes no fim de cada mês
    when = np.arange(months + 1)
    bal, prin = [float(initial)], [float(initial)]
    for y in range(1, years + 1):
        end = 12 * y
        age, amt = end - when[: end + 1], amounts[: end + 1]
        gain = amt * ((1 + i) ** age - 1)
        if ir == "regressivo":
            tax = float((gain * np.select([age * 30 <= 180, age * 30 <= 360, age * 30 <= 720], [0.225, 0.20, 0.175], 0.15)).sum())
        elif ir == "isento":
            tax = 0.0
        else:
            tax = float(gain.sum() * float(ir))
        deflator = (1 + inflation_pct / 100) ** y
        bal.append(float((amt * (1 + i) ** age).sum() - tax) / deflator)
        prin.append(float((amt / (1 + inflation_pct / 100) ** (when[: end + 1] / 12)).sum()))
    return {"balance": bal, "principal": prin, "interest": [b - p for b, p in zip(bal, prin)]}


def needed_monthly(remaining: float, annual_pct: float, months: int, tax: float = 0.0) -> float:
    """Aporte mensal para juntar `remaining` em `months` meses, contando o rendimento (líquido de `tax` sobre os juros)."""
    if remaining <= 0:
        return 0.0
    n = max(int(months), 1)
    i = ((1 + annual_pct / 100) ** (1 / 12) - 1) * (1 - tax)
    return remaining / n if i <= 0 else remaining * i / ((1 + i) ** n - 1)
