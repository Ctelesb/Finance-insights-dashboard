<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 72"><g transform="translate(4,8) scale(1.0)"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38BDF8"/><stop offset="1" stop-color="#818CF8"/></linearGradient></defs><rect x="2.5" y="2.5" width="59" height="51" rx="9" fill="none" stroke="url(#g)" stroke-width="4"/><line x1="2.5" y1="17" x2="61.5" y2="17" stroke="url(#g)" stroke-width="3.5"/><circle cx="12" cy="9.8" r="2.4" fill="#38BDF8"/><circle cx="20" cy="9.8" r="2.4" fill="#38BDF8"/><circle cx="28" cy="9.8" r="2.4" fill="#38BDF8"/><g fill="none" stroke="url(#g)" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22,28 14,36 22,44"/><line x1="36" y1="25" x2="28" y2="47"/><polyline points="42,28 50,36 42,44"/></g></g><text x="84" y="40" font-family="Outfit, Montserrat, 'Segoe UI', Arial, sans-serif" font-size="30" font-weight="600" letter-spacing="3.5" fill="#F8FAFC">TELESCODE<tspan fill="#38BDF8" letter-spacing="0" dx="4">&lt;/&gt;</tspan></text><rect x="84" y="50" width="326" height="4" rx="2" fill="url(#g)"/></svg>">
    <img alt="Telescode" src="<img width="1526" height="600" alt="<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 72"><g transform="translate(4,8) scale(1.0)"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38BDF8"/><stop offset="1" stop-color="#818CF8"/></linearGradient></defs><rect x="2.5" y="2.5" width="59" height="51" rx="9" fill="none" stroke="url(#g)" stroke-width="4"/><line x1="2.5" y1="17" x2="61.5" y2="17" stroke="url(#g)" stroke-width="3.5"/><circle cx="12" cy="9.8" r="2.4" fill="#38BDF8"/><circle cx="20" cy="9.8" r="2.4" fill="#38BDF8"/><circle cx="28" cy="9.8" r="2.4" fill="#38BDF8"/><g fill="none" stroke="url(#g)" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22,28 14,36 22,44"/><line x1="36" y1="25" x2="28" y2="47"/><polyline points="42,28 50,36 42,44"/></g></g><text x="84" y="40" font-family="Outfit, Montserrat, 'Segoe UI', Arial, sans-serif" font-size="30" font-weight="600" letter-spacing="3.5" fill="#F8FAFC">TELESCODE<tspan fill="#38BDF8" letter-spacing="0" dx="4">&lt;/&gt;</tspan></text><rect x="84" y="50" width="326" height="4" rx="2" fill="url(#g)"/></svg>" src="https://github.com/user-attachments/assets/56bcb1de-ba86-43ac-ae15-48a1c51d01cd" />
" width="420">
  </picture>
</p>


<h1 align="center">Finance Insides Dashboard</h1>

<p align="center"><b>Finance Insights</b>: seu extrato, em respostas simples</p>

<p align="center">
  Quanto sobrou no mês? Envie o extrato do seu banco e descubra para onde o dinheiro foi, onde dá para economizar,
  quanto guardar para cada meta e o que essa economia vira investida.
</p>

<p align="center">
  <a href="https://finance-insights-dashboard-telescode-4.streamlit.app/"><b>Ver o app no ar</b></a>
</p>

---

## O que é

O **Finance-insights-dashboard** (Finance Insights) é um dashboard de finanças pessoais feito em Python com Streamlit. Você envia o extrato
(CSV ou OFX) ou usa os dados de exemplo, e o app transforma linhas de transações em respostas simples: quanto sobrou
no mês, o que pesou no orçamento, o que cortar, quanto guardar para cada objetivo e onde investir.

Todo o app está em português e usa o formato brasileiro (R$, datas `dd/mm/aaaa`, vírgula decimal).

## Demonstração

<!-- Adicione prints ou um GIF em docs/ e referencie aqui, por exemplo:
<p align="center"><img src="docs/visao-geral.png" width="900" alt="Visão geral do Sobrou"></p> -->

