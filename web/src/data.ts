// Carrega o dataset colunar (gerado por scripts/gerar_dados.py) e faz as agregações
// no navegador — as mesmas regras de negócio das medidas DAX do Power BI.

export interface RawData {
  meta: { inicio: string; fim: string; seed: number }
  dim: {
    canais: string[]
    pagamentos: string[]
    status: string[] // ["Entregue", "Devolvido", "Cancelado"]
    ufs: { uf: string; estado: string; regiao: string }[]
    produtos: { id: number; nome: string; categoria: string }[]
  }
  fato: {
    dia: number[]
    cliente: number[]
    produto: number[]
    uf: number[]
    canal: number[]
    pagamento: number[]
    status: number[]
    qtd: number[]
    receita: number[] // centavos
    custo: number[] // centavos
    prazo: number[] // -1 = sem entrega
    noPrazo: number[] // -1 = sem entrega
  }
}

export interface Dataset {
  raw: RawData
  n: number
  anos: number[]
  anoDaLinha: Int16Array
  mesDaLinha: Int8Array
  categorias: string[]
  categoriaDoProduto: Int8Array
  regioes: string[]
  regiaoDaUf: Int8Array
}

export interface Filtros {
  ano: number | 'todos'
  regiao: string
  canal: string
  categoria: string
}

export const TODOS = 'todos'
const ENTREGUE = 0
const DEVOLVIDO = 1
const CANCELADO = 2

export async function carregarDataset(): Promise<Dataset> {
  const resp = await fetch(`${import.meta.env.BASE_URL}data/vendas.json`)
  if (!resp.ok) throw new Error(`Falha ao carregar dados (${resp.status})`)
  const raw = (await resp.json()) as RawData
  return prepararDataset(raw)
}

/** Prepara índices de calendário e dimensões sem depender do navegador. */
export function prepararDataset(raw: RawData): Dataset {
  const n = raw.fato.dia.length

  const inicio = Date.parse(raw.meta.inicio + 'T00:00:00Z')
  const anoDaLinha = new Int16Array(n)
  const mesDaLinha = new Int8Array(n)
  const cache = new Map<number, [number, number]>()
  for (let i = 0; i < n; i++) {
    const d = raw.fato.dia[i]
    let am = cache.get(d)
    if (!am) {
      const dt = new Date(inicio + d * 86_400_000)
      am = [dt.getUTCFullYear(), dt.getUTCMonth()]
      cache.set(d, am)
    }
    anoDaLinha[i] = am[0]
    mesDaLinha[i] = am[1]
  }

  const categorias = [...new Set(raw.dim.produtos.map((p) => p.categoria))]
  const categoriaDoProduto = new Int8Array(raw.dim.produtos.length + 1)
  raw.dim.produtos.forEach((p) => (categoriaDoProduto[p.id] = categorias.indexOf(p.categoria)))

  const regioes = [...new Set(raw.dim.ufs.map((u) => u.regiao))]
  const regiaoDaUf = Int8Array.from(raw.dim.ufs.map((u) => regioes.indexOf(u.regiao)))

  const anos = [...new Set(anoDaLinha)].sort()
  return { raw, n, anos, anoDaLinha, mesDaLinha, categorias, categoriaDoProduto, regioes, regiaoDaUf }
}

export interface Totais {
  receita: number
  custo: number
  pedidos: number
  entregues: number
  cancelados: number
  devolvidos: number
  itens: number
  noPrazo: number
  prazoSoma: number
  clientes: Set<number>
}

const novoTotal = (): Totais => ({
  receita: 0, custo: 0, pedidos: 0, entregues: 0, cancelados: 0, devolvidos: 0,
  itens: 0, noPrazo: 0, prazoSoma: 0, clientes: new Set(),
})

export function somarTotais(a: Totais, b: Totais): Totais {
  return {
    receita: a.receita + b.receita,
    custo: a.custo + b.custo,
    pedidos: a.pedidos + b.pedidos,
    entregues: a.entregues + b.entregues,
    cancelados: a.cancelados + b.cancelados,
    devolvidos: a.devolvidos + b.devolvidos,
    itens: a.itens + b.itens,
    noPrazo: a.noPrazo + b.noPrazo,
    prazoSoma: a.prazoSoma + b.prazoSoma,
    clientes: new Set([...a.clientes, ...b.clientes]),
  }
}

