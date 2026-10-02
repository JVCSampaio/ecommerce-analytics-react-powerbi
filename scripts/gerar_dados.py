"""
Gera um dataset sintético (porém realista) de vendas de um e-commerce brasileiro,
em modelo estrela, para ser consumido pelo Power BI e pelo app React.

Saídas:
  data/fato_vendas.csv
  data/dim_produto.csv
  data/dim_cliente.csv
  data/dim_geografia.csv
  data/dim_calendario.csv
  web/public/data/vendas.json   (versão colunar compacta para o React)

Uso:
  pip install numpy pandas
  python scripts/gerar_dados.py
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
INICIO = date(2024, 1, 1)
FIM = date(2025, 12, 31)
N_CLIENTES = 8_000

RAIZ = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ / "data"
PASTA_WEB = RAIZ / "web" / "public" / "data"

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------- #
# Geografia
# --------------------------------------------------------------------------- #
GEO = [
    # uf, estado, regiao, peso (participação aprox. no e-commerce)
    ("SP", "São Paulo", "Sudeste", 30.0),
    ("RJ", "Rio de Janeiro", "Sudeste", 10.0),
    ("MG", "Minas Gerais", "Sudeste", 10.0),
    ("ES", "Espírito Santo", "Sudeste", 2.0),
    ("RS", "Rio Grande do Sul", "Sul", 6.0),
    ("PR", "Paraná", "Sul", 6.0),
    ("SC", "Santa Catarina", "Sul", 4.5),
    ("BA", "Bahia", "Nordeste", 5.0),
    ("PE", "Pernambuco", "Nordeste", 3.5),
    ("CE", "Ceará", "Nordeste", 3.0),
    ("MA", "Maranhão", "Nordeste", 1.2),
    ("PB", "Paraíba", "Nordeste", 1.0),
    ("RN", "Rio Grande do Norte", "Nordeste", 1.0),
    ("AL", "Alagoas", "Nordeste", 0.8),
    ("PI", "Piauí", "Nordeste", 0.7),
    ("SE", "Sergipe", "Nordeste", 0.6),
    ("GO", "Goiás", "Centro-Oeste", 3.0),
    ("DF", "Distrito Federal", "Centro-Oeste", 3.0),
    ("MT", "Mato Grosso", "Centro-Oeste", 1.5),
    ("MS", "Mato Grosso do Sul", "Centro-Oeste", 1.3),
    ("PA", "Pará", "Norte", 2.0),
    ("AM", "Amazonas", "Norte", 1.2),
    ("RO", "Rondônia", "Norte", 0.6),
    ("TO", "Tocantins", "Norte", 0.5),
    ("AC", "Acre", "Norte", 0.3),
    ("AP", "Amapá", "Norte", 0.3),
    ("RR", "Roraima", "Norte", 0.3),
]
dim_geo = pd.DataFrame(GEO, columns=["uf", "estado", "regiao", "peso"])

# frete base, prazo prometido e faixa de prazo real por região
LOGISTICA = {
    "Sudeste": dict(frete=19.9, prometido=5, prazo=(2, 7)),
    "Sul": dict(frete=24.9, prometido=7, prazo=(3, 9)),
    "Centro-Oeste": dict(frete=29.9, prometido=8, prazo=(4, 11)),
    "Nordeste": dict(frete=32.9, prometido=10, prazo=(5, 14)),
    "Norte": dict(frete=39.9, prometido=12, prazo=(7, 18)),
}

# --------------------------------------------------------------------------- #
# Produtos
# --------------------------------------------------------------------------- #
CATALOGO = {
    "Eletrônicos": dict(
        custo=(0.70, 0.82),
        itens=[
            ("Fone Bluetooth com Cancelamento de Ruído", 449.90),
            ("Smartwatch Fitness", 699.00),
            ("Caixa de Som Portátil", 299.90),
            ("Teclado Mecânico RGB", 389.90),
            ("Mouse Sem Fio Ergonômico", 149.90),
            ("Monitor 27\" IPS", 1_399.00),
            ("Tablet 10\" 128GB", 1_899.00),
            ("Notebook 15\" i5 16GB", 3_799.00),
            ("Carregador Turbo 65W", 129.90),
        ],
    ),
    "Casa & Cozinha": dict(
        custo=(0.52, 0.64),
        itens=[
            ("Air Fryer 5L", 429.90),
            ("Cafeteira Expresso", 799.00),
            ("Jogo de Panelas Antiaderente", 349.90),
            ("Liquidificador 1200W", 229.90),
            ("Aspirador Robô", 1_299.00),
            ("Jogo de Cama Queen 300 fios", 259.90),
            ("Kit Potes Herméticos", 89.90),
            ("Luminária de Mesa LED", 119.90),
        ],
    ),
    "Moda": dict(
        custo=(0.40, 0.52),
        itens=[
            ("Tênis Casual Unissex", 279.90),
            ("Jaqueta Corta-Vento", 229.90),
            ("Calça Jeans Slim", 179.90),
            ("Camiseta Básica Algodão", 59.90),
            ("Mochila Urbana", 199.90),
            ("Relógio Analógico", 249.90),
            ("Óculos de Sol", 159.90),
            ("Vestido Midi", 189.90),
        ],
    ),
    "Beleza": dict(
        custo=(0.38, 0.50),
        itens=[
            ("Kit Skincare Facial", 189.90),
            ("Protetor Solar FPS 50", 69.90),
            ("Perfume Amadeirado 100ml", 249.90),
            ("Secador de Cabelo 2000W", 219.90),
            ("Prancha Alisadora", 179.90),
            ("Sérum Vitamina C", 99.90),
            ("Kit Maquiagem Básico", 129.90),
            ("Barbeador Elétrico", 199.90),
        ],
    ),
    "Esporte & Lazer": dict(
        custo=(0.55, 0.66),
        itens=[
            ("Bicicleta Aro 29", 1_499.00),
            ("Esteira Dobrável", 2_199.00),
            ("Kit Halteres 20kg", 329.90),
            ("Tapete de Yoga", 99.90),
            ("Garrafa Térmica 1L", 89.90),
            ("Barraca Camping 4 Pessoas", 459.90),
            ("Bola de Futebol Oficial", 149.90),
            ("Patinete Elétrico", 2_499.00),
        ],
    ),
    "Livros": dict(
        custo=(0.58, 0.70),
        itens=[
            ("Livro — Análise de Dados com Python", 119.90),
            ("Livro — Storytelling com Dados", 89.90),
            ("Livro — Romance Contemporâneo", 54.90),
            ("Livro — Fantasia Épica (Box 3 vol.)", 149.90),
            ("Livro — Finanças Pessoais", 49.90),
            ("Livro — Biografia", 69.90),
            ("Livro — Culinária Brasileira", 99.90),
        ],
    ),
    "Brinquedos": dict(
        custo=(0.48, 0.60),
        itens=[
            ("Blocos de Montar 500 peças", 249.90),
            ("Boneca Articulada", 129.90),
            ("Carrinho de Controle Remoto", 199.90),
            ("Jogo de Tabuleiro Estratégia", 179.90),
            ("Quebra-Cabeça 1000 peças", 79.90),
            ("Pelúcia Grande", 99.90),
            ("Kit Ciência para Crianças", 149.90),
        ],
    ),
}

linhas = []
pid = 1
for categoria, cfg in CATALOGO.items():
    for nome, preco in cfg["itens"]:
        custo_pct = rng.uniform(*cfg["custo"])
        linhas.append(
            dict(
                id_produto=pid,
                produto=nome,
                categoria=categoria,
                preco_lista=round(preco, 2),
                custo_unitario=round(preco * custo_pct, 2),
            )
        )
        pid += 1
dim_produto = pd.DataFrame(linhas)

# Popularidade: produtos mais baratos vendem mais, com ruído
pop = (1 / np.sqrt(dim_produto["preco_lista"].to_numpy())) * rng.lognormal(0, 0.35, len(dim_produto))
# Ajuste por categoria (Moda e Beleza giram mais, Livros menos)
ajuste_cat = {"Eletrônicos": 1.15, "Casa & Cozinha": 1.1, "Moda": 1.2, "Beleza": 1.15,
              "Esporte & Lazer": 0.95, "Livros": 0.8, "Brinquedos": 0.9}
pop *= dim_produto["categoria"].map(ajuste_cat).to_numpy()
pop_produto = pop / pop.sum()

# --------------------------------------------------------------------------- #
# Clientes
# --------------------------------------------------------------------------- #
peso_uf = dim_geo["peso"].to_numpy() / dim_geo["peso"].sum()
faixas = ["18-24", "25-34", "35-44", "45-54", "55+"]
peso_faixa = [0.14, 0.33, 0.27, 0.16, 0.10]
data_cad_ini = date(2021, 1, 1)
dias_cad = (FIM - data_cad_ini).days

dim_cliente = pd.DataFrame(
    dict(
        id_cliente=np.arange(1, N_CLIENTES + 1),
        uf=rng.choice(dim_geo["uf"], size=N_CLIENTES, p=peso_uf),
        faixa_etaria=rng.choice(faixas, size=N_CLIENTES, p=peso_faixa),
        data_cadastro=[data_cad_ini + timedelta(days=int(x))
                       for x in rng.integers(0, dias_cad - 400, N_CLIENTES)],
    )
)
# Frequência de compra com cauda longa (poucos clientes compram muito)
freq_cliente = rng.gamma(0.6, 1.0, N_CLIENTES)
freq_cliente /= freq_cliente.sum()

# --------------------------------------------------------------------------- #
# Calendário
# --------------------------------------------------------------------------- #
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
datas = pd.date_range(INICIO, FIM, freq="D")
dim_calendario = pd.DataFrame(
    dict(
        data=datas.date,
        ano=datas.year,
        trimestre=["T" + str(q) for q in datas.quarter],
        mes_num=datas.month,
        mes_nome=[MESES[m - 1] for m in datas.month],
        ano_mes=datas.strftime("%Y-%m"),
        mes_ano=[f"{MESES[m - 1]}/{str(y)[2:]}" for y, m in zip(datas.year, datas.month)],
        dia_semana_num=datas.dayofweek + 1,
        dia_semana=[DIAS_SEMANA[d] for d in datas.dayofweek],
        fim_de_semana=(datas.dayofweek >= 5).astype(int),
    )
)


def black_friday(ano: int) -> date:
    """Última sexta-feira de novembro."""
    d = date(ano, 11, 30)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


BF = {black_friday(a) for a in (2024, 2025)}

# --------------------------------------------------------------------------- #
# Pedidos
# --------------------------------------------------------------------------- #
SAZONAL_MES = {1: 0.86, 2: 0.80, 3: 0.95, 4: 0.94, 5: 1.12, 6: 1.00,
               7: 0.96, 8: 1.02, 9: 0.95, 10: 1.02, 11: 1.45, 12: 1.38}
SEMANA = [1.12, 1.06, 1.02, 1.0, 0.98, 0.88, 0.86]
BASE_DIA = {2024: 34.0, 2025: 41.5}  # ~ +22% de crescimento

pedidos = []
id_pedido = 100_000
geo_idx = dim_geo.set_index("uf")

for d in datas.date:
    lam = BASE_DIA[d.year] * SAZONAL_MES[d.month] * SEMANA[d.weekday()]
    promo = 0.0
    if d in BF:
        lam *= 4.2
        promo = 1.0
    elif any(0 < (d - bf).days <= 3 for bf in BF):  # fim de semana + Cyber Monday
        lam *= 2.2
        promo = 0.8
    elif any(-7 <= (d - bf).days < 0 for bf in BF):  # "Black Week"
        lam *= 1.35
        promo = 0.5
    elif (d.month == 5 and 1 <= d.day <= 12):  # Dia das Mães
        lam *= 1.2
        promo = 0.3
    elif (d.month == 12 and 10 <= d.day <= 23):  # Natal
        lam *= 1.35
        promo = 0.3

    n = rng.poisson(lam)
    if n == 0:
        continue

    clientes = rng.choice(dim_cliente["id_cliente"].to_numpy(), size=n, p=freq_cliente)
    produtos = rng.choice(dim_produto["id_produto"].to_numpy(), size=n, p=pop_produto)

    # Canal: App cresce em 2025
    p_canal = [0.48, 0.32, 0.20] if d.year == 2024 else [0.42, 0.39, 0.19]
    canais = rng.choice(["Site", "App", "Marketplace"], size=n, p=p_canal)

    # Pagamento: Pix ganha espaço, boleto cai
    p_pag = [0.36, 0.52, 0.12] if d.year == 2024 else [0.46, 0.47, 0.07]
    pagamentos = rng.choice(["Pix", "Cartão de Crédito", "Boleto"], size=n, p=p_pag)

    for i in range(n):
        id_pedido += 1
        cli = int(clientes[i])
        prod = dim_produto.iloc[int(produtos[i]) - 1]
        uf = dim_cliente.at[cli - 1, "uf"]
        regiao = geo_idx.at[uf, "regiao"]
        log = LOGISTICA[regiao]

        preco = float(prod["preco_lista"])
        if preco < 150:
            qtd = int(rng.choice([1, 2, 3], p=[0.66, 0.24, 0.10]))
        elif preco < 600:
            qtd = int(rng.choice([1, 2, 3], p=[0.82, 0.14, 0.04]))
        else:
            qtd = int(rng.choice([1, 2], p=[0.96, 0.04]))

        valor_bruto = round(preco * qtd, 2)

        # Desconto
        if promo > 0 and rng.random() < 0.55 + 0.4 * promo:
            pct = rng.uniform(0.10, 0.18 + 0.17 * promo)
        elif rng.random() < 0.35:
            pct = rng.uniform(0.03, 0.15)
        else:
            pct = 0.0
        if pagamentos[i] == "Pix":
            pct += 0.05  # 5% off no Pix
        desconto = round(valor_bruto * pct, 2)
        receita = round(valor_bruto - desconto, 2)
        custo = round(float(prod["custo_unitario"]) * qtd, 2)

        frete = 0.0 if receita >= 299 else round(log["frete"] * rng.uniform(0.85, 1.15), 2)

        # Status
        p_dev = 0.065 if prod["categoria"] == "Moda" else 0.025
        p_canc = 0.07 if pagamentos[i] == "Boleto" else 0.035
        r = rng.random()
        if r < p_canc:
            status = "Cancelado"
        elif r < p_canc + p_dev:
            status = "Devolvido"
        else:
            status = "Entregue"

        if status == "Cancelado":
            prazo = None
            no_prazo = None
        else:
            lo, hi = log["prazo"]
            prazo = int(rng.triangular(lo, lo + (hi - lo) * 0.35, hi))
            if promo >= 0.8:  # pico logístico na Black Friday
                prazo += int(rng.integers(1, 4))
            no_prazo = int(prazo <= log["prometido"])

        pedidos.append(
            (id_pedido, d, cli, int(prod["id_produto"]), uf, canais[i], pagamentos[i], status,
             qtd, preco, valor_bruto, desconto, receita, custo, frete, prazo, no_prazo)
        )

fato = pd.DataFrame(
    pedidos,
    columns=["id_pedido", "data_pedido", "id_cliente", "id_produto", "uf", "canal",
             "forma_pagamento", "status", "quantidade", "preco_unitario", "valor_bruto",
             "desconto", "receita_liquida", "custo_total", "valor_frete",
             "prazo_entrega_dias", "entregue_no_prazo"],
)
fato["prazo_entrega_dias"] = fato["prazo_entrega_dias"].astype("Int64")
fato["entregue_no_prazo"] = fato["entregue_no_prazo"].astype("Int64")

# --------------------------------------------------------------------------- #
# Exporta CSVs (UTF-8, separador vírgula, decimal ponto)
# --------------------------------------------------------------------------- #
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
fato.to_csv(PASTA_DADOS / "fato_vendas.csv", index=False)
dim_produto.to_csv(PASTA_DADOS / "dim_produto.csv", index=False)
dim_cliente.to_csv(PASTA_DADOS / "dim_cliente.csv", index=False)
dim_geo.drop(columns="peso").to_csv(PASTA_DADOS / "dim_geografia.csv", index=False)
dim_calendario.to_csv(PASTA_DADOS / "dim_calendario.csv", index=False)

# --------------------------------------------------------------------------- #
# Exporta JSON colunar compacto para o React
# (valores monetários em centavos inteiros para economizar bytes)
# --------------------------------------------------------------------------- #
CANAIS = ["Site", "App", "Marketplace"]
PAGAMENTOS = ["Pix", "Cartão de Crédito", "Boleto"]
STATUS = ["Entregue", "Devolvido", "Cancelado"]
UFS = dim_geo["uf"].tolist()

dia0 = pd.Timestamp(INICIO)
payload = {
    "meta": {
        "inicio": INICIO.isoformat(),
        "fim": FIM.isoformat(),
        "geradoPor": "scripts/gerar_dados.py",
        "seed": SEED,
    },
    "dim": {
        "canais": CANAIS,
        "pagamentos": PAGAMENTOS,
        "status": STATUS,
        "ufs": [{"uf": u, "estado": e, "regiao": r} for u, e, r, _ in GEO],
        "produtos": [
            {"id": int(p.id_produto), "nome": p.produto, "categoria": p.categoria}
            for p in dim_produto.itertuples()
        ],
    },
    "fato": {
        "dia": (pd.to_datetime(fato["data_pedido"]) - dia0).dt.days.tolist(),
        "cliente": fato["id_cliente"].tolist(),
        "produto": fato["id_produto"].tolist(),
        "uf": fato["uf"].map({u: i for i, u in enumerate(UFS)}).tolist(),
        "canal": fato["canal"].map({c: i for i, c in enumerate(CANAIS)}).tolist(),
        "pagamento": fato["forma_pagamento"].map({c: i for i, c in enumerate(PAGAMENTOS)}).tolist(),
        "status": fato["status"].map({c: i for i, c in enumerate(STATUS)}).tolist(),
        "qtd": fato["quantidade"].tolist(),
        "receita": (fato["receita_liquida"] * 100).round().astype(int).tolist(),
        "custo": (fato["custo_total"] * 100).round().astype(int).tolist(),
        "prazo": fato["prazo_entrega_dias"].fillna(-1).astype(int).tolist(),
        "noPrazo": fato["entregue_no_prazo"].fillna(-1).astype(int).tolist(),
    },
}
PASTA_WEB.mkdir(parents=True, exist_ok=True)
with open(PASTA_WEB / "vendas.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

# --------------------------------------------------------------------------- #
# Resumo para conferência (os mesmos números devem aparecer no Power BI e no React)
# --------------------------------------------------------------------------- #
ok = fato[fato["status"] == "Entregue"]
print(f"Pedidos: {len(fato):,} | Entregues: {len(ok):,}")
for ano, g in ok.groupby(pd.to_datetime(ok["data_pedido"]).dt.year):
    rec = g["receita_liquida"].sum()
    mg = 1 - g["custo_total"].sum() / rec
    print(f"{ano}: Receita líquida R$ {rec:,.2f} | Ticket médio R$ {rec / len(g):,.2f} | Margem {mg:.1%}")
