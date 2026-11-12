import core

SAMPLE = "sample_data/extrato_exemplo.csv"


def load():
    return core.load_statement(SAMPLE)


def test_parse_number_formats():
    for raw, expected in [("1.234,56", 1234.56), ("-R$ 1.234,56", -1234.56), ("1234.56", 1234.56),
                          ("(50,00)", -50.0), ("1.234", 1234.0), ("12,5", 12.5)]:
        assert core._parse_number(raw) == expected, raw
    assert core._parse_number("abc") != core._parse_number("abc")  # NaN


def test_dates_iso_and_brazilian():
    csv = "Data,Histórico,Valor\n07/10/2026,A,-1\n2026-10-08,B,-2\n2026-10-09 14:30:00,C,-3\n".encode("utf-8")
    df = core.load_statement(csv)
    assert [d.day for d in df["date"]] == [7, 8, 9] and set(df["date"].dt.month) == {10}


def test_sample_loads_and_is_categorized():
    df = load()
    assert len(df) == 150 and set(df.columns) >= {"date", "description", "amount", "category", "month"}
    assert {"Moradia", "Mercado", "Alimentação", "Transporte"} <= set(df["category"])
    assert (df[df["category"] == "Outros"]["amount"] < 0).all()


def test_income_categories():
    assert core.categorize("SALARIO EMPRESA", 7800) == "Salário"
    assert core.categorize("PIX RECEBIDO", 100) == "Outras receitas"


def test_override_wins_and_ignores_numbers():
    assert core.rule_key("IFOOD *PEDIDO 8841") == core.rule_key("ifood *pedido 9002")
    rules = {core.rule_key("LOJA DA MARIA 12"): "Compras"}
    assert core.categorize("LOJA DA MARIA 55", -80, rules) == "Compras"
    assert core.categorize("LOJA DA MARIA 55", -80) == "Outros"


def test_bank_file_with_preamble_and_two_description_columns():
    raw = ("Extrato Conta Corrente\nPeríodo: 01/10/2026 a 31/10/2026\n\nData Lançamento;Histórico;Descrição;Valor;Saldo\n"
           "05/10/2026;Pix recebido;JOAO SILVA;\"1.500,00\";\"2.000,00\"\n06/10/2026;Compra no débito;UBER *TRIP;\"-32,10\";\"1.967,90\"\n")
    df = core.load_statement(raw.encode("latin-1"))
    assert len(df) == 2 and df["amount"].tolist() == [1500.0, -32.1] and df["category"].iloc[1] == "Transporte"


def test_credit_and_debit_columns():
    df = core.load_statement(b"Data,Descri\xe7\xe3o,Cr\xe9dito,D\xe9bito\n05/10/2026,SALARIO,\"7.800,00\",\n06/10/2026,IFOOD,,\"45,50\"\n")
    assert df["amount"].tolist() == [7800.0, -45.5]


def test_ofx():
    ofx = ("OFXHEADER:100\n<OFX><BANKTRANLIST>\n<STMTTRN>\n<DTPOSTED>20261006120000\n<TRNAMT>-32.10\n<MEMO>UBER *TRIP\n</STMTTRN>\n"
           "<STMTTRN>\n<DTPOSTED>20261005\n<TRNAMT>1500.00\n<NAME>PIX RECEBIDO\n</STMTTRN></BANKTRANLIST></OFX>").encode()
    df = core.load_statement(ofx)
    assert df["amount"].tolist() == [1500.0, -32.1] and df["date"].iloc[0].day == 5


def test_invert_sign_and_invalid_file():
    csv = b"Data;Descricao;Valor\n01/10/2026;IFOOD;50,00\n"
    assert core.load_statement(csv, invert_sign=True)["amount"].iloc[0] == -50.0
    for bad in (b"a;b\n1;2\n", b"Data;Descricao;Valor\nlixo;x;y\n"):
        try:
            core.load_statement(bad)
        except ValueError:
            continue
        raise AssertionError("deveria levantar ValueError")


def test_month_totals_and_budget_status():
    df = load()
    m = sorted(df["month"].unique())[0]
    t = core.month_totals(df, m)
    assert abs(t["balance"] - (t["income"] - t["expenses"])) < 1e-6
    st = core.budget_status(core.spending_by_category(df, m), {"Moradia": 1000, "Lazer": 0})
    assert st.loc[st["category"] == "Moradia", "status"].iloc[0] == "over"
    assert st.loc[st["category"] == "Lazer", "pct"].iloc[0] == 0


def test_projection_does_not_multiply_fixed_costs():
    df = load()
    m = sorted(df["month"].unique())[-1]
    pj, proj_cat = core.project_month(df, m), core.projected_spending(df, m)
    spent_cat = core.spending_by_category(df, m)
    naive = pj["spent"] / pj["last_day"] * pj["days"]
    assert pj["is_open"] and pj["spent"] < pj["projected"] < naive
    assert abs(proj_cat["Moradia"] - spent_cat["Moradia"]) / spent_cat["Moradia"] < 0.05  # aluguel não é extrapolado
    # A TV (compra pontual) não é multiplicada: o acréscimo em Compras é bem menor que o de uma regra de três
    extra_naive = spent_cat["Compras"] / pj["last_day"] * (pj["days"] - pj["last_day"])
    assert 0 <= proj_cat["Compras"] - spent_cat["Compras"] < 0.3 * extra_naive


def test_closed_month_has_no_projection():
    df = load()
    m = sorted(df["month"].unique())[0]
    pj = core.project_month(df, m)
    assert not pj["is_open"] and pj["projected"] == pj["spent"]


def test_outliers_flag_tv_but_not_rent():
    out = core.find_outliers(load())
    assert out["description"].tolist() == ["MAGALU TV 55 POLEGADAS"] and out["ratio"].iloc[0] > 10
