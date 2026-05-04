import { SHMETRO_LINE_COLORS } from '@kyuri-metro/shmetro-palette'

export type LineIdBlockProps = {
  background?: string
  fontFamily?: string
  foreground?: string
  height?: number
  lineNumber: string | number
}

type TextLayout = {
  x: number
  y: number
  fontSize: number
  letterSpacing?: number
  transform?: string
}

type BadgeLayout = {
  width: number
  height: number
  text: string
  textLayout: TextLayout
}

const FALLBACK_BACKGROUND = '#666666'
const FALLBACK_FOREGROUND = '#000000'
export const DEFAULT_LINE_ID_BLOCK_FONT_FAMILY = 'Arial, Helvetica, sans-serif'

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function parseLineNumber(lineNumber: string | number) {
  const lineString = String(lineNumber).trim()

  if (!/^\d{1,2}$/.test(lineString)) {
    return null
  }

  const lineId = Number(lineString)

  if (!Number.isInteger(lineId) || lineId < 0 || lineId > 99) {
    return null
  }

  return {
    lineId,
    lineString,
  }
}

function getBadgePalette(lineNumber: string | number, foreground?: string, background?: string) {
  const parsed = parseLineNumber(lineNumber)
  const metroPalette = parsed ? SHMETRO_LINE_COLORS[parsed.lineId] : undefined

  return {
    background: background ?? metroPalette?.background ?? FALLBACK_BACKGROUND,
    foreground: foreground ?? metroPalette?.foreground ?? FALLBACK_FOREGROUND,
  }
}

function scaleLayout(layout: BadgeLayout, nextHeight: number): BadgeLayout {
  if (layout.height === nextHeight) {
    return layout
  }

  const scale = nextHeight / layout.height

  return {
    width: layout.width * scale,
    height: nextHeight,
    text: layout.text,
    textLayout: {
      x: layout.textLayout.x * scale,
      y: layout.textLayout.y * scale,
      fontSize: layout.textLayout.fontSize * scale,
      letterSpacing:
        layout.textLayout.letterSpacing === undefined ? undefined : layout.textLayout.letterSpacing * scale,
      transform: layout.textLayout.transform,
    },
  }
}

function getBaseLayout(lineId: number, lineString: string): BadgeLayout {
  const layoutMap = {
    single_1: {
      width: 86,
      textLayout: { x: 7.5, y: 88.8, fontSize: 104 },
    },
    single_4: {
      width: 86,
      textLayout: { x: 14.9, y: 88.8, fontSize: 104 },
    },
    double_11: {
      width: 105,
      textLayout: { x: 3.6, y: 88.6, fontSize: 104, letterSpacing: -10.2 },
    },
    double_1x: {
      width: 105,
      textLayout: { x: -3.3, y: 88.6, fontSize: 104, letterSpacing: -14 },
    },
    double_21: {
      width: 105,
      textLayout: { x: 7.4, y: 88.6, fontSize: 104, letterSpacing: -9.5 },
    },
    double_2x: {
      width: 105,
      textLayout: { x: 0.7, y: 86.8, fontSize: 102, letterSpacing: -5.2, transform: 'scale(.98 1)' },
    },
  } as const

  if (lineString === '1') {
    return { width: layoutMap.single_1.width, height: 100, text: lineString, textLayout: layoutMap.single_1.textLayout }
  }

  if (lineId >= 2 && lineId <= 9) {
    return { width: layoutMap.single_4.width, height: 100, text: lineString, textLayout: layoutMap.single_4.textLayout }
  }

  if (lineString === '11') {
    return { width: layoutMap.double_11.width, height: 100, text: lineString, textLayout: layoutMap.double_11.textLayout }
  }

  if (lineId >= 10 && lineId <= 19) {
    return { width: layoutMap.double_1x.width, height: 100, text: lineString, textLayout: layoutMap.double_1x.textLayout }
  }

  if (lineString === '21') {
    return { width: layoutMap.double_21.width, height: 100, text: lineString, textLayout: layoutMap.double_21.textLayout }
  }

  return { width: layoutMap.double_2x.width, height: 100, text: lineString, textLayout: layoutMap.double_2x.textLayout }
}

export function getLineIdBlockWidth(lineNumber: string | number, height = 100) {
  const parsed = parseLineNumber(lineNumber)

  if (!parsed) {
    return null
  }

  return scaleLayout(getBaseLayout(parsed.lineId, parsed.lineString), height).width
}

function formatLetterSpacing(letterSpacing?: number) {
  if (letterSpacing === undefined) {
    return ''
  }

  return ` letter-spacing="${letterSpacing}px"`
}

function formatTransform(transform?: string) {
  if (!transform) {
    return ''
  }

  return ` transform="${transform}"`
}

export function generateLineIdBlock2020Svg({
  background,
  fontFamily = DEFAULT_LINE_ID_BLOCK_FONT_FAMILY,
  foreground,
  height = 100,
  lineNumber,
}: LineIdBlockProps) {
  const parsed = parseLineNumber(lineNumber)

  if (!parsed) {
    return ''
  }

  const palette = getBadgePalette(lineNumber, foreground, background)
  const layout = scaleLayout(getBaseLayout(parsed.lineId, parsed.lineString), height)

  return `<svg width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="${layout.width}" height="${layout.height}" fill="${palette.background}"/><text x="${layout.textLayout.x}" y="${layout.textLayout.y}" fill="${palette.foreground}" font-family="${escapeXml(fontFamily)}" font-size="${layout.textLayout.fontSize}px"${formatLetterSpacing(layout.textLayout.letterSpacing)}${formatTransform(layout.textLayout.transform)}>${layout.text}</text></svg>`
}