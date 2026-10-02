import type { ReactNode } from 'react'

export function Painel({
  titulo,
  subtitulo,
  children,
  className = '',
  acao,
}: {
  titulo: string
  subtitulo?: string
  children: ReactNode
  className?: string
  acao?: ReactNode
}) {
  return (
    <section className={`painel ${className}`}>
      <header className="painel-cab">
        <div>
          <h2>{titulo}</h2>
          {subtitulo && <p className="sub">{subtitulo}</p>}
        </div>
        {acao}
      </header>
      {children}
    </section>
  )
}

export interface Delta {
  texto: string
  sobe: boolean // direção da variação (define a seta)
  positivo: boolean // a variação é boa para o negócio? (define a cor)
  neutro?: boolean
}

export function KpiTile({ rotulo, valor, delta, rodape }: { rotulo: string; valor: string; delta?: Delta; rodape?: string }) {
  return (
    <div className="kpi">
      <span className="kpi-rotulo">{rotulo}</span>
      <span className="kpi-valor">{valor}</span>
      {delta ? (
        <span className={`kpi-delta ${delta.neutro ? 'neutro' : delta.positivo ? 'bom' : 'ruim'}`}>
          <span aria-hidden="true">{delta.neutro ? '•' : delta.sobe ? '▲' : '▼'}</span> {delta.texto}
          <span className="kpi-vs"> vs 2024</span>
        </span>
      ) : (
        <span className="kpi-delta neutro">{rodape ?? ' '}</span>
      )}
    </div>
  )
}

export function Legenda({ itens }: { itens: { nome: string; cor: string; tipo?: 'linha' | 'bloco' }[] }) {
  return (
    <ul className="legenda">
      {itens.map((i) => (
        <li key={i.nome}>
          <span className={`chave ${i.tipo ?? 'bloco'}`} style={{ background: i.cor }} />
          {i.nome}
        </li>
      ))}
    </ul>
  )
}

export function TooltipCaixa({ titulo, linhas }: { titulo: string; linhas: { nome: string; valor: string; cor?: string }[] }) {
  return (
    <div className="tooltip">
      <div className="tooltip-titulo">{titulo}</div>
      {linhas.map((l) => (
        <div className="tooltip-linha" key={l.nome}>
          {l.cor && <span className="chave bloco" style={{ background: l.cor }} />}
          <span className="tooltip-nome">{l.nome}</span>
          <span className="tooltip-valor">{l.valor}</span>
        </div>
      ))}
    </div>
  )
}
