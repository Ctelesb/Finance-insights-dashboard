"""Página 4: Metas. Acompanhe objetivos com prazo e veja quanto guardar por mês para chegar lá."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import savings
from ui import *  # noqa: F401,F403

ctx = st.session_state["ctx"]
df, budgets, reserve = ctx["df"], ctx["budgets"], ctx["reserve"]
R = get_rates()
today = pd.Timestamp.today().normalize()
snap = savings.snapshot(df, budgets, reserve, core.project_month(df, sorted(df["month"].unique())[-1])["is_open"])
economia = st.session_state.get("economia") or savings.default_plan(df, snap["months"])
COLS = ["Meta", "Valor alvo", "Já guardado", "Prazo"]

st.markdown('<p class="page-title">Metas</p><p class="page-sub">Escreva o que você quer conquistar, quanto custa e até quando. '
            'O app calcula quanto guardar por mês e se isso cabe no seu plano de economia.</p>', unsafe_allow_html=True)

if "goals_df" not in st.session_state:
    emergency = round(float(snap["avg"].reindex(savings.NEEDS).fillna(0).sum()) * 6, -2)
    st.session_state["goals_df"] = pd.DataFrame([
        {"Meta": "Reserva de emergência", "Valor alvo": emergency, "Já guardado": float(reserve),
         "Prazo": (today + pd.DateOffset(months=12)).date()},
        {"Meta": "Viagem", "Valor alvo": 6000.0, "Já guardado": 0.0, "Prazo": (today + pd.DateOffset(months=18)).date()}])

st.markdown(heading("Suas metas", "Clique em uma célula para editar. Use a última linha para adicionar uma meta nova."), unsafe_allow_html=True)
edited = st.data_editor(
    st.session_state["goals_df"], num_rows="dynamic", hide_index=True, **WIDTH,
    column_config={"Meta": st.column_config.TextColumn("Meta", required=True),
                   "Valor alvo": st.column_config.NumberColumn("Valor alvo", format="R$ %.2f", min_value=0.0, step=100.0),
                   "Já guardado": st.column_config.NumberColumn("Já guardado", format="R$ %.2f", min_value=0.0, step=100.0),
                   "Prazo": st.column_config.DateColumn("Prazo", format="DD/MM/YYYY")})
st.session_state["goals_df"] = edited

with st.expander("Salvar ou carregar suas metas"):
    st.caption("O app não guarda nada entre visitas. Baixe o arquivo para continuar depois.")
    records = json.dumps(edited.astype(str).to_dict("records"), ensure_ascii=False, indent=1)
    st.download_button("Baixar metas (JSON)", records, "metas.json", "application/json")
    up = st.file_uploader("Carregar metas salvas", type=["json"], key="goals_up")
    if up is not None and st.session_state.get("goals_loaded") != (up.name, up.size):
        try:
            loaded = pd.DataFrame(json.loads(up.getvalue().decode("utf-8")))[COLS]
            loaded["Prazo"] = pd.to_datetime(loaded["Prazo"]).dt.date
            loaded[["Valor alvo", "Já guardado"]] = loaded[["Valor alvo", "Já guardado"]].astype(float)
            st.session_state["goals_df"], st.session_state["goals_loaded"] = loaded, (up.name, up.size)
            st.rerun()
        except (ValueError, KeyError, TypeError):
            st.error("Esse arquivo não parece ser de metas do Finance Insights.")

# ---- Cálculo por meta ----
cards, total_need = [], 0.0
for _, g in edited.iterrows():
    name, target, saved, due = str(g["Meta"] or "").strip(), float(g["Valor alvo"] or 0), float(g["Já guardado"] or 0), g["Prazo"]
    if not name or target <= 0 or pd.isna(due):
        continue
    due = pd.Timestamp(due)
    months_left = (due.year - today.year) * 12 + due.month - today.month
    remaining = max(target - saved, 0.0)
    pct = min(saved / target * 100, 100)
    if remaining == 0:
        tone, line = "ok", "Meta conquistada. Parabéns!"
    elif months_left < 1:
        tone, line = "over", f"O prazo já chegou e ainda faltam <b>{brl(remaining)}</b>. Defina uma nova data."
    else:
        need = savings.needed_monthly(remaining, R["cdi"], months_left, 0.175 if months_left > 12 else 0.0) if months_left >= 6 else remaining / months_left
        total_need += need
        tone = "ok" if need <= economia else "warn" if need <= economia * 1.5 else "over"
        where = ("Tesouro Selic ou CDB com liquidez diária" if months_left <= 12 else
                 "CDB, LCI/LCA ou Tesouro IPCA+" if months_left <= 60 else "Tesouro IPCA+ e fundos de índice")
        line = (f"Faltam <b>{brl(remaining)}</b> em {months_left} meses: guarde <b>{brl(need)}</b> por mês. "
                f"Sugestão de onde aplicar: {where}.")
    cards.append(f'<div class="card"><div class="card-title">{name}</div>'
                 f'<div class="card-sub">até {due:%d/%m/%Y}</div>'
                 f'<div class="brow"><div class="bhead"><span>{brl(saved)} de {brl(target)}</span><span>{pct:.0f}%</span></div>'
                 f'<div class="bar"><div class="fill {tone}" style="width:{pct:.0f}%"></div></div></div>'
                 f'<div class="alert">{line}</div></div>')

if cards:
    st.write("")
    gap = total_need - economia
    k1, k2, k3 = st.columns(3)
    k1.markdown(stat_card("Metas em andamento", str(len(cards))), unsafe_allow_html=True)
    k2.markdown(stat_card("Precisa guardar por mês", brl(total_need)), unsafe_allow_html=True)
    k3.markdown(stat_card("Seu plano de economia", brl(economia),
                          "cabe no plano" if gap <= 0 else f"faltam {brl(gap)} por mês", "good" if gap <= 0 else "bad"),
                unsafe_allow_html=True)
    st.write("")
    cols = st.columns(2)
    for i, card in enumerate(cards):
        cols[i % 2].markdown(card, unsafe_allow_html=True)
        cols[i % 2].write("")
else:
    st.info("Adicione uma meta na tabela acima para ver o plano.")
st.caption("Cálculo com o CDI atual e imposto estimado de 17,5% sobre os juros em metas de mais de 12 meses. "
           "Estimativa educativa, não é recomendação de investimento.")
