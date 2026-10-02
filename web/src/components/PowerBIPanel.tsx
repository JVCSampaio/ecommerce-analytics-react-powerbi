import { Painel } from './ui'

const EMBED_URL = import.meta.env.VITE_POWERBI_EMBED_URL as string | undefined
const REPO_URL =
  (import.meta.env.VITE_REPO_URL as string | undefined) ?? 'https://github.com/JVCSampaio/ecommerce-analytics-react-powerbi'

const MEDIDAS = [
  ['Receita Líquida', 'CALCULATE ( SUM ( fato_vendas[receita_liquida] ), fato_vendas[status] = "Entregue" )'],
  ['Margem Bruta %', 'DIVIDE ( [Lucro Bruto], [Receita Líquida] )'],
  ['Ticket Médio', 'DIVIDE ( [Receita Líquida], [Pedidos Entregues] )'],
  ['Crescimento YoY %', 'VAR _anterior = [Receita Ano Anterior]\nRETURN IF ( NOT ISBLANK ( _anterior ), DIVIDE ( [Receita Líquida] - _anterior, _anterior ) )'],
  ['Entregas no Prazo %', 'DIVIDE ( CALCULATE ( SUM ( fato_vendas[entregue_no_prazo] ), fato_vendas[status] = "Entregue" ), [Pedidos Entregues] )'],
  ['Receita Acumulada no Ano', 'TOTALYTD ( [Receita Líquida], dim_calendario[data] )'],
]

function DiagramaEstrela() {
  const dims = [
    { nome: 'dim_calendario', campos: 'data · ano · mês', x: 20, y: 20 },
    { nome: 'dim_produto', campos: 'produto · categoria', x: 380, y: 20 },
    { nome: 'dim_cliente', campos: 'faixa etária · cadastro', x: 20, y: 196 },
    { nome: 'dim_geografia', campos: 'UF · estado · região', x: 380, y: 196 },
  ]
  const fato = { x: 200, y: 108 }
  return (
    <svg className="diagrama" viewBox="0 0 560 270" role="img" aria-label="Modelo estrela: fato_vendas ligada a quatro dimensões">
      {dims.map((d) => (
        <line key={d.nome} x1={d.x + 80} y1={d.y + 27} x2={fato.x + 80} y2={fato.y + 27} className="diag-rel" />
      ))}
      {dims.map((d) => (
        <g key={d.nome} transform={`translate(${d.x},${d.y})`}>
          <rect width="160" height="54" rx="8" className="diag-dim" />
          <text x="12" y="22" className="diag-titulo">{d.nome}</text>
          <text x="12" y="40" className="diag-campos">{d.campos}</text>
        </g>
      ))}
      <g transform={`translate(${fato.x},${fato.y})`}>
        <rect width="160" height="54" rx="8" className="diag-fato" />
        <text x="12" y="22" className="diag-titulo fato">fato_vendas</text>
        <text x="12" y="40" className="diag-campos fato">30 mil pedidos · 2 anos</text>
      </g>
    </svg>
  )
}

export function PowerBIPanel() {
  if (EMBED_URL) {
    return (
      <Painel titulo="Relatório Power BI" subtitulo="Publicado no Power BI Service e incorporado nesta página">
        <div className="embed">
          <iframe title="Relatório Power BI — Vendas E-commerce" src={EMBED_URL} allowFullScreen />
        </div>
      </Painel>
    )
  }

  return (
    <div className="grid-pbi">
      <Painel
        titulo="Relatório Power BI"
        subtitulo="O mesmo dataset e as mesmas regras de negócio do dashboard React, modelados no Power BI"
      >
        <ol className="passos">
          <li>
            Clone o repositório e abra <code>powerbi/VendasEcommerce.pbip</code> no Power BI Desktop.
          </li>
          <li>
            Clique em <strong>Atualizar</strong> — o modelo baixa os CSVs da pasta <code>data/</code> direto do GitHub
            (acesso anônimo).
          </li>
          <li>
            Opcional: <strong>Exibir → Temas → Procurar temas</strong> e escolha <code>powerbi/tema/TemaVendas.json</code>{' '}
            para usar a mesma paleta deste site.
          </li>
          <li>
            Para incorporar aqui: publique no Power BI Service, gere o link em{' '}
            <strong>Arquivo → Inserir relatório → Publicar na Web</strong>, salve-o como{' '}
            <code>VITE_POWERBI_EMBED_URL</code> em <code>web/.env.local</code> e rode <code>npm run build</code>.
          </li>
        </ol>
        <a className="botao" href={`${REPO_URL}/tree/main/powerbi`} target="_blank" rel="noreferrer">
          Ver projeto Power BI no GitHub
        </a>
      </Painel>

      <Painel titulo="Modelo de dados" subtitulo="Esquema estrela · relacionamentos 1:N partindo das dimensões">
        <DiagramaEstrela />
      </Painel>

      <Painel titulo="Medidas DAX principais" subtitulo="17 medidas no total, organizadas em pastas" className="span-2">
        <div className="medidas">
          {MEDIDAS.map(([nome, dax]) => (
            <div key={nome} className="medida">
              <div className="medida-nome">{nome}</div>
              <pre>
                <code>{dax}</code>
              </pre>
            </div>
          ))}
        </div>
      </Painel>
    </div>
  )
}
