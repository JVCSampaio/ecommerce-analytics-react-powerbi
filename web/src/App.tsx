import { useEffect, useMemo, useState, type ChangeEvent } from 'react'
import { BarrasHorizontais, MixPorAno, TendenciaMensal } from './components/charts'
import { PowerBIPanel } from './components/PowerBIPanel'
import { TopProdutos } from './components/TopProdutos'
import { KpiTile, Painel, type Delta } from './components/ui'
import { agregar, carregarDataset, medidas, totaisDoPeriodo, TODOS, type Dataset, type Filtros } from './data'
import { fmt } from './format'
import { useTema, type Preferencia, type Tokens } from './theme'

type Aba = 'react' | 'powerbi'

const FILTROS_INICIAIS: Filtros = { ano: 2025, regiao: TODOS, canal: TODOS, categoria: TODOS }

export default function App() {
  const [ds, setDs] = useState<Dataset | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIAIS)
  const [aba, setAba] = useState<Aba>('react')
  const { tokens: t, pref, setPref } = useTema()

  useEffect(() => {
    carregarDataset().then(setDs).catch((e: Error) => setErro(e.message))
  }, [])

  return (
    <div className="app">
      <header className="topo">
        <div className="marca">
          <span className="logo" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22">
              <rect x="3" y="12" width="4" height="9" rx="1.5" fill={t.series[0]} />
              <rect x="10" y="7" width="4" height="14" rx="1.5" fill={t.series[0]} opacity="0.75" />
              <rect x="17" y="3" width="4" height="18" rx="1.5" fill={t.series[0]} opacity="0.5" />
            </svg>
          </span>
          <div>
            <h1>Painel de Vendas · E-commerce</h1>
            <p className="sub">React + Power BI · dados sintéticos de jan/2024 a dez/2025</p>
          </div>
        </div>
        <div className="topo-acoes">
          <nav className="abas" role="tablist">
            <button role="tab" aria-selected={aba === 'react'} onClick={() => setAba('react')}>
              Dashboard React
            </button>
            <button role="tab" aria-selected={aba === 'powerbi'} onClick={() => setAba('powerbi')}>
              Power BI
            </button>
          </nav>
          <select
            className="tema"
            aria-label="Tema"
            value={pref}
            onChange={(e) => setPref(e.target.value as Preferencia)}
          >
            <option value="auto">Tema: sistema</option>
            <option value="light">Tema: claro</option>
            <option value="dark">Tema: escuro</option>
          </select>
        </div>
      </header>

      {aba === 'powerbi' ? (
        <PowerBIPanel />
      ) : erro ? (
        <div className="estado">Não foi possível carregar os dados: {erro}</div>
      ) : !ds ? (
        <div className="estado">Carregando 30 mil pedidos…</div>
      ) : (
        <Dashboard ds={ds} filtros={filtros} setFiltros={setFiltros} t={t} />
      )}

      <footer className="rodape">
        Projeto de portfólio · dataset gerado por <code>scripts/gerar_dados.py</code> · agregações feitas no navegador
        com as mesmas regras das medidas DAX
      </footer>
    </div>
  )
}

