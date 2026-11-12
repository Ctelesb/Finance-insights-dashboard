"""Finance Insights: tema, helpers visuais e barra lateral compartilhados pelas páginas.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import rates

# ==========================================================================
# 1. CONFIGURAÇÃO DA PÁGINA, CORES E CONSTANTES
# ==========================================================================


# Paleta vibrante usada em todos os gráficos.
# Para mudar o visual do app inteiro, basta editar estas cores.
CYAN = "#38BDF8"      # destaque principal (receitas, dentro da média, "ok")
ORANGE = "#FBBF24"    # (alias de AMBER, mantido por compatibilidade)
RED = "#F43F5E"       # ruim: estourou o orçamento, saldo negativo, despesa
GREEN = "#34D399"     # bom: ganhos, dentro do limite
AMBER = "#FBBF24"     # alerta financeiro: atenção, perto do limite
MUTED = "#94A3B8"     # textos secundários
GRID = "#1C2026"      # linhas de grade dos gráficos

# Cada categoria tem sempre a mesma cor, em qualquer gráfico.
# Cada categoria tem uma cor própria e fria/neutra. Verde, amarelo e vermelho ficam
# reservados para dizer se algo está bom, em alerta ou ruim.
CATEGORY_COLORS = {
    "Moradia": "#3B82F6",      # azul: estabilidade
    "Mercado": "#14B8A6",      # verde-azulado: alimentação básica
    "Alimentação": "#8B5CF6",  # violeta
    "Transporte": "#38BDF8",   # azul-claro: movimento
    "Lazer": "#D946EF",        # magenta: diversão
    "Saúde": "#F472B6",        # rosa: cuidado
    "Educação": "#6366F1",     # índigo: conhecimento
    "Compras": "#CBD5E1",      # cinza claro
    "Outros": "#64748B",       # cinza escuro
}
FALLBACK_COLOR = "#2DD4BF"  # categorias sem cor definida (ex.: "Outras receitas")

MONTHS_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
# Marcador de versão: aparece na barra lateral. Serve para confirmar que o deploy atualizou.
APP_VERSION = "v6"
SAMPLE_PATH = Path(__file__).parent / "sample_data" / "extrato_exemplo.csv"

# Compatibilidade: o Streamlit >= 1.50 usa width="stretch";
# versões anteriores usam use_container_width.
_VERSION = tuple(int(x) for x in st.__version__.split(".")[:2])
WIDTH = {"width": "stretch"} if _VERSION >= (1, 50) else {"use_container_width": True}
CHART_CFG = {"displayModeBar": False}  # esconde a barra de ferramentas do Plotly

# ==========================================================================
# 2. ESTILO (CSS)
# ==========================================================================
# Os cards são HTML puro estilizado aqui. O tamanho do número dos KPIs fica
# em `.kpi-value`: ele encolhe sozinho em telas menores (clamp) e nunca
# quebra de linha (nowrap), então o valor fica sempre ao lado do "R$".

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap');
html, body, .stApp, button, input, textarea { font-family: 'Outfit', sans-serif !important; }
.stApp { background: radial-gradient(1100px 480px at 12% -8%, #101a33 0%, #050816 62%); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #080D1C; border-right: 1px solid #16203A; }

/* Cards */
.card { background: linear-gradient(180deg, #0F172A 0%, #0A1122 100%); border: 1px solid #1E293B;
        border-radius: 28px; padding: 20px 22px; height: 100%; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-title) {
  background: linear-gradient(180deg, #0F172A 0%, #0A1122 100%); border: 1px solid #1E293B;
  border-radius: 28px; padding: 10px 14px; }
.card-title { color: #94A3B8; font-size: 18px; font-weight: 500; margin-bottom: 6px; }

/* Número principal dos KPIs: menor que antes e sempre em uma linha só */
.kpi-value { color: #F8FAFC; font-size: clamp(24px, 2.3vw, 36px); font-weight: 400;
             letter-spacing: -0.3px; line-height: 1.1; white-space: nowrap; }
.kpi-foot { margin-top: 20px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px;
            color: #8091A7; font-size: 14px; }
.pill { background: #172036; border-radius: 999px; padding: 7px 14px; font-size: 14px; color: #E2E8F0; }
.pill { white-space: normal; line-height: 1.25; }
.pill.good { color: #34D399; } .pill.bad { color: #FB7185; } .pill.warn { color: #FBBF24; }

.page-title { color: #F8FAFC; font-size: 36px; font-weight: 500; margin: 0; }
.page-sub { color: #94A3B8; font-size: 18px; margin: 6px 0 26px 0; line-height: 1.5; }

/* Barras de orçamento por categoria */
.brow { margin-bottom: 14px; }
.bhead { display: flex; justify-content: space-between; color: #E2E8F0; font-size: 16px; margin-bottom: 8px; }
.bhead span:last-child { color: #94A3B8; }
.bar { height: 8px; background: #172036; border-radius: 99px; overflow: hidden; }
.fill { height: 100%; border-radius: 99px; }
.fill.ok { background: #34D399; } .fill.warn { background: #FBBF24; } .fill.over { background: #F43F5E; }
.alert { background: #172036; border-radius: 16px; padding: 10px 14px; margin-bottom: 14px;
         color: #E2E8F0; font-size: 16px; line-height: 1.5; }
.alert b { color: #FBBF24; font-weight: 500; }

/* Abas em formato de pílula */
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #0B1325; padding: 5px; border-radius: 999px; width: fit-content; }
.stTabs [data-baseweb="tab"] { height: 36px; border-radius: 999px; padding: 0 18px; color: #94A3B8; }
.stTabs [aria-selected="true"] { background: #F8FAFC !important; color: #080D1C !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
div[data-testid="stDataFrame"] { border-radius: 20px; overflow: hidden; }

/* Tema escuro garantido pelo próprio app.
   Mesmo que o .streamlit/config.toml não seja lido (ex.: pasta não enviada ao
   GitHub), campos, uploader, seletor e avisos continuam escuros. */
.stApp { color: #F1F5F9; color-scheme: dark; font-size: 16px; }
.stApp label, .stApp [data-testid="stWidgetLabel"] p, .stApp .stMarkdown p,
.stApp [data-testid="stCaptionContainer"], section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p { color: #CBD5E1; }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
[data-testid="stFileUploaderDropzone"], .stNumberInput button, .stTextInput input {
  background-color: #0E1629 !important; color: #F1F5F9 !important; border-color: #1E293B !important; }
[data-baseweb="input"] input, [data-baseweb="select"] div { color: #F1F5F9 !important; }
[data-testid="stFileUploaderDropzone"] button { background: #172036 !important; color: #F1F5F9 !important; }
[data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzone"] span { color: #94A3B8 !important; }
div[data-testid="stAlert"] { background: #0C2238 !important; border: 1px solid #17405F; border-radius: 16px; }
div[data-testid="stAlert"] p { color: #7DD3FC !important; }
ul[data-testid="stSelectboxVirtualDropdown"], [data-baseweb="popover"] ul { background: #0E1629 !important; }
[data-baseweb="popover"] li { color: #F1F5F9 !important; }

/* Tabelas em HTML (não dependem do tema do Streamlit, ao contrário do st.dataframe) */
.tbl-wrap { max-height: 380px; overflow: auto; border: 1px solid #1E293B; border-radius: 20px; background: #0A1122; }
.tbl { width: 100%; border-collapse: collapse; font-size: 15px; color: #E2E8F0; }
.tbl th { position: sticky; top: 0; background: #0F172A; color: #94A3B8; font-weight: 400;
          text-align: left; padding: 12px 16px; }
.tbl td { padding: 11px 16px; border-top: 1px solid #16203A; }
.tbl tr:hover td { background: #0E1629; }
.tbl .r { text-align: right; white-space: nowrap; }

/* Reforço do tema escuro em versões diferentes do Streamlit */
section[data-testid="stSidebar"] input, [data-testid="stNumberInputContainer"],
[data-testid="stNumberInput"] button, div[data-baseweb="select"] > div,
.stTextInput > div > div, [data-testid="stFileUploaderDropzone"] {
  background-color: #0E1629 !important; color: #F1F5F9 !important; border-color: #1E293B !important; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] label *, [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * { color: #CBD5E1 !important; }
[data-testid="stFileUploaderDropzone"] * { color: #94A3B8 !important; }
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] button * {
  background: #172036 !important; color: #F1F5F9 !important; }
[data-baseweb="checkbox"] > span:first-of-type { background: #0E1629 !important; border-color: #2B3A55 !important; }
.stTabs [data-baseweb="tab-list"] { border-bottom: none !important; }
.stTabs [data-baseweb="tab-list"] + div, .stTabs [role="tablist"] ~ div[aria-hidden="true"] { display: none !important; }
/* Destaque do topo e insights */
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.hero { background: radial-gradient(640px 240px at 0% 0%, rgba(56,189,248,.17), transparent 70%),
        linear-gradient(180deg, #0F172A 0%, #0A1122 100%); border: 1px solid #1E293B; border-radius: 28px;
        padding: 26px 30px; height: 100%; animation: rise .55s ease both; }
.hero .eyebrow { color: #38BDF8; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; margin-bottom: 12px; }
.hero-h { color: #F8FAFC; font-size: clamp(20px, 2.3vw, 30px); font-weight: 300; line-height: 1.3; }
.hero-sub { color: #AEB5BD; font-size: clamp(15px, 1.3vw, 18px); margin-top: 16px; line-height: 1.5; }
.hl { color: #38BDF8; font-weight: 500; } .hl.warn { color: #FBBF24; } .hl.bad { color: #FB7185; } .hl.good { color: #34D399; }
.insights { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
.insight { background: linear-gradient(180deg, #0F172A 0%, #0A1122 100%); border: 1px solid #1E293B;
           border-radius: 22px; padding: 16px 18px; animation: rise .6s ease both; transition: border-color .2s, transform .2s; }
.insight:hover { border-color: #38BDF855; transform: translateY(-2px); }
.insight .ic { font-size: 22px; margin-bottom: 8px; } .insight .it { color: #F8FAFC; font-size: 15px; font-weight: 500; }
.insight .tx { color: #94A3B8; font-size: 13px; margin-top: 4px; line-height: 1.45; }

/* Marca, ícones, seções e passos */
.kpi-top { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.kpi-top .card-title { margin: 0; }
.badge { width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center; flex: none; }
.badge .ico { display: block; }
.ico { vertical-align: middle; }
.brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 6px 0; }
.brand img { width: 46px; height: auto; }
.brand-name { color: #F8FAFC; font-weight: 600; letter-spacing: .14em; font-size: 19px; line-height: 1; }
.brand-name span { color: #38BDF8; letter-spacing: 0; margin-left: 3px; }
.brand-bar { height: 3px; border-radius: 99px; background: linear-gradient(90deg, #38BDF8, #818CF8); margin-top: 7px; }
.brand-sub { color: #94A3B8; font-size: 13px; margin-bottom: 8px; }
.card-sub { color: #94A3B8; font-size: 15px; margin: 0 0 14px 0; line-height: 1.45; }
.sec-h { color: #F8FAFC; font-size: 24px; font-weight: 500; margin: 6px 0 2px 0; }
.sec-s { color: #94A3B8; font-size: 16px; margin-bottom: 14px; }
.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 18px; }
.step { background: linear-gradient(180deg, #0F172A 0%, #0A1122 100%); border: 1px solid #1E293B; border-radius: 22px;
        padding: 18px 20px; animation: rise .5s ease both; }
.step .t { color: #F8FAFC; font-size: 17px; font-weight: 500; margin: 10px 0 4px 0; }
.step .d { color: #94A3B8; font-size: 15px; line-height: 1.45; }
.hero .eyebrow { display: flex; align-items: center; gap: 8px; }
[data-testid="stWidgetLabel"] p { font-size: 15px !important; }
.risk { border-radius: 999px; padding: 3px 10px; font-size: 13px; background: #172036; }
</style>
"""
def inject_css() -> None:
    """Aplica o tema em todas as páginas (roda a cada execução do app)."""
    st.markdown(CSS, unsafe_allow_html=True)


