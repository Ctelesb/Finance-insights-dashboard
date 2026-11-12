"""Página 2: Economizar. Mostra onde cortar, quanto cada corte rende e o que isso vira em um ano."""
from __future__ import annotations

import streamlit as st

import insights
import savings
from ui import *  # noqa: F401,F403

ctx = st.session_state["ctx"]
df, budgets, reserve, month = ctx["df"], ctx["budgets"], ctx["reserve"], ctx["month"]

snap = savings.snapshot(df, budgets, reserve, core.project_month(df, sorted(df["month"].unique())[-1])["is_open"])
months, income, spend, avg = snap["months"], snap["income"], snap["spend"], snap["avg"]
proj = core.project_month(df, month)
ms = savings.month_score(df, month, budgets, reserve, core.projected_spending(df, month) if proj["is_open"] else None)
score = ms["score"]

rec = savings.recurring(df, months)
rec = rec.assign(category=rec["description"].map(savings.habit_of).fillna("Outros fixos"))
hs = savings.habit_stats(df, months)
HABIT = {n: (pct, tip) for n, _, pct, tip in savings.HABITS}

page_header("Economizar", f"Descubra o que dá para cortar sem abrir mão do essencial. Os valores são a média "
            f"de {len(months)} meses fechados do seu extrato.")
summary = st.container()  # preenchido no fim, quando o plano já foi montado

# ---- Passo 1: assinaturas e gastos fixos ----
st.markdown(heading("1. Assinaturas e gastos fixos",
                    "São cobranças que se repetem todo mês com o mesmo valor. Marque as que você cancelaria ou renegociaria."),
            unsafe_allow_html=True)
if rec.empty:
    st.caption("Nenhum gasto recorrente encontrado.")
    cancelled: list[str] = []
else:
    labels = {r.description: f"{r.description.title()} ({brl(r.monthly)}/mês)" for r in rec.itertuples()}
    st.markdown(f'<div class="alert">Você paga <b>{brl(rec["monthly"].sum())}</b> por mês nestes {len(rec)} itens, '
                f'ou <b>{brl(rec["monthly"].sum() * 12)}</b> por ano.</div>', unsafe_allow_html=True)
    cancelled = st.multiselect("Quais você cancelaria ou renegociaria?", list(labels), format_func=labels.get)
cancel_by_habit = rec[rec["description"].isin(cancelled)].groupby("category")["monthly"].sum()

# ---- Passo 2: hábitos de consumo ----
st.markdown(heading("2. Hábitos que pesam no bolso",
                    "Para cada hábito mostramos quanto você gasta, quantas vezes e o valor médio de cada compra. "
                    "Use o controle ao lado para escolher quanto reduzir."), unsafe_allow_html=True)
cuts: dict[str, int] = {}
if hs.empty:
    st.caption("Não encontrei hábitos de consumo no extrato.")
for name, r in hs.iterrows():
    left, right = st.columns([3, 2])
    left.markdown(
        f'<div class="card"><div class="card-title">{name}</div>'
        f'<div class="kpi-value">{brl(r["monthly"])}<span style="font-size:16px;color:#94A3B8"> por mês</span></div>'
        f'<div class="kpi-foot"><span>{r["times"]:.0f} vezes por mês, {brl(r["ticket"])} cada. {HABIT[name][1]}</span></div></div>',
        unsafe_allow_html=True)
    with right:
        cuts[name] = st.slider(f"Reduzir {name.lower()}", 0, 100, HABIT[name][0], 5, format="%d%%", key=f"cut_{name}")
        base = max(float(r["monthly"]) - float(cancel_by_habit.get(name, 0)), 0)
        st.caption(f"Economia: {brl(base * cuts[name] / 100)} por mês")

plan = savings.plan_savings(hs["monthly"], rec, cancelled, cuts)
st.session_state["economia"] = plan["monthly"]  # vira o aporte sugerido na página Investir

# ---- Resumo no topo (preenchido agora) ----
with summary:
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(stat_card("Renda média por mês", brl(income)), unsafe_allow_html=True)
    k2.markdown(stat_card("Gasto médio por mês", brl(spend), f"poupa {snap['save_rate']:.0f}% da renda",
                          "good" if snap["save_rate"] >= 20 else "bad"), unsafe_allow_html=True)
    k3.markdown(stat_card("Você pode economizar", brl(plan["monthly"]), f"{brl(plan['yearly'])} por ano", "good"),
                unsafe_allow_html=True)
    k4.markdown(stat_card(f"Saúde financeira de {month_long(month)}", f"{score}/100",
                          insights.score_status(score)[0], insights.score_status(score)[1]), unsafe_allow_html=True)
    st.write("")

# ---- Antes x depois ----
st.write("")
c1, c2 = st.columns([2, 1])
with c1, st.container(border=True):
    st.markdown('<div class="card-title">Hábitos: hoje x com o seu plano</div>'
                '<div class="card-sub">Amarelo é o que você gasta hoje por mês. Verde é o que passaria a gastar.</div>',
                unsafe_allow_html=True)
    names = list(hs.index)[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=[hs.loc[n, "monthly"] for n in names], name="Hoje", orientation="h",
                         marker=dict(color=AMBER, pattern=dict(shape="/", fgcolor="rgba(255,255,255,.5)", size=7, solidity=.35)), hovertemplate="%{y}<br>R$ %{x:,.2f}<extra>Hoje</extra>"))
    fig.add_trace(go.Bar(y=names, x=[hs.loc[n, "monthly"] - plan["by_category"].get(n, 0) for n in names],
                         name="Com o plano", orientation="h", marker=dict(color=GREEN),
                         hovertemplate="%{y}<br>R$ %{x:,.2f}<extra>Com o plano</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
    st.plotly_chart(style_fig(fig, 380), config=CHART_CFG, **WIDTH)
with c2:
    r = savings.rule_503020(avg, income)
    tips = [f"Necessidades: <b>{r['needs']:.0f}%</b> da renda (ideal até 50%).",
            f"Desejos: <b>{r['wants']:.0f}%</b> da renda (ideal até 30%).",
            f"Sobra para poupar: <b>{r['save']:.0f}%</b> (ideal 20% ou mais)."]
    if ms["reserve_months"] < 6:
        tips.append(f"Sua reserva cobre <b>{ms['reserve_months']:.1f}</b> de 6 meses de gastos essenciais.")
    st.markdown('<div class="card"><div class="card-title">Regra 50/30/20</div>'
                '<div class="card-sub">Um guia simples: metade da renda para o essencial, 30% para desejos e 20% para o futuro.</div>'
                + "".join(f'<div class="alert">{t}</div>' for t in tips) + '</div>', unsafe_allow_html=True)

# ---- O que o plano vira ----
st.write("")
months_saved = plan["yearly"] / income if income else 0
st.markdown(
    f'<div class="hero"><div class="eyebrow">{icon("target", size=18)}O que esse plano vira</div>'
    f'<div class="hero-h">Você guarda <span class="hl good">{brl(plan["monthly"])}</span> por mês, '
    f'<span class="hl good">{brl(plan["yearly"])}</span> em um ano. É como guardar <span class="hl">{months_saved:.1f} meses</span> inteiros de renda.</div>'
    f'<div class="hero-sub">Dinheiro parado perde para a inflação. Veja na próxima página quanto ele pode render.</div></div>',
    unsafe_allow_html=True)
st.write("")
st.page_link("views/investir.py", label="Investir essa economia", icon=":material/trending_up:")
