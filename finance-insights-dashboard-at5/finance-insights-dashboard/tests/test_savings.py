import core
import insights
import savings as s

df = core.load_statement("sample_data/extrato_exemplo.csv")
MONTHS = sorted(df["month"].unique())
CLOSED = MONTHS[:-1]


def test_simulate_matches_future_value_when_tax_free():
    sim = s.simulate(500, 13.65, 10, ir="isento")
    assert abs(sim["balance"][-1] - s.future_value(500, 13.65, 10)[-1]) < 1e-6
    assert sim["principal"][-1] == 500 * 120


def test_tax_and_inflation_reduce_result():
    gross = s.simulate(500, 13.65, 10, ir="isento")["balance"][-1]
    net = s.simulate(500, 13.65, 10)["balance"][-1]
    real = s.simulate(500, 13.65, 10, ir="isento", inflation_pct=4.1)["balance"][-1]
    assert real < net < gross
    assert abs(s.simulate(0, 15, 5, 1000, ir=0.15)["interest"][-1] - 0.85 * (1000 * 1.15 ** 5 - 1000)) < 1e-6


def test_regressive_tax_by_age():
    assert abs(s.simulate(0, 12, 1, 1000)["balance"][-1] - 1096.0) < 1e-6  # 360 dias: 20% de 120
    assert abs(s.simulate(100, 0, 1)["balance"][-1] - 1200.0) < 1e-9


def test_needed_monthly():
    assert s.needed_monthly(1200, 0, 12) == 100
    assert 0 < s.needed_monthly(1200, 13.65, 12) < 100
    assert s.needed_monthly(0, 13.65, 12) == 0


def test_month_score_bounds_and_reserve():
    m = MONTHS[0]
    low = s.month_score(df, m, core.DEFAULT_BUDGETS, 0)
    high = s.month_score(df, m, core.DEFAULT_BUDGETS, 50000)
    assert 0 <= low["score"] <= high["score"] <= 100
    scores = {s.month_score(df, x, core.DEFAULT_BUDGETS, 0)["score"] for x in MONTHS}
    assert len(scores) > 1  # a nota muda conforme o mês


def test_habits():
    assert s.habit_of("IFOOD *PEDIDO") == s.habit_of("UBER EATS") == "Delivery de comida"
    assert s.habit_of("UBER *TRIP") == "Transporte por app"
    assert s.habit_of("SUPERMERCADO ASSAI") is None


def test_recurring_finds_subscriptions():
    names = set(s.recurring(df, CLOSED)["description"])
    assert {"NETFLIX", "SPOTIFY", "ACADEMIA SMARTFIT"} <= names and "IFOOD *PEDIDO" not in names


def test_plan_does_not_double_count():
    hs, rec = s.habit_stats(df, CLOSED), s.recurring(df, CLOSED)
    rec = rec.assign(category=rec["description"].map(s.habit_of).fillna("Outros fixos"))
    plan = s.plan_savings(hs["monthly"], rec, ["NETFLIX", "SPOTIFY"], {"Streaming e música": 100})
    assert abs(plan["by_category"]["Streaming e música"] - hs.loc["Streaming e música", "monthly"]) < 1e-6


def test_insights_text():
    assert insights.score_status(90)[1] == "good" and insights.score_status(50) == ("Atenção", "warn")
    assert insights.score_status(10) == ("Crítica", "bad")
    html = insights.cards_html([("trend", "A <b>", "texto")], lambda n: "")
    assert "&lt;b&gt;" in html
