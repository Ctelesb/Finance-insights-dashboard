"""Relatório mensal em PDF (reportlab). Não depende do Streamlit."""
from __future__ import annotations

import html
import io

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GREEN, AMBER, RED, INK, MUTED = "#059669", "#D97706", "#E11D48", "#0F172A", "#64748B"


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _bars(rows: list[tuple[str, float, float]], width: float = 17 * cm) -> Drawing:
    """Barras horizontais: gasto (cor pelo uso do limite) sobre uma trilha cinza que representa o limite."""
    h = 20
    d = Drawing(width, h * len(rows) + 4)
    track = width - 5.2 * cm
    for i, (name, spent, limit) in enumerate(rows):
        y = (len(rows) - 1 - i) * h + 4
        pct = spent / limit if limit else 0
        color = RED if pct > 1 else AMBER if pct >= 0.8 else GREEN
        d.add(String(0, y + 4, name, fontName="Helvetica", fontSize=9, fillColor=colors.HexColor(INK)))
        d.add(Rect(3.2 * cm, y + 2, track, 10, fillColor=colors.HexColor("#E2E8F0"), strokeColor=None))
        d.add(Rect(3.2 * cm, y + 2, track * min(pct, 1), 10, fillColor=colors.HexColor(color), strokeColor=None))
        d.add(String(3.2 * cm + track + 6, y + 4, f"{brl(spent)} / {brl(limit)}", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor(MUTED)))
    return d


def build_report(month_name: str, cur: dict, proj: dict, score: int, score_label: str, status_rows: list[tuple],
                 insights: list[tuple[str, str, str]], plan_monthly: float, plan_yearly: float, using_sample: bool) -> bytes:
    """PDF de uma página e meia com resumo do mês, nota, orçamento, achados e plano de economia."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title=f"Finance Insights - {month_name}", author="Telescode")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=22, textColor=colors.HexColor(INK), alignment=0, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=13, textColor=colors.HexColor(INK), spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14, textColor=colors.HexColor(INK))
    small = ParagraphStyle("s", parent=body, fontSize=8, textColor=colors.HexColor(MUTED))
    story = [Paragraph(f"Finance Insights: {month_name}", h1),
             Paragraph("Relatório gerado por Telescode" + (" com dados de exemplo" if using_sample else ""), small), Spacer(1, 10)]

    over = proj["projected"] if proj["is_open"] else cur["expenses"]
    kpis = [["Receitas", "Despesas", "Saldo do mês", "Poupou"],
            [brl(cur["income"]), brl(cur["expenses"]), brl(cur["balance"]), f"{cur['savings_rate']:.0f}% da renda"]]
    t = Table(kpis, colWidths=[4.25 * cm] * 4)
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, 0), 8), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(MUTED)),
                           ("FONTSIZE", (0, 1), (-1, 1), 13), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                           ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor(RED)),
                           ("TEXTCOLOR", (2, 1), (2, 1), colors.HexColor(GREEN if cur["balance"] >= 0 else RED)),
                           ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor(GREEN)),
                           ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [t, Spacer(1, 8)]
    if proj["is_open"]:
        story.append(Paragraph(f"No ritmo atual, o mês deve fechar com gasto de <b>{brl(over)}</b> (hoje: {brl(proj['spent'])}).", body))
    tone = GREEN if score >= 60 else AMBER if score >= 40 else RED
    big = ParagraphStyle("big", parent=body, fontSize=26, leading=32)
    story += [Paragraph("Saúde financeira", h2),
              Paragraph(f'<font color="{tone}"><b>{score}/100</b></font> <font size="14" color="{tone}"><b>{score_label}</b></font>', big),
              Paragraph("Nota de 0 a 100: poupança (50 pontos), orçamento (30) e reserva de emergência (20).", small)]
    story.append(Paragraph("Orçamento por categoria", h2))
    rows = [(c, s, l) for c, s, l, _ in status_rows if l > 0]
    if rows:
        story.append(_bars(rows))
    if insights:
        story.append(Paragraph("O que chamou atenção", h2))
        for _, title, text in insights:
            story.append(Paragraph(f"<b>{html.escape(html.unescape(title))}.</b> {html.unescape(text)}", body))
            story.append(Spacer(1, 3))
    if plan_monthly > 0:
        story += [Paragraph("Plano de economia", h2),
                  Paragraph(f"Cortando o supérfluo você economiza <b>{brl(plan_monthly)}</b> por mês, "
                            f"ou <b>{brl(plan_yearly)}</b> por ano.", body)]
    story += [Spacer(1, 16), Paragraph("Simulações e valores são educativos e não constituem recomendação de investimento.", small)]
    doc.build(story)
    return buf.getvalue()
