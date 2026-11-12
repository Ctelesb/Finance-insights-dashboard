"""Página 1: Visão geral (o dashboard original, sem alterações de lógica)."""
from __future__ import annotations

import streamlit as st

import insights
import report
import savings
from ui import *  # noqa: F401,F403  (tema, helpers, core, go, pd)

ctx = st.session_state["ctx"]
df, budgets, using_sample, reserve = ctx["df"], ctx["budgets"], ctx["using_sample"], ctx["reserve"]

# ==========================================================================
# 5. CABEÇALHO E SELEÇÃO DO MÊS
# ==========================================================================

months = sorted(df["month"].unique())
month = ctx["month"]  # escolhido na barra lateral e compartilhado por todas as páginas
page_header(f"Visão geral de {month_long(month)}",
            "Aqui você vê quanto entrou, quanto saiu, para onde o dinheiro foi e se o orçamento "
            "vai aguentar até o fim do mês.")

if using_sample:
    st.markdown(onboarding_html(), unsafe_allow_html=True)

# Todas as métricas abaixo são calculadas em core.py para o mês escolhido.
prev_month = month - 1
cur = core.month_totals(df, month)                                    # receitas, despesas, saldo
prev = core.month_totals(df, prev_month) if prev_month in months else None  # mês anterior (comparação)
proj = core.project_month(df, month)                                  # projeção até o fim do mês
spent_cat = core.spending_by_category(df, month)                      # gasto por categoria
status = core.budget_status(spent_cat, budgets)                       # ok / atenção / estourou
total_budget = sum(budgets.values())

# ==========================================================================
# 5.5 DESTAQUE: o mês em uma frase, score de saúde financeira e insights
# ==========================================================================

snap = savings.snapshot(df, budgets, reserve, core.project_month(df, months[-1])["is_open"])
rec = savings.recurring(df, snap["months"])
potential = st.session_state.get("economia") or savings.default_plan(df, snap["months"])
future = savings.simulate(potential, get_rates()["cdi"], 10)["balance"][-1]  # Tesouro Selic, líquido de IR
# Mês em aberto: usa o gasto projetado por categoria (fixos pelo valor típico, variáveis pelo ritmo diário).
ms = savings.month_score(df, month, budgets, reserve, core.projected_spending(df, month) if proj["is_open"] else None)
score = ms["score"]

h_l, h_r = st.columns([3, 2])
h_l.markdown(insights.hero_html(month, proj, cur, total_budget, potential, future, icon_html=icon("wallet", size=18)),
             unsafe_allow_html=True)
with h_r, st.container(border=True):
    st.markdown(f'<div class="card-title">Saúde financeira de {month_long(month)}</div>'
                '<div class="card-sub">Nota de 0 a 100 que muda com o mês escolhido, com o extrato e com a sua reserva.</div>',
                unsafe_allow_html=True)
    tone = GREEN if score >= 60 else AMBER if score >= 40 else RED
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number=dict(suffix="/100", font=dict(size=36, color="#F8FAFC")),
        gauge=dict(axis=dict(range=[0, 100], tickcolor=GRID, tickfont=dict(color=MUTED, size=11)),
                   bar=dict(color=tone, thickness=0.3), bgcolor="#172036", borderwidth=0,
                   steps=[dict(range=[0, 40], color="rgba(244,63,94,.20)"), dict(range=[40, 60], color="rgba(251,191,36,.20)"),
                          dict(range=[60, 100], color="rgba(52,211,153,.20)")])))
    st.plotly_chart(style_fig(gauge, 160).update_layout(margin=dict(l=24, r=24, t=10, b=0)), config=CHART_CFG, **WIDTH)
    label, label_tone = insights.score_status(score)
    st.markdown(f'<div style="text-align:center;margin:-4px 0 16px 0"><span class="pill {label_tone}">Situação: {label}</span></div>',
                unsafe_allow_html=True)
    parts = [("Poupança", ms["parts"]["Poupança"] / 50, f"{ms['save_rate']:.0f}% da renda (meta 20%)"),
             ("Orçamento", ms["parts"]["Orçamento"] / 30, f"{ms['within_budget']:.0f}% das categorias no limite"),
             ("Reserva", ms["parts"]["Reserva"] / 20, f"{ms['reserve_months']:.1f} de 6 meses")]
    st.markdown("".join(
        f'<div class="brow"><div class="bhead"><span>{n}</span><span>{t}</span></div><div class="bar">'
        f'<div class="fill {"ok" if f >= .75 else "warn" if f >= .4 else "over"}" style="width:{f * 100:.0f}%"></div></div></div>'
        for n, f, t in parts), unsafe_allow_html=True)

