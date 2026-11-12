"""Textos de destaque e insights automáticos em linguagem simples (sem Streamlit)."""
from __future__ import annotations

import html

import pandas as pd

MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def score_status(score: int) -> tuple[str, str]:
    """(rótulo, tom) da nota: verde = bom, amarelo = atenção, vermelho = crítico."""
    if score >= 80:
        return "Excelente", "good"
    if score >= 60:
        return "Boa", "good"
    if score >= 40:
        return "Atenção", "warn"
    return "Crítica", "bad"


def hero_html(month: pd.Period, proj: dict, cur: dict, total_budget: float,
              potential: float, future: float, years: int = 10, icon_html: str = "") -> str:
    """Card de destaque: a situação do mês em uma frase + o que dá para ganhar economizando."""
    name = MONTHS_PT[month.month - 1]
    if proj["is_open"]:
        head = f'Você já gastou <span class="hl">{brl(proj["spent"])}</span> em {name}.'
        if total_budget:
            diff = proj["projected"] - total_budget
            cls = "hl bad" if diff > 0 else "hl good"
            head += (f' No ritmo atual, fecha o mês em <span class="{cls}">{brl(proj["projected"])}</span>, '
                     f'{brl(abs(diff))} {"acima" if diff > 0 else "abaixo"} do orçamento.')
    else:
        bal = cur["balance"]
        head = (f'Em {name} você gastou <span class="hl">{brl(cur["expenses"])}</span> e '
                f'{"sobraram" if bal >= 0 else "faltaram"} '
                f'<span class="{"hl good" if bal >= 0 else "hl bad"}">{brl(abs(bal))}</span>.')
    sub = ""
    if potential > 0:
        sub = (f'<div class="hero-sub">Cortando só o supérfluo, você economiza '
               f'<span class="hl good">{brl(potential)}/mês</span>. Investida por {years} anos no Tesouro Selic, já descontado o IR, isso vira '
               f'<span class="hl good">{brl(future)}</span>.</div>')
    return f'<div class="hero"><div class="eyebrow">{icon_html}Seu mês em uma frase</div><div class="hero-h">{head}</div>{sub}</div>'


def build_insights(df: pd.DataFrame, month: pd.Period, spent_cur: pd.Series, spent_prev: pd.Series | None,
                   rec: pd.DataFrame, outliers: pd.DataFrame, cur: dict) -> list[tuple[str, str, str]]:
    """Até 4 achados curtos: (ícone, título, texto)."""
    out: list[tuple[str, str, str]] = []
    month_out = outliers[outliers["date"].dt.to_period("M") == month] if not outliers.empty else outliers
    skip = set(month_out["category"]) if not month_out.empty else set()  # já tem card próprio (nº 4)

    # 1. Categoria que mais subiu (ou, sem comparação, a que mais pesa)
    if spent_prev is not None and not spent_prev.empty:
        diffs = [(c, v, float(spent_prev.get(c, 0))) for c, v in spent_cur.items()]
        diffs = [(c, v, p, (v - p) / p * 100) for c, v, p in diffs if p > 0 and v - p >= 50 and c not in skip]
        if diffs:
            c, v, p, pct = max(diffs, key=lambda t: t[3])
            out.append(("trend", f"{c} subiu {pct:.0f}%", f"{brl(v)} neste mês contra {brl(p)} no anterior."))
    if not out and not spent_cur.empty:
        c, v = spent_cur.index[0], float(spent_cur.iloc[0])
        out.append(("tag", f"{c} pesa mais", f"{brl(v)}, {v / spent_cur.sum() * 100:.0f}% dos seus gastos do mês."))

    # 2. Dia da semana mais caro (média histórica)
    exp = df[df["amount"] < 0]
    if not exp.empty:
        per_day = (-exp.groupby("date")["amount"].sum()).groupby(lambda d: d.weekday()).mean()
        wd = int(per_day.idxmax())
        out.append(("calendar", f"{WEEKDAYS[wd].capitalize()} é o dia mais caro", f"Você gasta em média {brl(per_day.max())} nesse dia."))

    # 3. Gastos recorrentes
    if not rec.empty:
        total = float(rec["monthly"].sum())
        out.append(("repeat", f"{len(rec)} gastos fixos recorrentes", f"{brl(total)} por mês, {brl(total * 12)} por ano. Vale revisar."))

    # 4. Gasto fora do padrão no mês, ou uma boa notícia
    if not month_out.empty:
        r = month_out.iloc[0]
        out.append(("alert", "Compra fora do padrão",
                    f"{html.escape(str(r['description'])).title()}: {brl(r['value'])}, {r['ratio']:.0f}x o maior outro gasto de {r['category']}."))
    elif cur["income"] > 0 and cur["savings_rate"] >= 20:
        out.append(("check", "Meta de poupança batida", f"Você poupou {cur['savings_rate']:.0f}% da renda neste mês."))
    return out[:4]


def cards_html(items: list[tuple[str, str, str]], icon) -> str:
    cards = "".join(f'<div class="insight"><div class="ic">{icon(i)}</div><div class="it">{html.escape(t)}</div>'
                    f'<div class="tx">{tx}</div></div>' for i, t, tx in items)
    return f'<div class="insights">{cards}</div>'