function Dashboard({
  ds,
  filtros,
  setFiltros,
  t,
}: {
  ds: Dataset
  filtros: Filtros
  setFiltros: (f: Filtros) => void
  t: Tokens
}) {
  const agg = useMemo(() => agregar(ds, filtros), [ds, filtros])
  const m = medidas(totaisDoPeriodo(ds, agg, filtros.ano))
  const anoAnterior = filtros.ano !== TODOS ? agg.porAno.get(filtros.ano - 1) : undefined
  const mAnt = anoAnterior && anoAnterior.pedidos > 0 ? medidas(anoAnterior) : null

  const rel = (atual: number, ant?: number): Delta | undefined =>
    mAnt && ant ? { texto: fmt.delta(atual / ant - 1), sobe: atual >= ant, positivo: atual >= ant } : undefined
  const pp = (atual: number, ant?: number, menorMelhor = false): Delta | undefined =>
    mAnt && ant !== undefined
      ? {
          texto: fmt.pp(atual - ant),
          sobe: atual >= ant,
          positivo: menorMelhor ? atual <= ant : atual >= ant,
          neutro: Math.abs(atual - ant) < 0.0005,
        }
      : undefined

  const categorias = ds.categorias
    .map((nome, i) => ({ nome, valor: agg.categoria[i].receita, custo: agg.categoria[i].custo }))
    .sort((a, b) => b.valor - a.valor)
  const margemCat = new Map(categorias.map((c) => [c.nome, c.valor ? 1 - c.custo / c.valor : 0]))

  const ufs = ds.raw.dim.ufs
    .map((u, i) => ({ nome: u.estado, valor: agg.uf[i] }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 8)

  const produtos = ds.raw.dim.produtos
    .map((p) => {
      const a = agg.produto[p.id]
      return { nome: p.nome, categoria: p.categoria, qtd: a.qtd, receita: a.receita, margem: a.receita ? 1 - a.custo / a.receita : 0 }
    })
    .filter((p) => p.receita > 0)
    .sort((a, b) => b.receita - a.receita)
    .slice(0, 10)

  const periodo = filtros.ano === TODOS ? '2024–2025' : String(filtros.ano)
  const set = (k: keyof Filtros) => (e: ChangeEvent<HTMLSelectElement>) =>
    setFiltros({ ...filtros, [k]: k === 'ano' && e.target.value !== TODOS ? Number(e.target.value) : e.target.value })
  const filtrado = filtros.regiao !== TODOS || filtros.canal !== TODOS || filtros.categoria !== TODOS || filtros.ano !== 2025

  return (
    <main>
      <div className="filtros" role="group" aria-label="Filtros">
        <label>
          Ano
          <select value={String(filtros.ano)} onChange={set('ano')}>
            {ds.anos.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
            <option value={TODOS}>Todos</option>
          </select>
        </label>
        <label>
          Região
          <select value={filtros.regiao} onChange={set('regiao')}>
            <option value={TODOS}>Todas</option>
            {ds.regioes.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          Canal
          <select value={filtros.canal} onChange={set('canal')}>
            <option value={TODOS}>Todos</option>
            {ds.raw.dim.canais.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Categoria
          <select value={filtros.categoria} onChange={set('categoria')}>
            <option value={TODOS}>Todas</option>
            {ds.categorias.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        {filtrado && (
          <button className="limpar" onClick={() => setFiltros(FILTROS_INICIAIS)}>
            Limpar filtros
          </button>
        )}
      </div>

      <div className="kpis">
        <KpiTile rotulo="Receita líquida" valor={fmt.brlCompacto(m.receita)} delta={rel(m.receita, mAnt?.receita)} rodape={periodo} />
        <KpiTile rotulo="Pedidos entregues" valor={fmt.int(m.pedidosEntregues)} delta={rel(m.pedidosEntregues, mAnt?.pedidosEntregues)} rodape={periodo} />
        <KpiTile rotulo="Ticket médio" valor={fmt.brl(m.ticketMedio)} delta={rel(m.ticketMedio, mAnt?.ticketMedio)} rodape={periodo} />
        <KpiTile rotulo="Margem bruta" valor={fmt.pct(m.margem)} delta={pp(m.margem, mAnt?.margem)} rodape={periodo} />
        <KpiTile rotulo="Clientes ativos" valor={fmt.int(m.clientesAtivos)} delta={rel(m.clientesAtivos, mAnt?.clientesAtivos)} rodape={periodo} />
        <KpiTile rotulo="Entregas no prazo" valor={fmt.pct(m.entregasNoPrazo)} delta={pp(m.entregasNoPrazo, mAnt?.entregasNoPrazo)} rodape={periodo} />
      </div>

      <div className="grid">
        <Painel
          className="span-2"
          titulo="Receita líquida mensal"
          subtitulo="Comparativo ano a ano · pico de novembro = Black Friday"
        >
          <TendenciaMensal mensal={agg.mensal} anoDestaque={filtros.ano === TODOS ? Math.max(...ds.anos) : filtros.ano} t={t} />
        </Painel>

        <Painel titulo="Receita por categoria" subtitulo={`${periodo} · passe o mouse para ver a margem`}>
          <BarrasHorizontais dados={categorias} t={t} detalhe={(n) => fmt.pct(margemCat.get(n) ?? 0)} />
        </Painel>

        <Painel titulo="Top 8 estados" subtitulo={`Receita líquida · ${periodo}`}>
          <BarrasHorizontais dados={ufs} t={t} />
        </Painel>

        <Painel titulo="Mix de canais" subtitulo="Participação na receita, por ano">
          <MixPorAno porAno={agg.canalPorAno} nomes={ds.raw.dim.canais} t={t} />
        </Painel>

        <Painel titulo="Mix de pagamentos" subtitulo="Participação na receita, por ano">
          <MixPorAno porAno={agg.pagamentoPorAno} nomes={ds.raw.dim.pagamentos} t={t} />
        </Painel>

        <Painel className="span-2" titulo="Top 10 produtos" subtitulo={`Por receita líquida · ${periodo}`}>
          <TopProdutos linhas={produtos} t={t} />
        </Painel>

        <Painel titulo="Operação" subtitulo={`Indicadores logísticos · ${periodo}`} className="span-2">
          <div className="kpis kpis-op">
            <KpiTile
                rotulo="Prazo médio de entrega"
                valor={fmt.dias(m.prazoMedio)}
                delta={
                  mAnt
                    ? {
                        texto: fmt.diasDelta(m.prazoMedio - mAnt.prazoMedio),
                        sobe: m.prazoMedio >= mAnt.prazoMedio,
                        positivo: m.prazoMedio <= mAnt.prazoMedio,
                        neutro: Math.abs(m.prazoMedio - mAnt.prazoMedio) < 0.05,
                      }
                    : undefined
                }
                rodape={periodo}
              />
            <KpiTile rotulo="Taxa de cancelamento" valor={fmt.pct(m.taxaCancelamento)} delta={pp(m.taxaCancelamento, mAnt?.taxaCancelamento, true)} rodape={periodo} />
            <KpiTile rotulo="Taxa de devolução" valor={fmt.pct(m.taxaDevolucao)} delta={pp(m.taxaDevolucao, mAnt?.taxaDevolucao, true)} rodape={periodo} />
            <KpiTile rotulo="Itens vendidos" valor={fmt.int(m.itens)} delta={rel(m.itens, mAnt?.itens)} rodape={periodo} />
          </div>
        </Painel>
      </div>
    </main>
  )
}
