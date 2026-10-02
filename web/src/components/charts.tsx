import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fmt, MESES } from '../format'
import type { Tokens } from '../theme'
import { Legenda, TooltipCaixa } from './ui'

const eixoTick = (t: Tokens) => ({ fill: t.muted, fontSize: 12 })

/** Escolhe tinta preta ou branca para texto dentro de um preenchimento colorido. */
function tintaSobre(hex: string) {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const lin = c.map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
  const L = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
  return 1.05 / (L + 0.05) >= (L + 0.05) / 0.05 ? '#ffffff' : '#0b0b0b'
}

/* ------------------------------------------------------------------------- */
/* Comparativo mensal ano a ano                                              */
/* ------------------------------------------------------------------------- */
export function TendenciaMensal({
  mensal,
  anoDestaque,
  t,
}: {
  mensal: Map<number, number[]>
  anoDestaque: number
  t: Tokens
}) {
  const anos = [...mensal.keys()].sort()
  const dados = MESES.map((m, i) => {
    const linha: Record<string, number | string> = { mes: m }
    for (const a of anos) linha[String(a)] = mensal.get(a)![i]
    return linha
  })
  const cor = (a: number) => (a === anoDestaque ? t.series[0] : t.deEnfase)

  return (
    <>
      <Legenda itens={anos.map((a) => ({ nome: String(a), cor: cor(a), tipo: 'linha' as const })).reverse()} />
      <div className="grafico" style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dados} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid vertical={false} stroke={t.grid} />
            <XAxis dataKey="mes" tick={eixoTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} />
            <YAxis
              tick={eixoTick(t)}
              tickLine={false}
              axisLine={false}
              width={72}
              tickFormatter={(v: number) => fmt.brlCompacto(v)}
            />
            <Tooltip
              cursor={{ stroke: t.axis, strokeWidth: 1 }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <TooltipCaixa
                    titulo={String(label)}
                    linhas={[...payload]
                      .sort((a, b) => Number(b.dataKey) - Number(a.dataKey))
                      .map((p) => ({
                        nome: String(p.dataKey),
                        valor: fmt.brlInteiro(Number(p.value)),
                        cor: cor(Number(p.dataKey)),
                      }))}
                  />
                ) : null
              }
            />
            {anos.map((a) => (
              <Line
                key={a}
                type="monotone"
                dataKey={String(a)}
                stroke={cor(a)}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, stroke: t.surface, strokeWidth: 2 }}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}

/* ------------------------------------------------------------------------- */
/* Barras horizontais (série única)                                          */
/* ------------------------------------------------------------------------- */
export function BarrasHorizontais({
  dados,
  t,
  detalhe,
  altura,
}: {
  dados: { nome: string; valor: number }[]
  t: Tokens
  detalhe?: (nome: string) => string
  altura?: number
}) {
  const h = altura ?? Math.max(160, dados.length * 34 + 16)
  return (
    <div className="grafico" style={{ height: h }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={dados} layout="vertical" margin={{ top: 0, right: 84, bottom: 0, left: 0 }} barCategoryGap={6}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="nome"
            width={140}
            tick={{ fill: t.ink2, fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: t.axis }}
          />
          <Tooltip
            cursor={{ fill: t.grid, opacity: 0.5 }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <TooltipCaixa
                  titulo={String(payload[0].payload.nome)}
                  linhas={[
                    { nome: 'Receita líquida', valor: fmt.brlInteiro(Number(payload[0].value)) },
                    ...(detalhe ? [{ nome: 'Margem bruta', valor: detalhe(String(payload[0].payload.nome)) }] : []),
                  ]}
                />
              ) : null
            }
          />
          <Bar dataKey="valor" fill={t.series[0]} barSize={18} radius={[0, 4, 4, 0]} isAnimationActive={false}>
            <LabelList
              dataKey="valor"
              position="right"
              formatter={(v) => fmt.brlCompacto(Number(v))}
              style={{ fill: t.ink2, fontSize: 12 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ------------------------------------------------------------------------- */
/* Mix 100% empilhado por ano (HTML puro — 2px de respiro entre segmentos)    */
/* ------------------------------------------------------------------------- */
export function MixPorAno({
  porAno,
  nomes,
  t,
}: {
  porAno: Map<number, number[]>
  nomes: string[]
  t: Tokens
}) {
  const [hover, setHover] = useState<{ ano: number; i: number } | null>(null)
  const anos = [...porAno.keys()].sort()
  const partes = anos.map((a) => {
    const v = porAno.get(a)!
    const total = v.reduce((s, x) => s + x, 0) || 1
    return { ano: a, valores: v, shares: v.map((x) => x / total) }
  })
  const ultimo = partes[partes.length - 1]
  const primeiro = partes[0]

  return (
    <div className="mix">
      <Legenda itens={nomes.map((n, i) => ({ nome: n, cor: t.series[i] }))} />
      {partes.map((p) => (
        <div className="mix-linha" key={p.ano}>
          <span className="mix-ano">{p.ano}</span>
          <div className="mix-barra" role="img" aria-label={`Mix ${p.ano}: ${nomes.map((n, i) => `${n} ${fmt.pct(p.shares[i])}`).join(', ')}`}>
            {p.shares.map((s, i) => (
              <div
                key={nomes[i]}
                className={`mix-seg ${hover && (hover.ano !== p.ano || hover.i !== i) ? 'apagado' : ''}`}
                style={{ flexGrow: s, background: t.series[i], color: tintaSobre(t.series[i]) }}
                onMouseEnter={() => setHover({ ano: p.ano, i })}
                onMouseLeave={() => setHover(null)}
              >
                {s >= 0.12 && <span>{fmt.pct(s)}</span>}
              </div>
            ))}
          </div>
        </div>
      ))}
      <p className="mix-nota">
        {hover ? (
          <>
            <strong>{nomes[hover.i]}</strong> em {hover.ano}: {fmt.brlInteiro(porAno.get(hover.ano)![hover.i])} (
            {fmt.pct(partes.find((x) => x.ano === hover.ano)!.shares[hover.i])} da receita)
          </>
        ) : (
          nomes
            .map((n, i) => ({ n, d: ultimo.shares[i] - primeiro.shares[i] }))
            .sort((a, b) => b.d - a.d)
            .slice(0, 1)
            .map(({ n, d }) => (
              <span key={n}>
                Maior ganho de participação: <strong>{n}</strong> ({fmt.pp(d)} de {primeiro.ano} para {ultimo.ano})
              </span>
            ))
        )}
      </p>
    </div>
  )
}