# ==========================================================================
# 3. FUNÇÕES AUXILIARES (formatação, cards e estilo dos gráficos)
# ==========================================================================

def brl(value: float) -> str:
    """Formata em reais no padrão brasileiro: 1234.5 -> 'R$ 1.234,50'."""
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def month_label(period: pd.Period) -> str:
    """Período -> 'Outubro 2026'."""
    return f"{MONTHS_PT[period.month - 1]} {period.year}"


_TONES = {"good": ("#34D399", "rgba(52,211,153,.15)"), "bad": ("#FB7185", "rgba(244,63,94,.15)"),
          "warn": ("#FBBF24", "rgba(251,191,36,.15)")}


def month_long(period: pd.Period) -> str:
    """Período -> 'outubro de 2026' (para frases e títulos)."""
    return f"{MONTHS_PT[period.month - 1].lower()} de {period.year}"


def kpi_card(title: str, value: str, delta: float | None, higher_is_good: bool,
             note: str, delta_label: str = "vs mês anterior", ico: str = "wallet", tone: str = "good") -> str:
    """Card de indicador com ícone em selo colorido (verde = bom, amarelo = alerta, vermelho = ruim).

    `delta` é a variação percentual; `higher_is_good` define a cor da pílula de variação.
    """
    if delta is None:
        pill = '<span class="pill">sem comparação</span>'
    else:
        good = (delta >= 0) == higher_is_good
        arrow = icon("up" if delta >= 0 else "down", "#34D399" if good else "#FB7185", 14)
        pill = f'<span class="pill {"good" if good else "bad"}">{arrow} {abs(delta):.0f}% {delta_label}</span>'
    fg, bg = _TONES[tone]
    # Tudo em uma linha só: linhas em branco ou recuos quebrariam o Markdown.
    return (f'<div class="card"><div class="kpi-top"><span class="badge" style="background:{bg}">{icon(ico, fg, 24)}</span>'
            f'<div class="card-title">{title}</div></div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-foot">{pill}<span>{note}</span></div></div>')


