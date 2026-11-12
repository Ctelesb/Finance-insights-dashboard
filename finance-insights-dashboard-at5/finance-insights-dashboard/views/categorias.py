"""Página 5: Categorias. Ensine o app a classificar as despesas do seu jeito."""
from __future__ import annotations

import json

import streamlit as st

from ui import *  # noqa: F401,F403

ctx = st.session_state["ctx"]
df = ctx["df"]
overrides = st.session_state.setdefault("overrides", {})

exp = df[df["amount"] < 0].copy()
exp["regra"] = exp["description"].map(core.rule_key)
total = float(-exp["amount"].sum())
others = float(-exp[exp["category"] == "Outros"]["amount"].sum())
share = others / total * 100 if total else 0.0

st.markdown('<p class="page-title">Categorias</p><p class="page-sub">Quanto mais despesas ficam na categoria certa, mais '
            'confiáveis são os gráficos, a nota e as dicas de economia. Corrija uma vez e o app aplica a regra a todas as '
            'transações parecidas, em qualquer mês.</p>', unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
k1.markdown(stat_card("Despesas em \"Outros\"", f"{share:.0f}%", "sem categoria definida", "good" if share < 10 else "warn" if share < 25 else "bad"),
            unsafe_allow_html=True)
k2.markdown(stat_card("Valor sem categoria", brl(others)), unsafe_allow_html=True)
k3.markdown(stat_card("Regras suas", str(len(overrides)), "valem para todo o extrato"), unsafe_allow_html=True)
st.write("")

st.markdown(heading("Classifique as despesas", "Escolha a categoria na última coluna e clique em Salvar regras."), unsafe_allow_html=True)
mode = st.radio("Mostrar", ["Sem categoria", "Todas as despesas"], horizontal=True, label_visibility="collapsed")
base = exp if mode == "Todas as despesas" else exp[exp["category"] == "Outros"]
grp = (base.groupby("regra").agg(Descrição=("description", "first"), Categoria=("category", lambda s: s.mode().iat[0]),
                                 Vezes=("amount", "size"), Total=("amount", lambda s: -s.sum()))
       .reset_index().sort_values("Total", ascending=False).reset_index(drop=True))
if grp.empty:
    st.success("Todas as despesas já têm categoria. Para revisar uma classificação, escolha \"Todas as despesas\".")
else:
    edited = st.data_editor(
        grp[["regra", "Descrição", "Vezes", "Total", "Categoria"]], hide_index=True, **WIDTH,
        disabled=["regra", "Descrição", "Vezes", "Total"],
        column_config={"regra": None, "Total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                       "Categoria": st.column_config.SelectboxColumn("Categoria", options=list(core.DEFAULT_BUDGETS), required=True)})
    if st.button("Salvar regras", type="primary"):
        merged = edited.merge(grp[["regra", "Categoria"]], on="regra", suffixes=("", "_antes"))
        changed = merged[merged["Categoria"] != merged["Categoria_antes"]]
        for row in changed.itertuples():
            overrides[row.regra] = row.Categoria
        if len(changed):
            st.rerun()
        st.info("Nenhuma categoria foi alterada.")

if overrides:
    st.markdown(heading("Suas regras", "Aplicadas a toda descrição parecida (números e símbolos são ignorados)."), unsafe_allow_html=True)
    st.markdown(html_table(["Descrição (padrão)", "Categoria"], [[k.title(), v] for k, v in sorted(overrides.items())]), unsafe_allow_html=True)
    st.write("")
    b1, b2 = st.columns(2)
    b1.download_button("Baixar regras (JSON)", json.dumps(overrides, ensure_ascii=False, indent=1), "regras_categorias.json", "application/json")
    if b2.button("Apagar todas as regras"):
        overrides.clear()
        st.rerun()
with st.expander("Carregar regras salvas"):
    st.caption("O app não guarda nada entre visitas. Baixe as regras e carregue de novo quando voltar.")
    up = st.file_uploader("Arquivo de regras (JSON)", type=["json"], key="rules_up")
    if up is not None and st.session_state.get("rules_loaded") != (up.name, up.size):
        try:
            data = json.loads(up.getvalue().decode("utf-8"))
            if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
                raise ValueError
            overrides.update({core.rule_key(k): v for k, v in data.items() if v in core.DEFAULT_BUDGETS})
            st.session_state["rules_loaded"] = (up.name, up.size)
            st.rerun()
        except ValueError:
            st.error("Esse arquivo não parece ser de regras do Finance Insights.")
