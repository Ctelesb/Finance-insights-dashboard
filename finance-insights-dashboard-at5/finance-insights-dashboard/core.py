"""Lógica de dados do Finance Insights (sem Streamlit, fácil de testar).

Lê o extrato em CSV, categoriza as transações e calcula totais, projeção,
orçamento e gastos atípicos. O DataFrame padrão tem as colunas:
date (datetime), description, amount (despesa < 0), category e month (Period).
"""
from __future__ import annotations

import io
import re
import unicodedata
from calendar import monthrange

import numpy as np
import pandas as pd

# Limite mensal inicial por categoria (editável na barra lateral do app).
DEFAULT_BUDGETS = {
    "Moradia": 3000, "Mercado": 1300, "Alimentação": 650, "Transporte": 700,
    "Lazer": 450, "Saúde": 250, "Educação": 150, "Compras": 500, "Outros": 200,
}

# Palavras-chave por categoria. A ordem importa: a primeira que casar vence.
CATEGORY_KEYWORDS = {
    "Moradia": ["ALUGUEL", "CONDOMINIO", "ENERGIA", "ENEL", "CEMIG", "LIGHT", "AGUA", "SABESP",
                "INTERNET", "VIVO", "CLARO", "IPTU", "GAS"],
    "Compras": ["AMAZON", "SHOPEE", "RENNER", "MAGALU", "MAGAZINE", "MERCADO LIVRE", "MERCADOLIVRE",
                "SHEIN", "ALIEXPRESS", "ZARA", "AMERICANAS", "CASAS BAHIA", "KABUM"],
    "Mercado": ["SUPERMERCADO", "MERCADO", "ASSAI", "CARREFOUR", "HORTIFRUTI", "ATACADAO", "PAO DE ACUCAR"],
    "Alimentação": ["IFOOD", "RAPPI", "RESTAURANTE", "LANCHONETE", "PADARIA", "MCDONALDS", "BURGER",
                    "PIZZARIA", "CAFE", "STARBUCKS"],
    "Transporte": ["UBER", "99", "POSTO", "IPIRANGA", "SHELL", "COMBUSTIVEL", "ESTACIONAMENTO",
                   "PEDAGIO", "SEM PARAR", "METRO", "ONIBUS"],
    "Lazer": ["NETFLIX", "SPOTIFY", "DISNEY", "HBO", "PRIME VIDEO", "YOUTUBE", "ACADEMIA", "SMARTFIT",
              "CINEMA", "INGRESSO", "BAR", "STEAM", "PLAYSTATION"],
    "Saúde": ["FARMACIA", "DROGASIL", "DROGARIA", "RAIA", "PACHECO", "HOSPITAL", "CLINICA", "UNIMED",
              "LABORATORIO", "DENTISTA"],
    "Educação": ["ALURA", "CURSO", "FACULDADE", "ESCOLA", "UDEMY", "COURSERA", "MENSALIDADE", "LIVRARIA"],
}
_PATTERNS = {cat: re.compile(r"\b(?:" + "|".join(re.escape(k) for k in kws) + r")\b")
             for cat, kws in CATEGORY_KEYWORDS.items()}

# Nomes de coluna reconhecidos (comparados sem acento e em minúsculas).
_DATE_COLS = ("data", "date", "dt", "dia")
_DESC_COLS = ("descri", "histor", "estabelec", "lancamento", "memo", "title", "titulo", "detalhe")
_VALUE_COLS = ("valor", "amount", "value", "quantia")


# --------------------------------------------------------------------------
# Leitura e categorização
# --------------------------------------------------------------------------

def _plain(text: str) -> str:
    """Maiúsculas e sem acento: 'Salário' -> 'SALARIO'."""
    return "".join(c for c in unicodedata.normalize("NFD", str(text)) if unicodedata.category(c) != "Mn").upper()


def _parse_number(raw) -> float:
    """Converte '1.234,56', '-R$ 1.234,56', '1234.56' ou '(50,00)' em float. Inválido vira NaN."""
    s = str(raw).strip().replace("R$", "").replace(" ", "").replace("\xa0", "")
    if not s or s.lower() == "nan":
        return np.nan
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.endswith("-")
    s = s.strip("()+-")
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
    elif "," in s:
        dec = ","
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        dec = ""  # '1.234' é mil duzentos e trinta e quatro
    else:
        dec = "."
    if dec:
        thousands = "." if dec == "," else ","
        s = s.replace(thousands, "").replace(dec, ".")
    else:
        s = s.replace(".", "")
    try:
        value = float(s)
    except ValueError:
        return np.nan
    return -value if neg else value


