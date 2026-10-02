import { fmt } from '../format'
import type { Tokens } from '../theme'

export interface LinhaProduto {
  nome: string
  categoria: string
  qtd: number
  receita: number
  margem: number
}

export function TopProdutos({ linhas, t }: { linhas: LinhaProduto[]; t: Tokens }) {
  const max = Math.max(...linhas.map((l) => l.receita), 1)
  return (
    <div className="tabela-wrap">
      <table className="tabela">
        <thead>
          <tr>
            <th>#</th>
            <th>Produto</th>
            <th className="num col-itens">Itens</th>
            <th className="num">Receita líquida</th>
            <th className="num">Margem</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={l.nome}>
              <td className="rank">{i + 1}</td>
              <td>
                <div className="produto-nome">{l.nome}</div>
                <div className="produto-cat">{l.categoria}</div>
              </td>
              <td className="num col-itens">{fmt.int(l.qtd)}</td>
              <td className="num">
                <div className="celula-barra">
                  <span>{fmt.brlInteiro(l.receita)}</span>
                  <span className="mini-trilho" aria-hidden="true">
                    <span className="mini-barra" style={{ width: `${(l.receita / max) * 100}%`, background: t.series[0] }} />
                  </span>
                </div>
              </td>
              <td className="num">{fmt.pct(l.margem)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