/** Medidas derivadas — equivalentes às medidas DAX do modelo Power BI. */
export function medidas(t: Totais) {
  const receita = t.receita / 100
  const custo = t.custo / 100
  return {
    receita,
    lucro: receita - custo,
    margem: receita ? (receita - custo) / receita : 0,
    pedidosEntregues: t.entregues,
    ticketMedio: t.entregues ? receita / t.entregues : 0,
    clientesAtivos: t.clientes.size,
    entregasNoPrazo: t.entregues ? t.noPrazo / t.entregues : 0,
    prazoMedio: t.entregues ? t.prazoSoma / t.entregues : 0,
    taxaCancelamento: t.pedidos ? t.cancelados / t.pedidos : 0,
    taxaDevolucao: t.pedidos ? t.devolvidos / t.pedidos : 0,
    itens: t.itens,
  }
}
export type Medidas = ReturnType<typeof medidas>

export interface Agregado {
  /** Totais por ano (respeita região/canal/categoria, ignora o filtro de ano). */
  porAno: Map<number, Totais>
  /** Receita mensal (R$) por ano — para o comparativo anual. */
  mensal: Map<number, number[]>
  /** Mix de receita por canal e por pagamento, por ano (ignora o próprio filtro). */
  canalPorAno: Map<number, number[]>
  pagamentoPorAno: Map<number, number[]>
  /** Recortes do período selecionado. */
  categoria: { receita: number; custo: number }[]
  uf: number[]
  produto: { receita: number; custo: number; qtd: number }[]
}

export function agregar(ds: Dataset, f: Filtros): Agregado {
  const { raw } = ds
  const F = raw.fato
  const regiaoIdx = f.regiao === TODOS ? -1 : ds.regioes.indexOf(f.regiao)
  const canalIdx = f.canal === TODOS ? -1 : raw.dim.canais.indexOf(f.canal)
  const catIdx = f.categoria === TODOS ? -1 : ds.categorias.indexOf(f.categoria)

  const porAno = new Map<number, Totais>()
  const mensal = new Map<number, number[]>()
  const canalPorAno = new Map<number, number[]>()
  const pagamentoPorAno = new Map<number, number[]>()
  for (const a of ds.anos) {
    porAno.set(a, novoTotal())
    mensal.set(a, new Array(12).fill(0))
    canalPorAno.set(a, new Array(raw.dim.canais.length).fill(0))
    pagamentoPorAno.set(a, new Array(raw.dim.pagamentos.length).fill(0))
  }
  const categoria = ds.categorias.map(() => ({ receita: 0, custo: 0 }))
  const uf = new Array(raw.dim.ufs.length).fill(0)
  const produto = new Array(raw.dim.produtos.length + 1).fill(null).map(() => ({ receita: 0, custo: 0, qtd: 0 }))

  for (let i = 0; i < ds.n; i++) {
    if (regiaoIdx >= 0 && ds.regiaoDaUf[F.uf[i]] !== regiaoIdx) continue
    if (catIdx >= 0 && ds.categoriaDoProduto[F.produto[i]] !== catIdx) continue

    const ano = ds.anoDaLinha[i]
    const st = F.status[i]
    const entregue = st === ENTREGUE
    const receita = F.receita[i]

    if (entregue) canalPorAno.get(ano)![F.canal[i]] += receita / 100
    if (canalIdx >= 0 && F.canal[i] !== canalIdx) continue

    const t = porAno.get(ano)!
    t.pedidos++
    if (st === CANCELADO) t.cancelados++
    else if (st === DEVOLVIDO) t.devolvidos++
    if (!entregue) continue

    t.entregues++
    t.receita += receita
    t.custo += F.custo[i]
    t.itens += F.qtd[i]
    t.noPrazo += F.noPrazo[i]
    t.prazoSoma += F.prazo[i]
    t.clientes.add(F.cliente[i])
    mensal.get(ano)![ds.mesDaLinha[i]] += receita / 100
    pagamentoPorAno.get(ano)![F.pagamento[i]] += receita / 100

    if (f.ano !== TODOS && ano !== f.ano) continue
    const c = categoria[ds.categoriaDoProduto[F.produto[i]]]
    c.receita += receita / 100
    c.custo += F.custo[i] / 100
    uf[F.uf[i]] += receita / 100
    const p = produto[F.produto[i]]
    p.receita += receita / 100
    p.custo += F.custo[i] / 100
    p.qtd += F.qtd[i]
  }

  return { porAno, mensal, canalPorAno, pagamentoPorAno, categoria, uf, produto }
}

export function totaisDoPeriodo(ds: Dataset, agg: Agregado, ano: Filtros['ano']): Totais {
  if (ano !== TODOS) return agg.porAno.get(ano)!
  return ds.anos.map((a) => agg.porAno.get(a)!).reduce(somarTotais)
}
