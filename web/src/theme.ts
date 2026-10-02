import { useEffect, useState } from 'react'

// Paleta categórica validada para daltonismo (ordem fixa — nunca reciclar cores).
// A mesma paleta está no tema do Power BI: powerbi/tema/TemaVendas.json
export interface Tokens {
  modo: 'light' | 'dark'
  surface: string
  ink: string
  ink2: string
  muted: string
  grid: string
  axis: string
  series: string[]
  deEnfase: string
}

const LIGHT: Tokens = {
  modo: 'light',
  surface: '#fcfcfb',
  ink: '#0b0b0b',
  ink2: '#52514e',
  muted: '#898781',
  grid: '#e1e0d9',
  axis: '#c3c2b7',
  series: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'],
  deEnfase: '#a3a19a',
}

const DARK: Tokens = {
  modo: 'dark',
  surface: '#1a1a19',
  ink: '#ffffff',
  ink2: '#c3c2b7',
  muted: '#898781',
  grid: '#2c2c2a',
  axis: '#383835',
  series: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
  deEnfase: '#6b6a64',
}

export type Preferencia = 'auto' | 'light' | 'dark'

const CHAVE = 'painel-vendas:tema'

function lerPreferencia(): Preferencia {
  try {
    const v = localStorage.getItem(CHAVE)
    return v === 'light' || v === 'dark' ? v : 'auto'
  } catch {
    return 'auto'
  }
}

export function useTema() {
  const [pref, setPref] = useState<Preferencia>(lerPreferencia)
  const [sistemaEscuro, setSistemaEscuro] = useState(
    () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches,
  )

  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const ouvir = (e: MediaQueryListEvent) => setSistemaEscuro(e.matches)
    mq.addEventListener('change', ouvir)
    return () => mq.removeEventListener('change', ouvir)
  }, [])

  useEffect(() => {
    const el = document.documentElement
    if (pref === 'auto') delete el.dataset.theme
    else el.dataset.theme = pref
    try {
      if (pref === 'auto') localStorage.removeItem(CHAVE)
      else localStorage.setItem(CHAVE, pref)
    } catch {
      /* armazenamento indisponível — segue sem persistir */
    }
  }, [pref])

  const escuro = pref === 'dark' || (pref === 'auto' && sistemaEscuro)
  return { tokens: escuro ? DARK : LIGHT, escuro, pref, setPref }
}
