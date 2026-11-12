"""Página 3: Investir. Mostra, de forma visual, o que a economia vira em cada produto conhecido."""
from __future__ import annotations

import streamlit as st

import savings
from ui import *  # noqa: F401,F403

ctx = st.session_state["ctx"]
df, reserve = ctx["df"], ctx["reserve"]
snap = savings.snapshot(df, ctx["budgets"], reserve, core.project_month(df, sorted(df["month"].unique())[-1])["is_open"])
target = float(snap["avg"].reindex(savings.NEEDS).fillna(0).sum()) * 6
R = get_rates()

st.markdown('<p class="page-title">Investir</p>'
            '<p class="page-sub">Escolha quanto investir por mês e veja, ano a ano, quanto é dinheiro seu e quanto são '
            'juros. Depois compare os investimentos mais conhecidos.</p>', unsafe_allow_html=True)

# ---- Passo 1: reserva de emergência ----
pct = min(reserve / target * 100, 100) if target else 0
tone = "ok" if pct >= 100 else "warn" if pct >= 50 else "over"
msg = ("Reserva completa. Você pode investir com mais tranquilidade." if pct >= 100 else
       "Antes de buscar mais retorno, complete a reserva em Tesouro Selic ou CDB com liquidez diária.")
st.markdown(
    f'<div class="card"><div class="card-title">Passo 1: reserva de emergência</div>'
    f'<div class="card-sub">O ideal é ter 6 meses de gastos essenciais guardados antes de assumir qualquer risco.</div>'
    f'<div class="brow"><div class="bhead"><span>{brl(reserve)} de {brl(target)}</span><span>{pct:.0f}%</span></div>'
    f'<div class="bar"><div class="fill {tone}" style="width:{pct:.0f}%"></div></div></div>'
    f'<div class="alert">{msg} Informe o valor atual na barra lateral.</div></div>', unsafe_allow_html=True)

# ---- Passo 2: parâmetros ----
st.markdown(heading("Passo 2: monte a sua simulação"), unsafe_allow_html=True)
suggested = int(round(st.session_state.get("economia", 0) / 10) * 10) 
p1, p2, p3, p4 = st.columns(4)
monthly = p1.number_input("Quanto investir por mês (R$)", min_value=0, value=suggested, step=50,
                          help="Sugestão vinda do plano da página Economizar.")
initial = p2.number_input("Quanto já tem para começar (R$)", min_value=0, value=0, step=500)
years = p3.slider("Por quantos anos", 1, 30, 10)
names = [p["name"] for p in savings.PRODUCTS]
choice = p4.selectbox("Onde investir", names, index=1)
t1, t2 = st.columns(2)
use_ir = t1.toggle("Descontar imposto de renda", value=True, help="Aplica a tabela regressiva (22,5% a 15%) em CDB, Tesouro e similares.")
real = t2.toggle("Mostrar em valores de hoje", value=False, help="Desconta a inflação: mostra quanto o dinheiro compraria hoje.")
with st.expander("Taxas usadas na simulação (você pode mudar)"):
    if R["live"]:
        st.caption(f"Selic e IPCA vêm do Banco Central do Brasil (Selic {R['selic']:.2f}% a.a. em {R['selic_date']}).".replace(".", ",", 1))
    else:
        st.caption("Sem conexão com o Banco Central: usando valores de referência (Selic 13,75% a.a. em 04/11/2026).")
    a = st.columns(6)
    rates = {
        "cdi": a[0].number_input("CDI (% a.a.)", 0.0, 40.0, float(R["cdi"]), 0.25, help="Aproximadamente a Selic meta menos 0,10."),
        "poup": a[1].number_input("Poupança (% a.a.)", 0.0, 30.0, savings.POUPANCA, 0.1),
        "ipca": a[2].number_input("Tesouro IPCA+ (% a.a.)", 0.0, 30.0, float(R["ipca_plus"]), 0.25, help="IPCA em 12 meses mais 7% de juro real (premissa)."),
        "fii": a[3].number_input("Fundos imobiliários (% a.a.)", 0.0, 40.0, savings.FII_RETURN, 0.5, help="Premissa. Não é garantia."),
        "rv": a[4].number_input("Fundos de índice (% a.a.)", 0.0, 40.0, savings.RV_RETURN, 0.5, help="Premissa de longo prazo. Não é garantia."),
    }
    inflation = a[5].number_input("Inflação (% a.a.)", 0.0, 30.0, float(R["ipca12"]), 0.1, help="Usada quando você pede valores de hoje.")

prod = next(p for p in savings.PRODUCTS if p["name"] == choice)
sims = {p["name"]: savings.simulate(monthly, savings.product_rate(p, rates), years, initial,
                                    ir=p["ir"] if use_ir else "isento", inflation_pct=inflation if real else 0.0)
        for p in savings.PRODUCTS}
sim = sims[choice]
final, put, interest = sim["balance"][-1], sim["principal"][-1], sim["interest"][-1]
st.caption(f"{choice}: {prod['who']} Risco {prod['risk'].lower()}. Exemplos: {prod['examples']}. "
           f"Imposto: {savings.IR_LABEL[prod['ir']].lower()}{'' if use_ir else ' (desligado na simulação)'}.")

if not (monthly or initial):
    st.info("Informe um valor para investir por mês (ou um valor inicial) para ver a simulação.")
    st.stop()

