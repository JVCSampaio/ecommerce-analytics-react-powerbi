"""Confere integridade do modelo estrela e equivalência CSV/JSON, sem dependências."""
from collections import defaultdict
import csv
from datetime import date
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(name):
    with (ROOT / 'data' / f'{name}.csv').open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    raw = json.loads((ROOT / 'web/public/data/vendas.json').read_text(encoding='utf-8'))
    rows = read_csv('fato_vendas')
    require(all(len(values) == len(rows) for values in raw['fato'].values()), 'Tamanhos CSV/JSON divergentes')
    require(len({r['id_pedido'] for r in rows}) == len(rows), 'Pedidos duplicados')
    keys = {
        'id_cliente': {r['id_cliente'] for r in read_csv('dim_cliente')},
        'id_produto': {r['id_produto'] for r in read_csv('dim_produto')},
        'uf': {r['uf'] for r in read_csv('dim_geografia')},
        'data_pedido': {r['data'] for r in read_csv('dim_calendario')},
    }
    for name, dimension in [('dim_cliente', 'id_cliente'), ('dim_produto', 'id_produto'),
                            ('dim_geografia', 'uf'), ('dim_calendario', 'data')]:
        dim = read_csv(name)
        require(len({r[dimension] for r in dim}) == len(dim), f'Chave duplicada em {name}')
    metrics = defaultdict(lambda: {'receita_centavos': 0, 'custo_centavos': 0, 'entregues': 0})
    for i, row in enumerate(rows):
        require(all(row[k] in valid for k, valid in keys.items()), f'Referência inválida no pedido {i}')
        expected = {
            'dia': (date.fromisoformat(row['data_pedido']) - date.fromisoformat(raw['meta']['inicio'])).days,
            'cliente': int(row['id_cliente']), 'produto': int(row['id_produto']),
            'qtd': int(row['quantidade']),
            'receita': int(Decimal(row['receita_liquida']) * 100),
            'custo': int(Decimal(row['custo_total']) * 100),
            'prazo': int(row['prazo_entrega_dias'] or -1),
            'noPrazo': int(row['entregue_no_prazo'] or -1),
            'uf': next(n for n, u in enumerate(raw['dim']['ufs']) if u['uf'] == row['uf']),
            'canal': raw['dim']['canais'].index(row['canal']),
            'pagamento': raw['dim']['pagamentos'].index(row['forma_pagamento']),
            'status': raw['dim']['status'].index(row['status']),
        }
        require(all(raw['fato'][k][i] == v for k, v in expected.items()), f'CSV/JSON divergem na linha {i}')
        if row['status'] == 'Entregue':
            m = metrics[row['data_pedido'][:4]]
            m['receita_centavos'] += expected['receita']
            m['custo_centavos'] += expected['custo']
            m['entregues'] += 1
    for path in (ROOT / 'powerbi').rglob('*'):
        if path.suffix in {'.json', '.pbip', '.pbir', '.pbism'}:
            json.loads(path.read_text(encoding='utf-8'))
    report = json.loads((ROOT / 'powerbi/VendasEcommerce.Report/report.json').read_text(encoding='utf-8'))
    require(len(report['sections']) == 2, 'O relatório deve ter duas páginas')
    for section in report['sections']:
        for visual in section['visualContainers']:
            json.loads(visual['config'])
            json.loads(visual['filters'])
    print(f'OK: {len(rows):,} pedidos; quatro dimensões; CSV/JSON equivalentes; JSON do PBIP válido.')
    print(json.dumps(dict(metrics), indent=2))


if __name__ == '__main__':
    main()