st.write("")
cards = insights.build_insights(df, month, spent_cat, core.spending_by_category(df, prev_month) if prev_month in months else None,
                                rec, core.find_outliers(df), cur)
if cards:
    st.markdown(heading("O que chamou atenção", "Achados automáticos do seu extrato, em uma frase cada."), unsafe_allow_html=True)
    st.markdown(insights.cards_html(cards, icon), unsafe_allow_html=True)
st.write("")
b1, b2, _ = st.columns([1, 1, 2])
b1.page_link("views/economizar.py", label="Ver como economizar mais", icon=":material/savings:")
b2.download_button("Baixar relatório do mês (PDF)", report.build_report(
    month_long(month), cur, proj, score, insights.score_status(score)[0],
    [(r.category, r.spent, r.limit, r.status) for r in status.itertuples()], cards, potential, potential * 12, using_sample),
    f"relatorio_{month}.pdf", "application/pdf")
st.write("")

# ==========================================================================
# 6. KPIs: receitas, despesas, saldo e gasto projetado
# ==========================================================================

k1, k2, k3, k4 = st.columns(4)
k1.markdown(kpi_card("Receitas", brl(cur["income"]),
                     core.pct_change(cur["income"], prev["income"]) if prev else None,
                     True, "", ico="income", tone="good"), unsafe_allow_html=True)
k2.markdown(kpi_card("Despesas", brl(cur["expenses"]),
                     core.pct_change(cur["expenses"], prev["expenses"]) if prev else None,
                     False, "", ico="expense", tone="bad"), unsafe_allow_html=True)
k3.markdown(kpi_card("Saldo do mês", brl(cur["balance"]),
                     core.pct_change(cur["balance"], prev["balance"]) if prev else None,
                     True, f'poupou {cur["savings_rate"]:.0f}% da renda', ico="wallet",
                     tone="good" if cur["balance"] >= 0 else "bad"), unsafe_allow_html=True)

if proj["is_open"]:
    # Mês em andamento: compara a projeção com o orçamento total.
    k4.markdown(kpi_card("Gasto projetado", brl(proj["projected"]),
                         core.pct_change(proj["projected"], total_budget) if total_budget else None,
                         False, f'hoje: {brl(proj["spent"])}', "vs orçamento total", ico="gauge",
                         tone="bad" if total_budget and proj["projected"] > total_budget else "good"),
                unsafe_allow_html=True)
else:
    # Mês fechado: não há o que projetar, mostra quanto do orçamento foi usado.
    used = proj["spent"] / total_budget * 100 if total_budget else 0
    k4.markdown(kpi_card("Orçamento usado", f"{used:.0f}%", None, False, "mês fechado", ico="gauge",
                         tone="bad" if used > 100 else "warn" if used >= 80 else "good"),
                unsafe_allow_html=True)

st.write("")

# ==========================================================================
# 7. ROSCA (gasto por categoria) + GASTO POR DIA
# ==========================================================================

c1, c2 = st.columns([1, 2])