def _find_columns(columns: list[str], hints: tuple[str, ...]) -> list[str]:
    return [col for col in columns if any(h in _plain(col).lower() for h in hints)]


_CREDIT_COLS, _DEBIT_COLS = ("credito", "entrada"), ("debito", "saida")


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _read_ofx(text: str) -> pd.DataFrame:
    """Extrato OFX (formato que a maioria dos bancos oferece): data, descrição e valor de cada lançamento."""
    rows = []
    for blk in re.findall(r"<STMTTRN>(.*?)(?=</STMTTRN>|<STMTTRN>|</BANKTRANLIST>|$)", text, re.S | re.I):
        def tag(name: str) -> str:
            m = re.search(rf"<{name}>([^<\r\n]+)", blk, re.I)
            return m.group(1).strip() if m else ""
        d = tag("DTPOSTED")[:8]
        if len(d) == 8:
            rows.append((f"{d[:4]}-{d[4:6]}-{d[6:8]}", tag("MEMO") or tag("NAME"), tag("TRNAMT")))
    return pd.DataFrame(rows, columns=["Data", "Descrição", "Valor"])


def _read_csv(source: bytes | str) -> pd.DataFrame:
    raw = source if isinstance(source, bytes) else open(source, "rb").read()
    text = _decode(raw)
    if text.lstrip().upper().startswith("OFXHEADER") or "<OFX>" in text.upper():
        return _read_ofx(text)
    lines = text.splitlines()
    # Alguns bancos colocam linhas de resumo antes do cabeçalho: procura a linha que parece o cabeçalho.
    start = 0
    for i, line in enumerate(lines[:40]):
        low = _plain(line).lower()
        if (any(h in low for h in _DATE_COLS) and any(h in low for h in _VALUE_COLS + _CREDIT_COLS + _DEBIT_COLS)
                and max(line.count(s) for s in (";", ",", "\t")) >= 2):
            start = i
            break
    first = lines[start] if lines else ""
    sep = max((";", ",", "\t"), key=first.count)
    return pd.read_csv(io.StringIO("\n".join(lines[start:])), sep=sep, dtype=str)


def _parse_dates(raw: pd.Series) -> pd.Series:
    """dd/mm/aaaa (padrão BR) e aaaa-mm-dd (ISO). O ISO é lido à parte para não inverter dia e mês."""
    s = raw.astype(str).str.strip()
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}")
    out = pd.to_datetime(s.where(iso).str[:10], format="%Y-%m-%d", errors="coerce")
    br = pd.to_datetime(s.where(~iso), dayfirst=True, errors="coerce", format="mixed")
    return out.fillna(br)


def rule_key(description: str) -> str:
    """Chave de uma regra de categoria: descrição sem acento, sem números e sem símbolos
    ('IFOOD *PEDIDO 8841' e 'IFOOD *PEDIDO 9002' viram a mesma regra)."""
    text = re.sub(r"[\d*#/\\.\-_]+", " ", _plain(description))
    return re.sub(r"\s+", " ", text).strip()


def categorize(description: str, amount: float, overrides: dict | None = None) -> str:
    """Categoria pela descrição. Regras do usuário (overrides) vencem as palavras-chave padrão."""
    if amount > 0:
        return "Salário" if re.search(r"\b(SALARIO|FOLHA|PROVENTOS)\b", _plain(description)) else "Outras receitas"
    if overrides:
        hit = overrides.get(rule_key(description))
        if hit:
            return hit
    text = _plain(description)
    for cat, pattern in _PATTERNS.items():
        if pattern.search(text):
            return cat
    return "Outros"


