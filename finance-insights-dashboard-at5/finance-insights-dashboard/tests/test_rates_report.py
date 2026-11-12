import json

import core
import insights
import rates
import report
import savings


def test_parse_last():
    assert rates.parse_last(json.dumps([{"data": "04/11/2026", "valor": "13.75"}])) == (13.75, "04/11/2026")
    assert rates.parse_last('[{"data":"01/10/2026","valor":"4,10"}]')[0] == 4.1


def test_fetch_falls_back_without_network():
    original = rates.urllib.request.urlopen

    def boom(*a, **k):
        raise OSError("sem rede")
    rates.urllib.request.urlopen = boom
    try:
        r = rates.fetch(timeout=0.1)
    finally:
        rates.urllib.request.urlopen = original
    assert r["live"] is False and r["selic"] == 13.75 and r["cdi"] == 13.65 and r["ipca_plus"] == 11.1


def test_pdf_report_builds():
    df = core.load_statement("sample_data/extrato_exemplo.csv")
    m = sorted(df["month"].unique())[-1]
    cur, proj = core.month_totals(df, m), core.project_month(df, m)
    st = core.budget_status(core.spending_by_category(df, m), core.DEFAULT_BUDGETS)
    pdf = report.build_report("outubro de 2026", cur, proj, 54, "Atenção",
                              [(r.category, r.spent, r.limit, r.status) for r in st.itertuples()],
                              [("alert", "Teste", "texto &amp; mais")], 336.0, 4032.0, True)
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