with c1, st.container(border=True):
    st.markdown('<div class="card-title">Para onde foi o dinheiro</div><div class="card-sub">Cada cor é uma categoria. O valor no centro é o total gasto no mês.</div>', unsafe_allow_html=True)
    if spent_cat.empty:
        st.caption("Sem despesas neste mês.")
    else:
        colors = [CATEGORY_COLORS.get(c, FALLBACK_COLOR) for c in spent_cat.index]
        fig = go.Figure(go.Pie(
            labels=spent_cat.index, values=spent_cat.values, hole=0.72, sort=False,
            marker=dict(colors=colors, line=dict(color="#0A1122", width=3)),
            textinfo="none",
            hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>"))
        # Total no centro da rosca.
        fig.add_annotation(text=f"<b>{brl(spent_cat.sum())}</b>", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=15, color="#F8FAFC"))
        # Margem direita maior para a legenda não ser cortada.
        style_fig(fig, 300).update_layout(
            margin=dict(l=0, r=120, t=10, b=0),
            legend=dict(orientation="v", y=0.5, x=1.0, font=dict(color="#E2E8F0", size=12)))
        st.plotly_chart(fig, config=CHART_CFG, **WIDTH)

with c2, st.container(border=True):
    st.markdown('<div class="card-title">Gasto por dia</div><div class="card-sub">Verde: dentro da média. Amarelo: acima da média. Vermelho: mais que o dobro da média.</div>',
                unsafe_allow_html=True)
    daily = core.daily_spending(df, month)
    # A média considera só os dias já decorridos (importa em mês aberto).
    active = daily.loc[: int(proj["last_day"])]
    avg = active.mean() if len(active) else 0
    fig = go.Figure(go.Bar(
        x=daily.index, y=daily.values,
        marker=dict(color=[RED if v > 2 * avg else AMBER if v > avg else GREEN for v in daily.values],
                    pattern=dict(shape=["x" if v > 2 * avg else "/" if v > avg else "" for v in daily.values], fgcolor="rgba(255,255,255,.5)", size=7, solidity=.35)),
        hovertemplate="Dia %{x}<br>R$ %{y:,.2f}<extra></extra>"))
    fig.add_hline(y=avg, line=dict(color="#94A3B8", width=1, dash="dot"),
                  annotation_text=f"média {brl(avg)}", annotation_font_color=MUTED,
                  annotation_position="top left")
    fig.update_xaxes(dtick=2, title="Dia do mês")
    st.plotly_chart(style_fig(fig, 300), config=CHART_CFG, **WIDTH)

st.write("")

# ==========================================================================
# 8. PROJEÇÃO ACUMULADA + ORÇAMENTO POR CATEGORIA
# ==========================================================================

p1, p2 = st.columns([2, 1])

with p1, st.container(border=True):
    st.markdown('<div class="card-title">Gasto acumulado e projeção até o fim do mês</div><div class="card-sub">A linha tracejada mostra onde você chega no fim do mês se mantiver o ritmo.</div>',
                unsafe_allow_html=True)
    cum = core.cumulative_spending(df, month, int(proj["last_day"]))
    fig = go.Figure()
    # Linha sólida: o que já foi gasto.
    fig.add_trace(go.Scatter(
        x=cum.index, y=cum.values, mode="lines", name="Gasto acumulado",
        line=dict(color=CYAN, width=3), fill="tozeroy", fillcolor="rgba(56,189,248,0.18)",
        hovertemplate="Dia %{x}<br>R$ %{y:,.2f}<extra></extra>"))
    # Linha tracejada: para onde o gasto deve chegar no fim do mês.
    if proj["is_open"]:
        fig.add_trace(go.Scatter(
            x=[proj["last_day"], proj["days"]], y=[proj["spent"], proj["projected"]],
            mode="lines+markers", name="Projeção",
            line=dict(color=(RED if total_budget and proj["projected"] > total_budget else GREEN), width=3, dash="dash"), marker=dict(size=[0, 9]),
            hovertemplate="Dia %{x}<br>R$ %{y:,.2f}<extra></extra>"))
    # Linha de referência: orçamento total do mês.
    if total_budget:
        fig.add_hline(y=total_budget, line=dict(color="#F8FAFC", width=1, dash="dot"),
                      annotation_text=f"orçamento total {brl(total_budget)}",
                      annotation_font_color=MUTED, annotation_position="top left")
    fig.update_xaxes(range=[1, proj["days"]], title="Dia do mês")
    st.plotly_chart(style_fig(fig, 330), config=CHART_CFG, **WIDTH)

with p2:
    # Alerta de orçamento: banner no topo + uma barra por categoria.
    # Verde/ciano < 80%, laranja 80-100%, vermelho > 100% (regra em core.budget_status).
    over = status[status["status"] == "over"]
    warn = status[status["status"] == "warn"]

    rows = ""
    for r in status[status["limit"] > 0].itertuples():
        width = min(r.pct, 100)  # a barra nunca passa de 100% de largura
        rows += (f'<div class="brow"><div class="bhead"><span>{r.category}</span>'
                 f'<span>{brl(r.spent)} / {brl(r.limit)}</span></div>'
                 f'<div class="bar"><div class="fill {r.status}" style="width:{width:.0f}%"></div></div></div>')

    if len(over):
        banner = f'<div class="alert"><b>{len(over)} categoria(s) estouraram:</b> {", ".join(over["category"])}.</div>'
    elif len(warn):
        banner = f'<div class="alert"><b>{len(warn)} categoria(s) perto do limite.</b> Atenção até o fim do mês.</div>'
    else:
        banner = '<div class="alert">Tudo dentro do orçamento neste mês.</div>'

    st.markdown(f'<div class="card"><div class="card-title">Orçamento por categoria</div><div class="card-sub">Verde: dentro do limite. Amarelo: perto. Vermelho: estourou.</div>{banner}{rows}</div>',
                unsafe_allow_html=True)

st.write("")

# ==========================================================================
# 9. ABAS: transações, gastos atípicos e evolução mensal
# ==========================================================================

tab_tx, tab_out, tab_evo = st.tabs(["Transações", "Gastos atípicos", "Evolução mensal"])

with tab_tx:
    # Busca por texto + filtro por categoria, aplicados ao mês selecionado.
    f1, f2 = st.columns(2)
    query = f1.text_input("Buscar na descrição", placeholder="ex.: ifood, uber, aluguel")
    cats = f2.multiselect("Categorias", sorted(df["category"].unique()))
    view = df[df["month"] == month]
    if query:
        view = view[view["description"].str.contains(query, case=False, na=False, regex=False)]
    if cats:
        view = view[view["category"].isin(cats)]
    shown = view.sort_values("date", ascending=False).head(500)  # limite evita página pesada
    st.markdown(html_table(
        ["Data", "Descrição", "Categoria", "Valor"],
        [[r.date.strftime("%d/%m/%Y"), r.description, r.category, brl(r.amount)] for r in shown.itertuples()],
        right=(3,)), unsafe_allow_html=True)
    if len(view) > len(shown):
        st.caption(f"Mostrando as {len(shown)} transações mais recentes de {len(view)}. Use a busca ou baixe o CSV.")
    # Exporta o extrato inteiro já categorizado (separador ; e vírgula decimal, abre direto no Excel BR).
    export = (df.assign(month=df["month"].astype(str))
                .to_csv(sep=";", decimal=",", index=False).encode("utf-8-sig"))
    st.download_button("Baixar extrato categorizado (CSV)", export, "extrato_categorizado.csv", "text/csv")

with tab_out:
    # Gasto atípico = despesa bem acima do padrão da própria categoria (core.find_outliers).
    st.caption("Despesas pelo menos 2x maiores que o maior outro gasto da mesma categoria.")
    outliers = core.find_outliers(df)
    if outliers.empty:
        st.info("Nenhum gasto fora do padrão encontrado.")
    else:
        st.markdown(html_table(
            ["Data", "Descrição", "Categoria", "Valor", "Maior outro gasto", "Vezes maior"],
            [[r.date.strftime("%d/%m/%Y"), r.description, r.category, brl(r.value),
              brl(r.others_max), f"{r.ratio:.1f}x"] for r in outliers.itertuples()],
            right=(3, 4, 5)), unsafe_allow_html=True)

with tab_evo:
    # Receitas x despesas de todos os meses do extrato.
    summary = core.monthly_summary(df)
    labels = [month_label(m) for m in summary["month"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=summary["income"], name="Receitas", marker=dict(color=GREEN)))
    fig.add_trace(go.Bar(x=labels, y=summary["expenses"], name="Despesas", marker=dict(color=RED, pattern=dict(shape="/", fgcolor="rgba(255,255,255,.5)", size=7, solidity=.35))))
    fig.update_layout(barmode="group")
    st.plotly_chart(style_fig(fig, 340), config=CHART_CFG, **WIDTH)
