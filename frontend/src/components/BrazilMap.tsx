import { useEffect, useState } from 'react'
import { geoMercator, geoPath } from 'd3-geo'
import type { Feature, FeatureCollection, Geometry } from 'geojson'

interface BrazilMapProps {
  selectedUF: string
  onSelectUF: (uf: string) => void
}

interface StateProperties {
  name?: string
  sigla?: string
  abbrev?: string
  UF?: string
  uf?: string
  nome?: string
}

type StateFeature = Feature<Geometry, StateProperties>

const GEOJSON_URL =
  'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'

const STATE_CODES: Record<string, string> = {
  Acre: 'AC',
  Alagoas: 'AL',
  Amapá: 'AP',
  Amazonas: 'AM',
  Bahia: 'BA',
  Ceará: 'CE',
  'Distrito Federal': 'DF',
  'Espírito Santo': 'ES',
  Goiás: 'GO',
  Maranhão: 'MA',
  'Mato Grosso': 'MT',
  'Mato Grosso do Sul': 'MS',
  'Minas Gerais': 'MG',
  Pará: 'PA',
  Paraíba: 'PB',
  Paraná: 'PR',
  Pernambuco: 'PE',
  Piauí: 'PI',
  'Rio de Janeiro': 'RJ',
  'Rio Grande do Norte': 'RN',
  'Rio Grande do Sul': 'RS',
  Rondônia: 'RO',
  Roraima: 'RR',
  'Santa Catarina': 'SC',
  'São Paulo': 'SP',
  Sergipe: 'SE',
  Tocantins: 'TO',
}

export default function BrazilMap({
  selectedUF,
  onSelectUF,
}: BrazilMapProps) {
  const [states, setStates] = useState<StateFeature[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadMap() {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(GEOJSON_URL)

        if (!response.ok) {
          throw new Error('Não foi possível carregar o mapa.')
        }

        const data = (await response.json()) as FeatureCollection<
          Geometry,
          StateProperties
        >

        if (!data.features?.length) {
          throw new Error('O arquivo do mapa não contém estados.')
        }

        if (active) {
          setStates(data.features as StateFeature[])
        }
      } catch {
        if (active) {
          setError(
            'Não foi possível carregar o mapa. Verifique sua conexão e tente novamente.',
          )
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadMap()

    return () => {
      active = false
    }
  }, [])

  const projection = geoMercator()
    .center([-54, -15])
    .scale(620)
    .translate([400, 245])

  const pathGenerator = geoPath(projection)

  if (loading) {
    return (
      <div className="map-message" role="status">
        Carregando mapa do Brasil...
      </div>
    )
  }

  if (error) {
    return (
      <div className="map-message map-error" role="alert">
        {error}
      </div>
    )
  }

  return (
    <div className="brazil-map-container">
      <svg
        className="brazil-map"
        viewBox="0 0 800 490"
        preserveAspectRatio="xMidYMid meet"
        role="group"
        aria-label="Mapa interativo dos estados brasileiros"
      >
        {states.map((state, index) => {
          const properties = state.properties
          const stateName = properties?.name ?? properties?.nome ?? ''

          const uf =
            properties?.sigla ??
            properties?.abbrev ??
            properties?.UF ??
            properties?.uf ??
            STATE_CODES[stateName] ??
            ''

          const selected = selectedUF === uf
          const d = pathGenerator(state)

          if (!d || !uf) return null

          return (
            <path
              key={uf || stateName || index}
              d={d}
              className={`map-state${selected ? ' selected' : ''}`}
              fill={selected ? '#173B70' : '#8BBCE8'}
              onClick={() => onSelectUF(selected ? '' : uf)}
              tabIndex={0}
              role="button"
              aria-pressed={selected}
              aria-label={`${stateName || uf}${selected ? ', selecionado' : ''}`}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  onSelectUF(selected ? '' : uf)
                }
              }}
            >
              <title>{stateName || uf}</title>
            </path>
          )
        })}
      </svg>

      <div className="map-legend">
        <span>
          <i className="legend-selected" />
          Estado selecionado
        </span>
        <span>
          <i className="legend-default" />
          Outros estados
        </span>
      </div>

      <p className="map-hint">
        Clique em um estado para consultar os dados ou clique novamente para
        desmarcá-lo.
      </p>
    </div>
  )
}