def style_fig(fig: go.Figure, height: int = 300) -> go.Figure:
    """Aplica o tema escuro e transparente a qualquer gráfico Plotly."""
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color=MUTED, size=13),
        legend=dict(orientation="h", y=-0.15, font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor="#172036", font_color="#F8FAFC", bordercolor="#2B3A55"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def html_table(headers: list[str], rows: list[list[str]], right: tuple[int, ...] = ()) -> str:
    """Tabela em HTML com o tema do app.

    Usada no lugar do st.dataframe, que desenha em canvas e fica branco quando
    o tema do Streamlit (.streamlit/config.toml) não é carregado.
    `right` lista os índices das colunas alinhadas à direita (valores).
    """
    th = "".join(f'<th class="{"r" if i in right else ""}">{html.escape(h)}</th>' for i, h in enumerate(headers))
    body = "".join(
        "<tr>" + "".join(f'<td class="{"r" if i in right else ""}">{html.escape(str(c))}</td>'
                         for i, c in enumerate(row)) + "</tr>"
        for row in rows)
    # Tudo em uma linha só, para o Markdown não interpretar como bloco de código.
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


@st.cache_data(show_spinner=False)
def load(source: bytes | str, invert_sign: bool, overrides: tuple = ()) -> pd.DataFrame:
    """Lê e categoriza o extrato (com as regras do usuário). O cache evita reprocessar a cada clique."""
    return core.load_statement(source, invert_sign=invert_sign, overrides=dict(overrides))


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def get_rates() -> dict:
    """Selic e IPCA do Banco Central, atualizados a cada 6 horas (com valores de reserva se não houver conexão)."""
    return rates.fetch()


# ==========================================================================
# 4. ÍCONES (imagens SVG), LOGO E BARRA LATERAL
# ==========================================================================
import base64  # noqa: E402
from functools import lru_cache  # noqa: E402

_ICONS = {
    "trend": '<polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/>',
    "repeat": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "alert": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "check": '<circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9"/>',
    "tag": '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><circle cx="7" cy="7" r="1"/>',
    "wallet": '<path d="M3 7a2 2 0 0 1 2-2h14v4"/><path d="M3 7v11a2 2 0 0 0 2 2h16V9H5a2 2 0 0 1-2-2z"/><circle cx="17" cy="14" r="1"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "up": '<polyline points="18 15 12 9 6 15"/>',
    "down": '<polyline points="6 9 12 15 18 9"/>',
    "income": '<path d="M17 7L7 17"/><path d="M17 17H7V7"/>',
    "expense": '<path d="M7 17L17 7"/><path d="M7 7h10v10"/>',
    "gauge": '<circle cx="12" cy="12" r="10"/><path d="M12 12l4-4"/><circle cx="12" cy="12" r="1"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
}


@lru_cache(maxsize=None)
def icon(name: str, color: str = "#38BDF8", size: int = 24) -> str:
    """Ícone como imagem SVG embutida (nada de emoji)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_ICONS[name]}</svg>')
    return f'<img class="ico" width="{size}" height="{size}" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"/>'


_MARK = ('<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38BDF8"/>'
         '<stop offset="1" stop-color="#818CF8"/></linearGradient></defs>'
         '<rect x="2.5" y="2.5" width="59" height="51" rx="9" fill="none" stroke="url(#g)" stroke-width="4"/>'
         '<line x1="2.5" y1="17" x2="61.5" y2="17" stroke="url(#g)" stroke-width="3.5"/>'
         '<circle cx="12" cy="9.8" r="2.4" fill="#38BDF8"/><circle cx="20" cy="9.8" r="2.4" fill="#38BDF8"/>'
         '<circle cx="28" cy="9.8" r="2.4" fill="#38BDF8"/>'
         '<g fill="none" stroke="url(#g)" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round">'
         '<polyline points="22,28 14,36 22,44"/><line x1="36" y1="25" x2="28" y2="47"/>'
         '<polyline points="42,28 50,36 42,44"/></g>')


@lru_cache(maxsize=1)
def logo_html() -> str:
    """Logo Telescode (símbolo igual ao de assets/logo.svg) para a barra lateral."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 56">{_MARK}</svg>'
    b64 = base64.b64encode(svg.encode()).decode()
    return (f'<div class="brand"><img src="data:image/svg+xml;base64,{b64}"/><div>'
            f'<div class="brand-name">TELESCODE<span>&lt;/&gt;</span></div><div class="brand-bar"></div></div></div>'
            f'<div class="brand-sub">Finance Insights</div>')


def heading(title: str, sub: str = "") -> str:
    return f'<div class="sec-h">{title}</div>' + (f'<div class="sec-s">{sub}</div>' if sub else "")


def onboarding_html() -> str:
    steps = [("upload", "1. Envie seu extrato", "Suba o CSV do seu banco na barra lateral. Por enquanto você vê dados de exemplo."),
             ("chart", "2. Entenda o seu mês", "Veja quanto gastou, para onde foi e se o orçamento vai aguentar até o fim."),
             ("target", "3. Economize e invista", "Descubra o que cortar e quanto essa economia vira investida.")]
    cards = "".join(f'<div class="step">{icon(i, size=28)}<div class="t">{t}</div><div class="d">{d}</div></div>' for i, t, d in steps)
    return f'<div class="steps">{cards}</div>'


def stat_card(title: str, value: str, note: str = "", tone: str = "") -> str:
    """Card simples (título, número grande e uma linha de apoio). tone: 'good' | 'bad' | ''."""
    foot = f'<span class="pill {tone}">{note}</span>' if note else ""
    return (f'<div class="card"><div class="card-title">{title}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-foot">{foot}</div></div>')


def setup() -> dict:
    """Barra lateral (logo, upload, mês, reserva, orçamento) + leitura do extrato. Guarda tudo em st.session_state['ctx']."""
    with st.sidebar:
        st.markdown(logo_html(), unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Extrato bancário (CSV ou OFX)", type=["csv", "ofx"],
            help="CSV com data, descrição e valor (ou crédito e débito), ou o arquivo OFX que seu banco oferece. "
                 "Despesas com valor negativo.")
        invert = st.checkbox(
            "Despesas vêm com valor positivo", value=False,
            help="Marque para faturas de cartão em que a compra aparece como valor positivo.")
        reserve = st.number_input("Reserva de emergência atual (R$)", min_value=0, value=0 if uploaded else 12000, step=500,
                                  help="Usada na nota de saúde financeira e na página Investir. "
                                       "Nos dados de exemplo, começa com um valor de demonstração.")
        with st.expander("Orçamento mensal por categoria"):
            budgets = {
                cat: st.number_input(cat, min_value=0, value=int(default), step=50, key=f"budget_{cat}")
                for cat, default in core.DEFAULT_BUDGETS.items()
            }
    overrides = tuple(sorted(st.session_state.get("overrides", {}).items()))  # regras criadas na página Categorias
    try:
        if uploaded is not None:
            df, using_sample = load(uploaded.getvalue(), invert, overrides), False
        else:
            df, using_sample = load(str(SAMPLE_PATH), invert, overrides), True
    except (ValueError, pd.errors.ParserError) as err:
        st.error(f"Não consegui ler o arquivo. {err}")
        st.stop()
    if not using_sample and not (df["amount"] < 0).any():
        st.warning("Todas as transações estão com valor positivo, então não encontrei despesas. "
                   "Se for uma fatura de cartão, marque \"Despesas vêm com valor positivo\" na barra lateral.")
    keys = [str(m) for m in sorted(df["month"].unique())]
    # O mês é escolhido no cabeçalho das páginas (page_header). Guardamos a escolha em duas chaves para
    # que ela sobreviva à troca de página e volte ao último mês quando o extrato muda.
    chosen = st.session_state.get("month_sel") or st.session_state.get("month_choice")
    chosen = chosen if chosen in keys else keys[-1]
    st.session_state["month_choice"] = st.session_state["month_sel"] = chosen
    ctx = dict(df=df, budgets=budgets, reserve=float(reserve), using_sample=using_sample, month=pd.Period(chosen),
               overrides=dict(overrides))
    st.session_state["ctx"] = ctx
    return ctx


def page_header(title: str, sub: str) -> None:
    """Título da página com o seletor de mês no canto direito."""
    keys = [str(m) for m in sorted(st.session_state["ctx"]["df"]["month"].unique())]
    left, right = st.columns([3, 1])
    left.markdown(f'<p class="page-title">{title}</p><p class="page-sub">{sub}</p>', unsafe_allow_html=True)
    with right:
        st.selectbox("Mês que você quer ver", keys, key="month_sel", format_func=lambda k: month_label(pd.Period(k)))
