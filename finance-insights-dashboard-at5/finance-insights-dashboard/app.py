"""Finance Insights: ponto de entrada multi-page.

Rodar:  streamlit run app.py

- ui.py        tema (CSS), ícones, logo e barra lateral compartilhados
- core.py      lógica de dados (leitura do CSV, categorias, projeção, alertas)
- savings.py   economia, hábitos, score e produtos de investimento
- insights.py  textos de destaque e achados automáticos
- rates.py     Selic e IPCA do Banco Central (com valores de reserva)
- report.py    relatório mensal em PDF
- views/       uma página por arquivo (visão geral, economizar, investir, metas, categorias)
- assets/      logo (SVG) e ícone do app
"""
from pathlib import Path

import streamlit as st
from PIL import Image

st.set_page_config(page_title="Finance Insights | Telescode", layout="wide",
                   page_icon=Image.open(Path(__file__).parent / "assets" / "icon.png"))

import ui  # noqa: E402

ui.inject_css()
ui.setup()

pages = [
    st.Page("views/overview.py", title="Visão geral", icon=":material/dashboard:", url_path="visao-geral", default=True),
    st.Page("views/economizar.py", title="Economizar", icon=":material/savings:", url_path="economizar"),
    st.Page("views/investir.py", title="Investir", icon=":material/trending_up:", url_path="investir"),
    st.Page("views/metas.py", title="Metas", icon=":material/flag:", url_path="metas"),
    st.Page("views/categorias.py", title="Categorias", icon=":material/category:", url_path="categorias"),
]
st.navigation(pages).run()