Teste sem instalar nada: **[https://finance-insights-dashboard-telescode-4.streamlit.app/](https://finance-insights-dashboard-telescode-4.streamlit.app/)**.
O app abre com dados de exemplo; para analisar o seu extrato, envie o arquivo na barra lateral.

## Páginas

### Visão geral
- **O mês em uma frase**: quanto você já gastou, quanto deve fechar o mês e a diferença para o orçamento.
- **Saúde financeira de 0 a 100**, calculada para o mês escolhido.
- **Indicadores** de receitas, despesas, saldo e gasto projetado, com comparação com o mês anterior.
- **Gráficos**: gasto por categoria, gasto por dia, acumulado com projeção até o fim do mês e orçamento por categoria.
- **Achados automáticos**: categoria que mais subiu, dia da semana mais caro, gastos fixos recorrentes e compras fora do padrão.
- **Relatório mensal em PDF**, transações com busca e filtro, gastos atípicos e evolução mensal.

### Economizar
- Detecta **assinaturas e gastos fixos** (cobranças que se repetem todo mês com o mesmo valor).
- Mostra **8 hábitos de consumo** (delivery, transporte por app, cafés, bares e cinema, compras por impulso,
  streaming, jogos e apps, tarifas), com quanto você gasta, quantas vezes e o valor médio de cada compra.
- Você escolhe quanto reduzir em cada um e vê a economia **por mês e por ano**, comparada com a **regra 50/30/20**.

### Investir
- Simula o que a economia vira em **7 investimentos conhecidos**: Poupança, Tesouro Selic, CDB, LCI/LCA,
  Tesouro IPCA+, fundos imobiliários (ex.: MXRF11, HGLG11) e ETFs (ex.: BOVA11, IVVB11).
- **Imposto de renda** (tabela regressiva aplicada a cada aporte pela sua idade) e **inflação** (valores de hoje)
  podem ser ligados ou desligados.
- Selic e IPCA vêm do **Banco Central do Brasil**; sem conexão, o app usa valores de referência e avisa.
- Gráfico que separa o **dinheiro que você coloca** dos **juros** e gráfico que compara os produtos entre si.

### Metas
- Tabela editável com meta, valor, quanto já guardou e prazo.
- Para cada meta: barra de progresso, **quanto guardar por mês**, se isso cabe no seu plano de economia e
  onde aplicar de acordo com o prazo. Dá para baixar e carregar as metas em JSON.

### Categorias
- Mostra quanto das despesas ficou em "Outros" e deixa você **reclassificar** uma vez: a regra vale para toda
  descrição parecida (números e símbolos são ignorados), em qualquer mês. Regras podem ser baixadas e carregadas.

## Como funciona

**Nota de saúde financeira.** De 0 a 100, muda com o mês escolhido, o extrato e a reserva informada:

| Componente | Pontos | Como pontua |
|---|---|---|
| Poupança | 50 | Máximo quando a sobra do mês chega a 20% da renda |
| Orçamento | 30 | Proporção de categorias dentro do limite definido |
| Reserva | 20 | Máximo quando a reserva cobre 6 meses de gastos essenciais |

Faixas: **Excelente** (80+), **Boa** (60+), **Atenção** (40+) e **Crítica** (abaixo de 40).

**Projeção do mês.** Em mês ainda em andamento, o app não multiplica tudo pelo ritmo diário. Gastos fixos
(mesmo valor todo mês, como aluguel e assinaturas) entram pelo valor típico, compras pontuais fora do padrão
ficam como estão, e só o gasto variável segue o ritmo dos dias já passados.

**Cores.** Verde é bom (ganhos, dentro do limite), amarelo é alerta financeiro e vermelho é ruim (despesa,
orçamento estourado). Gráficos de status também usam texturas, para quem não distingue bem verde e vermelho.
As categorias usam cores próprias, frias e neutras, para não se confundirem com esses sinais.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

No Windows, se o comando `streamlit` não for encontrado: `python -m streamlit run app.py`.
O app abre em `http://localhost:8501` já com dados de exemplo. Para gerar o extrato de exemplo de novo:
`python generate_sample.py`.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes cobrem leitura de extratos (CSV, OFX, cabeçalho deslocado, crédito e débito), categorização e regras,
projeção, gastos atípicos, simulação com imposto e inflação, nota de saúde financeira, taxas e relatório em PDF.
Eles rodam automaticamente no GitHub Actions (`.github/workflows/tests.yml`).

## Formatos de extrato aceitos

- **CSV** com colunas de data, descrição e valor, ou de data, descrição, crédito e débito. Aceita separador `;`,
  `,` ou tabulação, datas `dd/mm/aaaa` ou `aaaa-mm-dd` e valores como `1.234,56`, `-R$ 1.234,56` e `(50,00)`.
  Linhas de resumo antes do cabeçalho são ignoradas.
- **OFX**, o arquivo que a maioria dos bancos oferece para exportar o extrato.

Despesas devem ter valor negativo. Em faturas de cartão em que a compra aparece como positiva, marque
**"Despesas vêm com valor positivo"** na barra lateral (o app avisa quando não encontra nenhuma despesa).
As categorias iniciais vêm de palavras-chave (`CATEGORY_KEYWORDS` em `core.py`); o que não for reconhecido
vai para "Outros" e pode ser corrigido na página Categorias.

## Estrutura do projeto

```
app.py          ponto de entrada multi-page (navegação)
core.py         leitura de extratos, categorias, projeção, orçamento e gastos atípicos
savings.py      economia, hábitos, nota, produtos de investimento e simulação com IR e inflação
insights.py     textos de destaque e achados automáticos
rates.py        Selic e IPCA do Banco Central (com valores de reserva)
report.py       relatório mensal em PDF
ui.py           tema (CSS), ícones, logo e barra lateral compartilhados
views/          uma página por arquivo: overview, economizar, investir, metas, categorias
assets/         logo (SVG) e ícone do app
sample_data/    extrato de exemplo
tests/          testes automáticos
```

`core.py`, `savings.py`, `insights.py`, `rates.py` e `report.py` não dependem do Streamlit.

## Premissas e avisos

- Taxas de referência (sem conexão): Selic de 13,75% a.a. (Copom, 04/11/2026) e poupança de cerca de 8,3% a.a.
  Todas ficam **editáveis na tela**. Os retornos de Tesouro IPCA+ (IPCA mais 7% de juro real), fundos
  imobiliários (11%) e ETFs (15%) são **premissas**, não garantias.
- O imposto dos fundos imobiliários é simplificado (rendimentos isentos para pessoa física); ETFs pagam 15%
  sobre o ganho; CDB e Tesouro seguem a tabela regressiva.
- Os produtos citados são exemplos educativos. **Isto não é recomendação de investimento.**

## Privacidade

O app lê o extrato apenas durante a sessão e o código não o grava em banco de dados nem em disco. Metas e regras
de categoria só persistem se você baixar os arquivos. As únicas chamadas externas são as consultas públicas de Selic
e IPCA ao Banco Central, que não enviam nenhum dado seu. Ao publicar em um serviço de hospedagem, vale conferir a
política dele.

## Tecnologias

Python, Streamlit, Pandas, Plotly e ReportLab.

## Autor

Feito por **Telescode**.