def load_statement(source: bytes | str, invert_sign: bool = False, overrides: dict | None = None) -> pd.DataFrame:
    """Lê o extrato (CSV ou OFX) e devolve o DataFrame categorizado. Levanta ValueError se o arquivo não servir."""
    raw = _read_csv(source)
    cols = list(raw.columns)
    first = lambda hints: (_find_columns(cols, hints) or [None])[0]  # noqa: E731
    c_date, c_val, c_cred, c_deb = first(_DATE_COLS), first(_VALUE_COLS), first(_CREDIT_COLS), first(_DEBIT_COLS)
    skip = {c for c in (c_date, c_val, c_cred, c_deb) if c} | set(_find_columns(cols, ("saldo", "balance")))
    c_desc = [c for c in _find_columns(cols, _DESC_COLS) if c not in skip]
    if not (c_date and c_desc and (c_val or c_cred or c_deb)):
        raise ValueError("O arquivo precisa ter colunas de data, descrição e valor "
                         f"(encontrei: {', '.join(cols)}).")
    if c_val:
        amount = raw[c_val].map(_parse_number)
    else:  # extratos com colunas separadas de crédito e débito
        cred = raw[c_cred].map(_parse_number).fillna(0) if c_cred else 0
        deb = raw[c_deb].map(_parse_number).abs().fillna(0) if c_deb else 0
        amount = cred - deb
    desc = raw[c_desc].fillna("").astype(str).apply(lambda r: " ".join(x.strip() for x in r if x.strip()), axis=1)
    df = pd.DataFrame({"date": _parse_dates(raw[c_date]), "description": desc, "amount": amount}) \
        .dropna(subset=["date", "amount"])
    if df.empty:
        raise ValueError("Não encontrei nenhuma transação válida (confira o formato de data e valor).")
    if invert_sign:
        df["amount"] = -df["amount"]
    df["category"] = [categorize(d, a, overrides) for d, a in zip(df["description"], df["amount"])]
    df["date"] = df["date"].dt.normalize()
    df["month"] = df["date"].dt.to_period("M")
    return df.sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------
# Métricas do mês
# --------------------------------------------------------------------------

def month_totals(df: pd.DataFrame, month: pd.Period) -> dict:
    """Receitas, despesas (positivo), saldo e taxa de poupança (% da renda) do mês."""
    m = df[df["month"] == month]["amount"]
    income, expenses = float(m[m > 0].sum()), float(-m[m < 0].sum())
    balance = income - expenses
    return {"income": income, "expenses": expenses, "balance": balance,
            "savings_rate": balance / income * 100 if income > 0 else 0.0}


def pct_change(current: float, previous: float) -> float | None:
    """Variação percentual; None quando não há base de comparação."""
    return None if not previous else (current - previous) / abs(previous) * 100


def _fixed_baseline(df: pd.DataFrame, month: pd.Period) -> tuple[set, pd.Series]:
    """Gastos fixos conhecidos pelo histórico: (descrições, total típico por categoria).

    Fixo = mesma descrição, com o mesmo valor, na maioria dos outros meses (aluguel, assinaturas).
    Moradia sempre conta como fixa (a conta de luz varia pouco e vence cedo no mês).
    """
    hist = df[(df["month"] != month) & (df["amount"] < 0)]
    n = hist["month"].nunique()
    fixed: set = set()
    if n >= 2:
        per = hist.groupby(["description", "month"])["amount"].agg(total="sum", times="size").reset_index()
        per["total"] = per["total"].abs()
        g = per.groupby("description").agg(mean=("total", "mean"), std=("total", "std"), months=("total", "size"), times=("times", "max"))
        # Fixo de verdade: aparece na maioria dos meses, no máximo 2 vezes por mês, sempre com o mesmo valor
        # (aluguel, assinatura, mensalidade). Compras de mercado ou posto até podem somar parecido, mas não são idênticas.
        fixed = set(g[(g["months"] >= max(2, int(0.6 * n))) & (g["times"] <= 2) & (g["std"].fillna(0) <= g["mean"] * 0.02)].index)
    hf = hist[hist["description"].isin(fixed) | (hist["category"] == "Moradia")]
    typical = (-hf.groupby(["category", "month"])["amount"].sum()).groupby("category").mean() if len(hf) else pd.Series(dtype=float)
    return fixed, typical


def projected_spending(df: pd.DataFrame, month: pd.Period) -> pd.Series:
    """Gasto do mês por categoria, projetado até o fim quando o mês está em aberto.

    Não extrapola tudo na regra de três: gastos fixos entram pelo valor típico (o aluguel já pago não vira
    1,1 aluguel) e compras pontuais fora do padrão ficam como estão. Só o gasto variável segue o ritmo diário.
    """
    cur = df[(df["month"] == month) & (df["amount"] < 0)].copy()
    cur["value"] = -cur["amount"]
    actual = cur.groupby("category")["value"].sum().sort_values(ascending=False)
    days = monthrange(month.year, month.month)[1]
    last_day = int(df[df["month"] == month]["date"].max().day)
    if not (month == df["month"].max() and last_day < days) or cur.empty:
        return actual
    fixed, typical = _fixed_baseline(df, month)
    out = find_outliers(df)
    out = out[out["date"].dt.to_period("M") == month] if not out.empty else out
    one_off = set(zip(out["date"], out["description"], out["value"])) if not out.empty else set()
    is_fx = cur["description"].isin(fixed) | (cur["category"] == "Moradia")
    is_oo = pd.Series([(d, s, v) in one_off for d, s, v in zip(cur["date"], cur["description"], cur["value"])], index=cur.index)
    paid = cur[is_fx].groupby("category")["value"].sum()
    pont = cur[is_oo & ~is_fx].groupby("category")["value"].sum()
    var = cur[~is_fx & ~is_oo].groupby("category")["value"].sum() / last_day * days
    cats = set(actual.index) | set(typical.index)
    proj = {c: max(paid.get(c, 0.0), typical.get(c, 0.0)) + pont.get(c, 0.0) + var.get(c, 0.0) for c in cats}
    return pd.Series(proj).sort_values(ascending=False)


