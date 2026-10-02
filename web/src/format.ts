const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const brlCompacto = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact',
  maximumFractionDigits: 2,
})
const brlInteiro = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const inteiro = new Intl.NumberFormat('pt-BR')
const pct = new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 })
const um = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

export const fmt = {
  brl: (v: number) => brl.format(v),
  brlCompacto: (v: number) => brlCompacto.format(v),
  brlInteiro: (v: number) => brlInteiro.format(v),
  int: (v: number) => inteiro.format(v),
  pct: (v: number) => pct.format(v),
  dias: (v: number) => `${um.format(v)} dias`,
  diasDelta: (v: number) => Math.abs(v) < 0.05 ? 'estável' : `${v > 0 ? '+' : ''}${um.format(v)} dia${Math.abs(v) >= 2 ? 's' : ''}`,
  /** Variação relativa com sinal: +12,3% */
  delta: (v: number) => (v > 0 ? '+' : '') + pct.format(v),
  /** Variação em pontos percentuais: +1,2 p.p. */
  pp: (v: number) => (v > 0 ? '+' : '') + um.format(v * 100) + ' p.p.',
}

export const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
