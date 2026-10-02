import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { agregar, medidas, prepararDataset, totaisDoPeriodo, TODOS } from '../src/data.ts'
import type { RawData, Filtros } from '../src/data.ts'

const raw = JSON.parse(readFileSync(new URL('../public/data/vendas.json', import.meta.url), 'utf8')) as RawData
const ds = prepararDataset(raw)
const filtros: Filtros[] = [
  { ano: 2025, regiao: TODOS, canal: TODOS, categoria: TODOS },
  { ano: 2024, regiao: 'Norte', canal: TODOS, categoria: TODOS },
  { ano: TODOS, regiao: 'Sudeste', canal: 'App', categoria: 'Moda' },
]

for (const f of filtros) {
  test(`KPIs respeitam status e filtros: ${JSON.stringify(f)}`, () => {
    const agg = agregar(ds, f)
    const m = medidas(totaisDoPeriodo(ds, agg, f.ano))
    // Referência independente: seleção de linhas, sem os índices da agregação.
    const selecionadas = raw.fato.dia.map((d, i) => ({
      i, ano: new Date(Date.parse(raw.meta.inicio + 'T00:00:00Z') + d * 86400000).getUTCFullYear(),
    })).filter(({ i, ano }) =>
      (f.ano === TODOS || ano === f.ano)
      && (f.regiao === TODOS || raw.dim.ufs[raw.fato.uf[i]].regiao === f.regiao)
      && (f.canal === TODOS || raw.dim.canais[raw.fato.canal[i]] === f.canal)
      && (f.categoria === TODOS || raw.dim.produtos.find(p => p.id === raw.fato.produto[i])!.categoria === f.categoria),
    )
    const entregues = selecionadas.filter(({ i }) => raw.dim.status[raw.fato.status[i]] === 'Entregue')
    const soma = (campo: keyof RawData['fato']) => entregues.reduce((s, { i }) => s + raw.fato[campo][i], 0)
    assert.equal(m.receita, soma('receita') / 100)
    assert.equal(Math.round(m.lucro * 100), soma('receita') - soma('custo'))
    assert.equal(m.pedidosEntregues, entregues.length)
    assert.equal(m.clientesAtivos, new Set(entregues.map(({ i }) => raw.fato.cliente[i])).size)
    assert.equal(m.entregasNoPrazo, soma('noPrazo') / entregues.length)
    assert.ok(Math.abs(agg.categoria.reduce((s, c) => s + c.receita, 0) - m.receita) < 0.000001)
    assert.ok(Math.abs(agg.uf.reduce((s, n) => s + n, 0) - m.receita) < 0.000001)
    assert.ok(Math.abs(agg.produto.reduce((s, p) => s + p.receita, 0) - m.receita) < 0.000001)
  })
}

test('período sem vendas não exibe NaN ou Infinity', () => {
  const agg = agregar(ds, { ano: 2025, regiao: 'Norte', canal: 'App', categoria: 'Moda' })
  const total = totaisDoPeriodo(ds, agg, 2025)
  const vazio = { ...total, receita: 0, custo: 0, pedidos: 0, entregues: 0, clientes: new Set<number>() }
  assert.equal(medidas(vazio).ticketMedio, 0)
  assert.equal(medidas(vazio).margem, 0)
})