# ---- Resposta em uma frase + números ----
unit = " em valores de hoje" if real else ""
st.markdown(
    f'<div class="hero"><div class="eyebrow">{icon("trend", size=18)}O resultado</div><div class="hero-h">'
    f'Investindo <span class="hl">{brl(monthly)}</span> por mês durante {years} anos em <span class="hl">{choice}</span>, '
    f'você terá <span class="hl good">{brl(final)}</span>{unit}.</div>'
    f'<div class="hero-sub">{brl(put)} saíram do seu bolso e <span class="hl good">{brl(interest)}</span> vieram dos juros'
    f'{f", {interest / put * 100:.0f}% a mais do que você colocou" if put else ""}'
    f'{", já descontado o imposto" if use_ir and prod["ir"] != "isento" else ""}.</div></div>', unsafe_allow_html=True)
st.write("")
k1, k2, k3 = st.columns(3)
k1.markdown(stat_card("Dinheiro que você coloca", brl(put), f"{brl(monthly)} por mês"), unsafe_allow_html=True)
k2.markdown(stat_card("Juros ganhos", brl(interest), "trabalho do tempo", "good"), unsafe_allow_html=True)
k3.markdown(stat_card(f"Total em {years} anos", brl(final), "valores de hoje" if real else ""), unsafe_allow_html=True)
st.write("")

# ---- Gráfico 1: dinheiro seu x juros ----
x = list(range(years + 1))
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=sim["principal"], name="Dinheiro que você coloca", mode="lines", stackgroup="one",
                         line=dict(width=1, color=CYAN), fillcolor="rgba(56,189,248,0.55)",
                         hovertemplate="Ano %{x}<br>Seu dinheiro: R$ %{y:,.2f}<extra></extra>"))
fig.add_trace(go.Scatter(x=x, y=sim["interest"], name="Juros acumulados", mode="lines",
                         stackgroup="one", line=dict(width=1, color="#34D399"), fillcolor="rgba(52,211,153,0.6)",
                         hovertemplate="Ano %{x}<br>Juros: R$ %{y:,.2f}<extra></extra>"))
fig.add_annotation(x=years, y=final, text=f"<b>{brl(final)}</b>", showarrow=True, ax=-70, ay=-30,
                   arrowcolor="#94A3B8", font=dict(color="#F8FAFC", size=14))
fig.update_xaxes(title="Anos investindo", dtick=max(years // 10, 1))
fig.update_yaxes(title="Valor acumulado", tickprefix="R$ ", tickformat=",.0f")
with st.container(border=True):
    st.markdown('<div class="card-title">Como o seu dinheiro cresce</div>'
                '<div class="card-sub">A área azul é o que você coloca. A verde são os juros. '
                'Com o tempo, o verde cresce mais rápido que o azul: é o juro composto.</div>', unsafe_allow_html=True)
    st.plotly_chart(style_fig(fig, 360), config=CHART_CFG, **WIDTH)

# ---- Gráfico 2: comparação entre investimentos ----
PCOL = {"Poupança": "#94A3B8", "Tesouro Selic": "#3B82F6", "CDB 100% do CDI": "#38BDF8", "LCI / LCA": "#14B8A6",
        "Tesouro IPCA+": "#6366F1", "Fundos imobiliários": "#A855F7", "Fundos de índice (ETFs)": "#D946EF"}
order = sorted(sims, key=lambda n: sims[n]["balance"][-1])
bars = go.Figure(go.Bar(y=order, x=[sims[n]["balance"][-1] for n in order], orientation="h",
                        marker=dict(color=[PCOL[n] for n in order],
                                    line=dict(color=["#F8FAFC" if n == choice else "rgba(0,0,0,0)" for n in order], width=2)),
                        text=[brl(sims[n]["balance"][-1]) for n in order], textposition="outside", cliponaxis=False,
                        textfont=dict(color="#E2E8F0", size=13), hovertemplate="%{y}<br>R$ %{x:,.2f}<extra></extra>"))
bars.update_layout(margin=dict(l=0, r=110, t=10, b=0), showlegend=False)
bars.update_xaxes(visible=False)
with st.container(border=True):
    st.markdown(f'<div class="card-title">Qual investimento rende mais em {years} anos?</div>'
                '<div class="card-sub">Mesmo valor, mesmo prazo, produtos diferentes'
                f'{", já com imposto" if use_ir else ""}. Cada produto tem a sua cor; '
                'a barra com contorno branco é a que você escolheu.</div>', unsafe_allow_html=True)
    st.plotly_chart(style_fig(bars, 70 + 46 * len(order)), config=CHART_CFG, **WIDTH)

# ---- Tabela de produtos ----
st.markdown(heading("Conheça cada investimento", "Exemplos reais de onde encontrar cada um. Não é recomendação."), unsafe_allow_html=True)
rows = [[p["name"], p["examples"], p["risk"], savings.IR_LABEL[p["ir"]], f'{savings.product_rate(p, rates):.1f}% a.a.'.replace(".", ","),
         brl(sims[p["name"]]["balance"][-1])] for p in savings.PRODUCTS]
st.markdown(html_table(["Investimento", "Exemplos", "Risco", "Imposto", "Retorno bruto", f"Em {years} anos"], rows, right=(4, 5)),
            unsafe_allow_html=True)
st.caption("O imposto dos fundos imobiliários é simplificado: considero o retorno como rendimentos mensais, isentos para pessoa física. "
           "ETFs pagam 15% sobre o ganho. Renda variável oscila: o retorno é uma premissa, não uma promessa. "
           "Simulação educativa, não é recomendação de investimento.")
