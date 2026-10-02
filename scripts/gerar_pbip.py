"""
Gera o projeto Power BI em formato PBIP (Power BI Project) — tudo em texto,
versionável no Git:

  powerbi/VendasEcommerce.pbip
  powerbi/VendasEcommerce.SemanticModel/   (modelo semântico em TMDL)
  powerbi/VendasEcommerce.Report/          (relatório: páginas e visuais)
  powerbi/tema/TemaVendas.json             (tema com a mesma paleta do app React)

O modelo lê os CSVs da pasta data/ direto do GitHub (parâmetro UrlBaseDados),
então funciona em qualquer máquina depois de clonar o repositório.

Uso:
  python scripts/gerar_pbip.py --url-base https://raw.githubusercontent.com/<usuario>/<repo>/main/data/
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "powerbi"
NOME = "VendasEcommerce"

# Paleta categórica (mesma do app React — validada para daltonismo)
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

_ns = uuid.UUID("6f1c2a7e-3b7d-4c55-9a3e-2d8e4b1f0a99")


def tag(*partes: str) -> str:
    """lineageTag determinístico (o mesmo a cada execução => diffs limpos no Git)."""
    return str(uuid.uuid5(_ns, "/".join(partes)))


def q(nome: str) -> str:
    """Coloca aspas simples em nomes TMDL que tenham espaço/acentos/símbolos."""
    return nome if nome.replace("_", "").isalnum() and nome.isascii() else "'" + nome.replace("'", "''") + "'"


# --------------------------------------------------------------------------- #
# Definição do modelo
# --------------------------------------------------------------------------- #
# (nome, tipo TMDL, tipo M, extras)
TABELAS: dict[str, dict] = {
    "dim_calendario": dict(
        arquivo="dim_calendario.csv",
        data_table=True,
        colunas=[
            ("data", "dateTime", "type date", dict(isKey=True, formatString="dd/MM/yyyy")),
            ("ano", "int64", "Int64.Type", dict(formatString="0")),
            ("trimestre", "string", "type text", {}),
            ("mes_num", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("mes_nome", "string", "type text", dict(sortByColumn="mes_num")),
            ("ano_mes", "string", "type text", dict(isHidden=True)),
            ("mes_ano", "string", "type text", dict(sortByColumn="ano_mes")),
            ("dia_semana_num", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("dia_semana", "string", "type text", dict(sortByColumn="dia_semana_num")),
            ("fim_de_semana", "int64", "Int64.Type", dict(formatString="0")),
        ],
    ),
    "dim_produto": dict(
        arquivo="dim_produto.csv",
        colunas=[
            ("id_produto", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("produto", "string", "type text", {}),
            ("categoria", "string", "type text", {}),
            ("preco_lista", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="none")),
            ("custo_unitario", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="none")),
        ],
    ),
    "dim_cliente": dict(
        arquivo="dim_cliente.csv",
        colunas=[
            ("id_cliente", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("uf", "string", "type text", dict(dataCategory="StateOrProvince")),
            ("faixa_etaria", "string", "type text", {}),
            ("data_cadastro", "dateTime", "type date", dict(formatString="dd/MM/yyyy")),
        ],
    ),
    "dim_geografia": dict(
        arquivo="dim_geografia.csv",
        colunas=[
            ("uf", "string", "type text", dict(dataCategory="StateOrProvince")),
            ("estado", "string", "type text", dict(dataCategory="StateOrProvince")),
            ("regiao", "string", "type text", {}),
        ],
    ),
    "fato_vendas": dict(
        arquivo="fato_vendas.csv",
        colunas=[
            ("id_pedido", "int64", "Int64.Type", dict(formatString="0")),
            ("data_pedido", "dateTime", "type date", dict(formatString="dd/MM/yyyy", isHidden=True)),
            ("id_cliente", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("id_produto", "int64", "Int64.Type", dict(formatString="0", isHidden=True)),
            ("uf", "string", "type text", dict(isHidden=True)),
            ("canal", "string", "type text", {}),
            ("forma_pagamento", "string", "type text", {}),
            ("status", "string", "type text", {}),
            ("quantidade", "int64", "Int64.Type", dict(formatString="#,0", summarizeBy="sum")),
            ("preco_unitario", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="none")),
            ("valor_bruto", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="sum")),
            ("desconto", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="sum")),
            ("receita_liquida", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="sum")),
            ("custo_total", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="sum")),
            ("valor_frete", "double", "type number", dict(formatString="\\R$ #,0.00", summarizeBy="sum")),
            ("prazo_entrega_dias", "int64", "Int64.Type", dict(formatString="0", summarizeBy="none")),
            ("entregue_no_prazo", "int64", "Int64.Type", dict(formatString="0", summarizeBy="none")),
        ],
        medidas=[
            # (nome, DAX, formato, pasta)
            ("Receita Líquida",
             'CALCULATE ( SUM ( fato_vendas[receita_liquida] ), fato_vendas[status] = "Entregue" )',
             "\\R$ #,0;-\\R$ #,0;\\R$ #,0", "Vendas"),
            ("Custo",
             'CALCULATE ( SUM ( fato_vendas[custo_total] ), fato_vendas[status] = "Entregue" )',
             "\\R$ #,0;-\\R$ #,0;\\R$ #,0", "Vendas"),
            ("Lucro Bruto", "[Receita Líquida] - [Custo]", "\\R$ #,0;-\\R$ #,0;\\R$ #,0", "Vendas"),
            ("Margem Bruta %", "DIVIDE ( [Lucro Bruto], [Receita Líquida] )", "0.0%;-0.0%;0.0%", "Vendas"),
            ("Pedidos", "COUNTROWS ( fato_vendas )", "#,0", "Pedidos"),
            ("Pedidos Entregues",
             'CALCULATE ( COUNTROWS ( fato_vendas ), fato_vendas[status] = "Entregue" )', "#,0", "Pedidos"),
            ("Ticket Médio", "DIVIDE ( [Receita Líquida], [Pedidos Entregues] )",
             "\\R$ #,0.00;-\\R$ #,0.00;\\R$ #,0.00", "Pedidos"),
            ("Itens Vendidos",
             'CALCULATE ( SUM ( fato_vendas[quantidade] ), fato_vendas[status] = "Entregue" )', "#,0", "Pedidos"),
            ("Clientes Ativos",
             'CALCULATE ( DISTINCTCOUNT ( fato_vendas[id_cliente] ), fato_vendas[status] = "Entregue" )',
             "#,0", "Clientes"),
            ("Desconto Médio %",
             'DIVIDE (\n    CALCULATE ( SUM ( fato_vendas[desconto] ), fato_vendas[status] = "Entregue" ),\n'
             '    CALCULATE ( SUM ( fato_vendas[valor_bruto] ), fato_vendas[status] = "Entregue" )\n)',
             "0.0%;-0.0%;0.0%", "Vendas"),
            ("Taxa de Cancelamento %",
             'DIVIDE ( CALCULATE ( COUNTROWS ( fato_vendas ), fato_vendas[status] = "Cancelado" ), [Pedidos] )',
             "0.0%;-0.0%;0.0%", "Operação"),
            ("Taxa de Devolução %",
             'DIVIDE ( CALCULATE ( COUNTROWS ( fato_vendas ), fato_vendas[status] = "Devolvido" ), [Pedidos] )',
             "0.0%;-0.0%;0.0%", "Operação"),
            ("Entregas no Prazo %",
             'DIVIDE (\n    CALCULATE ( SUM ( fato_vendas[entregue_no_prazo] ), fato_vendas[status] = "Entregue" ),\n'
             "    [Pedidos Entregues]\n)",
             "0.0%;-0.0%;0.0%", "Operação"),
            ("Prazo Médio (dias)",
             'CALCULATE ( AVERAGE ( fato_vendas[prazo_entrega_dias] ), fato_vendas[status] = "Entregue" )',
             "0.0", "Operação"),
            ("Receita Ano Anterior",
             "CALCULATE ( [Receita Líquida], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )",
             "\\R$ #,0;-\\R$ #,0;\\R$ #,0", "Tempo"),
            ("Crescimento YoY %",
             "VAR _anterior = [Receita Ano Anterior]\nRETURN\n"
             "    IF ( NOT ISBLANK ( _anterior ), DIVIDE ( [Receita Líquida] - _anterior, _anterior ) )",
             "+0.0%;-0.0%;0.0%", "Tempo"),
            ("Receita Acumulada no Ano", "TOTALYTD ( [Receita Líquida], dim_calendario[data] )",
             "\\R$ #,0;-\\R$ #,0;\\R$ #,0", "Tempo"),
        ],
    ),
}

RELACOES = [
    ("fato_vendas", "data_pedido", "dim_calendario", "data"),
    ("fato_vendas", "id_produto", "dim_produto", "id_produto"),
    ("fato_vendas", "id_cliente", "dim_cliente", "id_cliente"),
    ("fato_vendas", "uf", "dim_geografia", "uf"),
]


# --------------------------------------------------------------------------- #
# Escrita do TMDL
# --------------------------------------------------------------------------- #
T = "\t"


def tmdl_tabela(nome: str, cfg: dict) -> str:
    L: list[str] = [f"table {q(nome)}", f"{T}lineageTag: {tag(nome)}"]
    if cfg.get("data_table"):
        L.append(f"{T}dataCategory: Time")
    L.append("")

    for med_nome, dax, fmt, pasta in cfg.get("medidas", []):
        linhas_dax = dax.split("\n")
        if len(linhas_dax) == 1:
            L.append(f"{T}measure {q(med_nome)} = {dax}")
        else:
            L.append(f"{T}measure {q(med_nome)} =")
            L += [f"{T*3}{linha}" for linha in linhas_dax]
        L += [
            f"{T*2}formatString: {fmt}",
            f"{T*2}displayFolder: {pasta}",
            f"{T*2}lineageTag: {tag(nome, 'm', med_nome)}",
            "",
        ]

    for col, tipo, _m, ex in cfg["colunas"]:
        L.append(f"{T}column {q(col)}")
        L.append(f"{T*2}dataType: {tipo}")
        if ex.get("isKey"):
            L.append(f"{T*2}isKey")
        if ex.get("isHidden"):
            L.append(f"{T*2}isHidden")
        if "formatString" in ex:
            L.append(f"{T*2}formatString: {ex['formatString']}")
        L.append(f"{T*2}lineageTag: {tag(nome, col)}")
        if "dataCategory" in ex:
            L.append(f"{T*2}dataCategory: {ex['dataCategory']}")
        L.append(f"{T*2}summarizeBy: {ex.get('summarizeBy', 'none')}")
        L.append(f"{T*2}sourceColumn: {col}")
        if "sortByColumn" in ex:
            L.append(f"{T*2}sortByColumn: {q(ex['sortByColumn'])}")
        L += ["", f"{T*2}annotation SummarizationSetBy = Automatic", ""]

    tipos = ", ".join(f'{{"{c}", {m}}}' for c, _t, m, _e in cfg["colunas"])
    m = [
        "let",
        f'    Fonte = Csv.Document(Web.Contents(UrlBaseDados, [RelativePath = "{cfg["arquivo"]}"]), '
        "[Delimiter = \",\", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),",
        "    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),",
        f'    Tipos = Table.TransformColumnTypes(Cabecalhos, {{{tipos}}}, "en-US")',
        "in",
        "    Tipos",
    ]
    L += [f"{T}partition {q(nome)} = m", f"{T*2}mode: import", f"{T*2}source ="]
    L += [f"{T*4}{linha}" for linha in m]
    L += ["", f"{T}annotation PBI_ResultType = Table", ""]
    return "\n".join(L)


def escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo.rstrip() + "\n", encoding="utf-8", newline="\n")


def gerar_modelo(url_base: str) -> None:
    sm = PASTA / f"{NOME}.SemanticModel"
    d = sm / "definition"

    escrever(sm / "definition.pbism", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "settings": {},
    }, indent=2) + "\n")

    escrever(d / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n\n")

    ordem = ["UrlBaseDados", *TABELAS.keys()]
    model = [
        "model Model",
        "\tculture: pt-BR",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: pt-BR",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        f"annotation PBI_QueryOrder = {json.dumps(ordem, ensure_ascii=False, separators=(',', ':'))}",
        "",
        'annotation PBI_ProTooling = ["DevMode"]',
        "",
    ]
    model += [f"ref table {q(t)}" for t in TABELAS]
    escrever(d / "model.tmdl", "\n".join(model) + "\n\n")

    escrever(d / "expressions.tmdl", "\n".join([
        f'expression UrlBaseDados = "{url_base}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
        f"\tlineageTag: {tag('UrlBaseDados')}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
    ]) + "\n")

    rel = []
    for ft, fc, tt, tc in RELACOES:
        rel += [
            f"relationship {tag('rel', ft, fc, tt, tc)}",
            *(["\tjoinOnDateBehavior: datePartOnly"] if fc == "data_pedido" else []),
            f"\tfromColumn: {q(ft)}.{q(fc)}",
            f"\ttoColumn: {q(tt)}.{q(tc)}",
            "",
        ]
    escrever(d / "relationships.tmdl", "\n".join(rel) + "\n")

    for nome, cfg in TABELAS.items():
        escrever(d / "tables" / f"{nome}.tmdl", tmdl_tabela(nome, cfg))


# --------------------------------------------------------------------------- #
# Relatório (formato report.json do PBIP)
# --------------------------------------------------------------------------- #
ALIAS = {"fato_vendas": "f", "dim_calendario": "c", "dim_produto": "p", "dim_geografia": "g"}


def _lit(v: str) -> dict:
    return {"expr": {"Literal": {"Value": v}}}


def _campo(tabela: str, nome: str, medida: bool) -> dict:
    tipo = "Measure" if medida else "Column"
    return {tipo: {"Expression": {"SourceRef": {"Source": ALIAS[tabela]}}, "Property": nome}}


def visual(nome_id: str, tipo: str, pos: tuple[int, int, int, int], papeis: dict[str, list[tuple]],
           titulo: str | None = None, ordem: tuple | None = None, objetos: dict | None = None) -> dict:
    """papeis: {"Category": [("dim_produto", "categoria", False)], "Y": [("fato_vendas", "Receita Líquida", True)]}"""
    x, y, w, h = pos
    tabelas = []
    select = []
    projections: dict[str, list] = {}
    for papel, campos in papeis.items():
        projections[papel] = []
        for tabela, campo, medida in campos:
            if tabela not in tabelas:
                tabelas.append(tabela)
            ref = f"{tabela}.{campo}"
            if not any(s["Name"] == ref for s in select):
                select.append({**_campo(tabela, campo, medida), "Name": ref, "NativeReferenceName": campo})
            proj = {"queryRef": ref}
            if papel in ("Category", "Values") and not medida:
                proj["active"] = True
            projections[papel].append(proj)

    query = {
        "Version": 2,
        "From": [{"Name": ALIAS[t], "Entity": t, "Type": 0} for t in tabelas],
        "Select": select,
    }
    if ordem:
        tabela, campo, medida, direcao = ordem
        query["OrderBy"] = [{"Direction": direcao, "Expression": _campo(tabela, campo, medida)}]

    single = {
        "visualType": tipo,
        "projections": projections,
        "prototypeQuery": query,
        "drillFilterOtherVisuals": True,
    }
    if objetos:
        single["objects"] = objetos
    if titulo:
        single["vcObjects"] = {"title": [{"properties": {
            "show": _lit("true"), "text": _lit(f"'{titulo}'")}}]}

    config = {
        "name": nome_id,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": single,
    }
    return {"x": x, "y": y, "z": 0, "width": w, "height": h,
            "config": json.dumps(config, ensure_ascii=False), "filters": "[]"}


def slicer(nome_id: str, pos, tabela: str, campo: str, titulo: str) -> dict:
    return visual(nome_id, "slicer", pos, {"Values": [(tabela, campo, False)]}, titulo=titulo,
                  objetos={"data": [{"properties": {"mode": _lit("'Dropdown'")}}]})


def card(nome_id: str, pos, medida: str) -> dict:
    return visual(nome_id, "card", pos, {"Values": [("fato_vendas", medida, True)]})


RL = ("fato_vendas", "Receita Líquida", True)


def gerar_relatorio() -> None:
    rp = PASTA / f"{NOME}.Report"
    escrever(rp / "definition.pbir", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}},
    }, indent=2) + "\n")

    pagina1 = [
        slicer("slAno", (24, 16, 200, 64), "dim_calendario", "ano", "Ano"),
        slicer("slRegiao", (236, 16, 200, 64), "dim_geografia", "regiao", "Região"),
        slicer("slCanal", (448, 16, 200, 64), "fato_vendas", "canal", "Canal"),
        card("cdReceita", (24, 96, 296, 112), "Receita Líquida"),
        card("cdPedidos", (336, 96, 296, 112), "Pedidos Entregues"),
        card("cdTicket", (648, 96, 296, 112), "Ticket Médio"),
        card("cdMargem", (960, 96, 296, 112), "Margem Bruta %"),
        visual("lnReceitaMes", "lineChart", (24, 224, 816, 232),
               {"Category": [("dim_calendario", "mes_ano", False)], "Y": [RL]},
               titulo="Receita líquida por mês",
               ordem=("dim_calendario", "mes_ano", False, 1)),
        visual("dnCanal", "donutChart", (856, 224, 400, 232),
               {"Category": [("fato_vendas", "canal", False)], "Y": [RL]},
               titulo="Receita por canal"),
        visual("brCategoria", "clusteredBarChart", (24, 472, 616, 232),
               {"Category": [("dim_produto", "categoria", False)], "Y": [RL]},
               titulo="Receita por categoria",
               ordem=(*RL, 2)),
        visual("brUF", "clusteredColumnChart", (656, 472, 600, 232),
               {"Category": [("dim_geografia", "uf", False)], "Y": [RL]},
               titulo="Receita por UF",
               ordem=(*RL, 2)),
    ]

    pagina2 = [
        slicer("slAno2", (24, 16, 200, 64), "dim_calendario", "ano", "Ano"),
        slicer("slCategoria2", (236, 16, 200, 64), "dim_produto", "categoria", "Categoria"),
        card("cdPrazo", (24, 96, 296, 112), "Entregas no Prazo %"),
        card("cdPrazoMedio", (336, 96, 296, 112), "Prazo Médio (dias)"),
        card("cdCancel", (648, 96, 296, 112), "Taxa de Cancelamento %"),
        card("cdDevol", (960, 96, 296, 112), "Taxa de Devolução %"),
        visual("tbProdutos", "tableEx", (24, 224, 760, 480),
               {"Values": [("dim_produto", "produto", False), ("dim_produto", "categoria", False),
                           ("fato_vendas", "Itens Vendidos", True), RL,
                           ("fato_vendas", "Margem Bruta %", True)]},
               titulo="Ranking de produtos",
               ordem=(*RL, 2)),
        visual("brPrazoRegiao", "clusteredBarChart", (800, 224, 456, 232),
               {"Category": [("dim_geografia", "regiao", False)],
                "Y": [("fato_vendas", "Entregas no Prazo %", True)]},
               titulo="Entregas no prazo por região",
               ordem=("fato_vendas", "Entregas no Prazo %", True, 2)),
        visual("dnPagamento", "donutChart", (800, 472, 456, 232),
               {"Category": [("fato_vendas", "forma_pagamento", False)], "Y": [RL]},
               titulo="Receita por forma de pagamento"),
    ]

    def secao(nome: str, exibicao: str, ordinal: int, visuais: list) -> dict:
        return {"name": nome, "displayName": exibicao, "displayOption": 1, "ordinal": ordinal,
                "width": 1280, "height": 720, "config": "{}", "filters": "[]",
                "visualContainers": visuais}

    config = {
        "version": "5.43",
        "themeCollection": {},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "exportDataMode": 1,
        },
    }
    report = {
        "config": json.dumps(config),
        "layoutOptimization": 0,
        "sections": [
            secao("VisaoGeral0000000001", "Visão Geral", 0, pagina1),
            secao("ProdutosLogistica0002", "Produtos & Logística", 1, pagina2),
        ],
    }
    escrever(rp / "report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def gerar_pbip_e_tema() -> None:
    escrever(PASTA / f"{NOME}.pbip", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }, indent=2) + "\n")

    tema = {
        "name": "Tema Vendas E-commerce",
        "dataColors": PALETA,
        "foreground": "#0b0b0b",
        "foregroundNeutralSecondary": "#52514e",
        "foregroundNeutralTertiary": "#898781",
        "background": "#fcfcfb",
        "backgroundLight": "#f9f9f7",
        "backgroundNeutral": "#e1e0d9",
        "tableAccent": PALETA[0],
        "good": "#0ca30c",
        "neutral": "#fab219",
        "bad": "#d03b3b",
        "maximum": "#104281",
        "center": "#f0efec",
        "minimum": "#cde2fb",
        "textClasses": {
            "callout": {"fontSize": 28, "fontFace": "Segoe UI Semibold", "color": "#0b0b0b"},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#0b0b0b"},
            "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#0b0b0b"},
            "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#52514e"},
        },
        "visualStyles": {
            "*": {"*": {
                "border": [{"show": False}],
                "dropShadow": [{"show": False}],
                "background": [{"show": True, "color": {"solid": {"color": "#ffffff"}}, "transparency": 0}],
            }},
            "page": {"*": {"background": [{"color": {"solid": {"color": "#f4f4f1"}}, "transparency": 0}]}},
        },
    }
    escrever(PASTA / "tema" / "TemaVendas.json", json.dumps(tema, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url-base", required=True,
                    help="URL (terminada em /) da pasta data/ — ex.: raw.githubusercontent.com/<user>/<repo>/main/data/")
    args = ap.parse_args()
    url = args.url_base if args.url_base.endswith("/") else args.url_base + "/"
    gerar_modelo(url)
    gerar_relatorio()
    gerar_pbip_e_tema()
    print(f"PBIP gerado em {PASTA}")


if __name__ == "__main__":
    main()