def project_month(df: pd.DataFrame, month: pd.Period) -> dict:
    """Projeta o gasto até o fim do mês (veja projected_spending).

    O mês está 'aberto' quando é o último do extrato e o último lançamento ainda não chegou ao último dia dele.
    """
    days = monthrange(month.year, month.month)[1]
    spent = float(-df[(df["month"] == month) & (df["amount"] < 0)]["amount"].sum())
    last_day = int(df[df["month"] == month]["date"].max().day)
    is_open = month == df["month"].max() and last_day < days
    if not is_open:
        return {"is_open": False, "spent": spent, "projected": spent, "last_day": days, "days": days}
    return {"is_open": True, "spent": spent, "projected": float(projected_spending(df, month).sum()),
            "last_day": last_day, "days": days}


def spending_by_category(df: pd.DataFrame, month: pd.Period) -> pd.Series:
    """Gasto do mês por categoria (positivo), do maior para o menor."""
    x = df[(df["month"] == month) & (df["amount"] < 0)]
    return (-x.groupby("category")["amount"].sum()).sort_values(ascending=False)


def budget_status(spent: pd.Series, budgets: dict[str, float]) -> pd.DataFrame:
    """Uso do orçamento por categoria: ok (< 80%), warn (80 a 100%) ou over (> 100%)."""
    rows = []
    for cat, limit in budgets.items():
        s = float(spent.get(cat, 0.0))
        pct = s / limit * 100 if limit > 0 else 0.0
        rows.append((cat, s, float(limit), pct, "over" if pct > 100 else "warn" if pct >= 80 else "ok"))
    return pd.DataFrame(rows, columns=["category", "spent", "limit", "pct", "status"])


def daily_spending(df: pd.DataFrame, month: pd.Period) -> pd.Series:
    """Gasto de cada dia do mês (índice 1..último dia; dias sem gasto valem 0)."""
    x = df[(df["month"] == month) & (df["amount"] < 0)]
    s = -x.groupby(x["date"].dt.day)["amount"].sum()
    return s.reindex(range(1, monthrange(month.year, month.month)[1] + 1), fill_value=0.0)


def cumulative_spending(df: pd.DataFrame, month: pd.Period, last_day: int) -> pd.Series:
    """Gasto acumulado do dia 1 até `last_day`."""
    return daily_spending(df, month).loc[:last_day].cumsum()


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Receitas, despesas e saldo de todos os meses do extrato."""
    return pd.DataFrame([{"month": m, **month_totals(df, m)} for m in sorted(df["month"].unique())])


# --------------------------------------------------------------------------
# Gastos atípicos
# --------------------------------------------------------------------------

def find_outliers(df: pd.DataFrame, factor: float = 2.0) -> pd.DataFrame:
    """Despesas pelo menos `factor` vezes maiores que o maior outro gasto da mesma categoria.

    Gastos fixos (mesma descrição em 2+ meses, como aluguel) não contam,
    senão apareceriam como atípicos todo mês.
    """
    cols = ["date", "description", "category", "value", "others_max", "ratio"]
    base = df[df["amount"] < 0].assign(value=lambda d: -d["amount"])
    exp = base[base["category"] != "Outros"]
    if df["month"].nunique() >= 2:
        exp = exp[exp.groupby("description")["month"].transform("nunique") < 2]
    top2 = base.groupby("category")["value"].apply(lambda s: sorted(s, reverse=True)[:2]).to_dict()
    rows = []
    for r in exp.itertuples():
        t = top2[r.category]
        others = (t[1] if len(t) > 1 else None) if r.value >= t[0] else t[0]  # maior valor da categoria sem contar esta linha
        if others and r.value >= factor * others:
            rows.append((r.date, r.description, r.category, r.value, float(others), r.value / others))
    return pd.DataFrame(rows, columns=cols).sort_values("ratio", ascending=False).reset_index(drop=True)
