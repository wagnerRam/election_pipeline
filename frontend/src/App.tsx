import { useEffect, useState } from 'react'

import {
  Activity,
  BarChart3,
  CheckCircle2,
  Database,
  MapPin,
  RefreshCw,
  Users,
  Vote,
} from 'lucide-react'

import {
  buscarResultados,
  buscarStatus,
  type ResultadoEleitoral,
  type StatusDados,
} from './services/api'

import './App.css'
import BrazilMap from './components/BrazilMap'

const VOTOS_NAO_VALIDOS = new Set(['VOTO BRANCO', 'VOTO NULO'])

const CARGOS = [
  { value: 'PRESIDENTE', label: 'Presidente' },
  { value: 'GOVERNADOR', label: 'Governador' },
  { value: 'SENADOR', label: 'Senador' },
  { value: 'DEPUTADO_FEDERAL', label: 'Deputado Federal' },
  { value: 'DEPUTADO_ESTADUAL', label: 'Deputado Estadual/Distrital' },
]

function App() {
  const [resultados, setResultados] = useState<ResultadoEleitoral[]>([])
  const [status, setStatus] = useState<StatusDados | null>(null)

  const [uf, setUf] = useState('')
  const [cargo, setCargo] = useState('PRESIDENTE')
  const [turno, setTurno] = useState('1')

  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [atualizacao, setAtualizacao] = useState(0)
  const [mostrarDetalhamento, setMostrarDetalhamento] = useState(false)

  const filtroDisponivel =
    cargo === 'PRESIDENTE' && turno === '1'

  useEffect(() => {
    let ativo = true

    async function carregarDados() {
      setCarregando(true)
      setErro('')

      try {
        const [respostaResultados, respostaStatus] = await Promise.all([
          buscarResultados(uf || undefined),
          buscarStatus(),
        ])

        if (!ativo) return

        setResultados(respostaResultados.resultados)
        setStatus(respostaStatus)
      } catch (error) {
        if (!ativo) return

        setErro(
          error instanceof Error
            ? error.message
            : 'Não foi possível carregar os dados.',
        )
      } finally {
        if (ativo) setCarregando(false)
      }
    }

    void carregarDados()

    return () => {
      ativo = false
    }
  }, [uf, atualizacao])

  const formatarNumero = (valor: number) =>
    new Intl.NumberFormat('pt-BR').format(valor)

  const formatarPercentual = (valor: number) =>
    `${valor.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}%`

  const formatarData = (data: string | null | undefined) => {
    if (!data) return 'Não informada'

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(data)) return data

    const dataValida = new Date(data)

    if (Number.isNaN(dataValida.getTime())) return data

    return dataValida.toLocaleString('pt-BR')
  }

  const normalizarNome = (nome: string) => nome.trim().toUpperCase()

  const resultadosValidos = resultados.filter(
    (item) => !VOTOS_NAO_VALIDOS.has(normalizarNome(item.candidato)),
  )

  const totalVotos = resultados.reduce(
    (total, item) => total + Number(item.votos || 0),
    0,
  )

  const totalVotosValidos = resultadosValidos.reduce(
    (total, item) => total + Number(item.votos || 0),
    0,
  )

  const mapaCandidatos = resultadosValidos.reduce(
    (mapa, item) => {
      const nome = item.candidato
      const atual = mapa.get(nome)

      if (atual) {
        atual.totalVotos += Number(item.votos || 0)

        if (!atual.partido && item.partido) {
          atual.partido = item.partido
        }
      } else {
        mapa.set(nome, {
          candidato: nome,
          partido: item.partido || '',
          totalVotos: Number(item.votos || 0),
        })
      }

      return mapa
    },
    new Map<
      string,
      {
        candidato: string
        partido: string
        totalVotos: number
      }
    >(),
  )

  const votosPorCandidato = Array.from(mapaCandidatos.values())
    .map((candidato) => ({
      ...candidato,
      percentual:
        totalVotosValidos > 0
          ? (candidato.totalVotos / totalVotosValidos) * 100
          : 0,
    }))
    .sort((a, b) => b.totalVotos - a.totalVotos)

  const estados = Array.from(
    new Set(resultados.map((item) => item.uf)),
  ).sort()

  const fonte = status?.fonte ?? 'TSE - votação por seção eleitoral'

  const cargoSelecionado = CARGOS.find(
    (item) => item.value === cargo,
  )

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Vote size={25} />
          </div>

          <div>
            <h1>
              Eleição <span>2026</span>
            </h1>
            <p>MONITORAMENTO ELEITORAL</p>
          </div>
        </div>

        <div className="header-status">
          <span className="status-dot" />
          <span>
            {erro ? 'Falha na conexão' : 'API conectada'}
          </span>
        </div>
      </header>

      <section className="page-heading">
        <div>
          <span className="eyebrow">PAINEL DE CONTROLE</span>
          <h2>Visão geral dos resultados</h2>
          <p>
            Acompanhe os dados eleitorais processados pelo pipeline.
          </p>
        </div>

        <div className="dashboard-filters">
          <label className="filter">
            <Vote size={18} />

            <select
              value={cargo}
              onChange={(event) => {
                setCargo(event.target.value)
                setMostrarDetalhamento(false)
              }}
              aria-label="Selecionar cargo"
            >
              {CARGOS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="filter">
            <Activity size={18} />

            <select
              value={turno}
              onChange={(event) => {
                setTurno(event.target.value)
                setMostrarDetalhamento(false)
              }}
              aria-label="Selecionar turno"
            >
              <option value="1">1º turno</option>
              <option value="2">2º turno</option>
            </select>
          </label>

          <label className="filter">
            <MapPin size={18} />

            <select
              value={uf}
              onChange={(event) => setUf(event.target.value)}
              aria-label="Selecionar estado"
            >
              <option value="">Todos os estados</option>

              {estados.map((estado) => (
                <option key={estado} value={estado}>
                  {estado}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {erro && (
        <section className="error-message">
          <strong>Não foi possível carregar os dados.</strong>
          <p>{erro}</p>
          <p>
            Confira se a API Python está em execução na porta 8000.
          </p>

          <button
            type="button"
            onClick={() => setAtualizacao((valor) => valor + 1)}
          >
            <RefreshCw size={16} />
            Tentar novamente
          </button>
        </section>
      )}

      {filtroDisponivel ? (
        <>
          <section className="simulation-alert">
            <Activity size={21} />

            <div>
              <strong>Fonte dos dados: {fonte}</strong>
              <p>
                Eleição {status?.eleicao ?? '2026'} — 1º turno.
                Confira a data de geração da fonte para avaliar a
                atualização dos dados.
              </p>
            </div>
          </section>

          <section className="metrics-grid">
            <article className="metric-card">
              <div className="metric-top">
                <span>Total de votos registrados</span>
                <div className="metric-icon purple">
                  <Vote size={21} />
                </div>
              </div>

              <strong>
                {carregando ? '...' : formatarNumero(totalVotos)}
              </strong>
              <p>Inclui votos válidos, brancos e nulos</p>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Candidatos</span>
                <div className="metric-icon blue">
                  <Users size={21} />
                </div>
              </div>

              <strong>
                {carregando ? '...' : votosPorCandidato.length}
              </strong>
              <p>Sem contabilizar brancos e nulos</p>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Estados consultados</span>
                <div className="metric-icon green">
                  <MapPin size={21} />
                </div>
              </div>

              <strong>
                {carregando ? '...' : estados.length}
              </strong>
              <p>
                {uf
                  ? `Estado selecionado: ${uf}`
                  : 'Estados na resposta atual'}
              </p>
            </article>

            <article className="metric-card">
              <div className="metric-top">
                <span>Registros processados</span>
                <div className="metric-icon orange">
                  <Database size={21} />
                </div>
              </div>

              <strong>
                {carregando
                  ? '...'
                  : formatarNumero(status?.total_registros ?? 0)}
              </strong>
              <p>Total da base informado pela API</p>
            </article>
          </section>

          <section className="panel map-panel">
            <div className="panel-heading">
              <div>
                <h3>
                  <MapPin size={20} />
                  Mapa eleitoral do Brasil
                </h3>
                <p>
                  Selecione um estado para filtrar os resultados.
                </p>
              </div>

              {uf && (
                <button
                  type="button"
                  className="map-clear-button"
                  onClick={() => setUf('')}
                >
                  Limpar filtro · {uf}
                </button>
              )}
            </div>

            <BrazilMap
              selectedUF={uf}
              onSelectUF={setUf}
            />
          </section>

          <section className="content-grid">
            <article className="panel ranking-panel">
              <div className="panel-heading">
                <div>
                  <h3>
                    <BarChart3 size={20} />
                    Resultados por candidato
                  </h3>
                  <p>
                    Votos e percentual sobre os votos válidos,
                    em ordem alfabética.
                  </p>
                </div>
              </div>

              {carregando ? (
                <p className="empty-state">
                  Carregando resultados...
                </p>
              ) : votosPorCandidato.length === 0 ? (
                <p className="empty-state">
                  Nenhum resultado encontrado.
                </p>
              ) : (
                <div className="candidate-cards">
                  {votosPorCandidato.map((candidato) => {
                    const iniciais = candidato.candidato
                      .split(/\s+/)
                      .filter(Boolean)
                      .slice(0, 2)
                      .map((parte) => parte[0])
                      .join('')
                      .toUpperCase()

                    return (
                      <article
                        className="candidate-card"
                        key={candidato.candidato}
                      >
                        <div className="candidate-card-header">
                          <div
                            className="candidate-avatar"
                            aria-hidden="true"
                          >
                            {iniciais}
                          </div>

                          <div className="candidate-card-name">
                            <h4>{candidato.candidato}</h4>
                            <p>
                              {candidato.partido ||
                                'Partido não disponível na base'}
                            </p>
                          </div>
                        </div>

                        <div className="candidate-card-divider" />

                        <div className="candidate-card-stats">
                          <div>
                            <span>Votos</span>
                            <strong>
                              {formatarNumero(candidato.totalVotos)}
                            </strong>
                          </div>

                          <div className="candidate-card-percent">
                            <span>Votos válidos</span>
                            <strong>
                              {formatarPercentual(
                                candidato.percentual,
                              )}
                            </strong>
                          </div>
                        </div>

                        <div
                          className="candidate-card-track"
                          role="progressbar"
                          aria-label={`Percentual de votos válidos de ${candidato.candidato}`}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={Number(
                            candidato.percentual.toFixed(2),
                          )}
                        >
                          <div
                            className="candidate-card-fill"
                            style={{
                              width: `${Math.min(
                                Math.max(candidato.percentual, 0),
                                100,
                              )}%`,
                            }}
                          />
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
            </article>

            <article className="panel status-panel">
              <div className="panel-heading">
                <div>
                  <h3>
                    <Activity size={20} />
                    Status da coleta
                  </h3>
                  <p>Informações da última atualização</p>
                </div>
              </div>

              <div className="collection-status">
                <CheckCircle2 size={20} />

                <div>
                  <strong>
                    {erro
                      ? 'Verifique a conexão'
                      : 'Dados carregados'}
                  </strong>
                  <span>
                    {erro
                      ? 'Falha ao consultar API'
                      : 'Metadados retornados pela API'}
                  </span>
                </div>
              </div>

              <div className="detail-row">
                <span>Ambiente</span>
                <strong>{status?.ambiente ?? '—'}</strong>
              </div>

              <div className="detail-row">
                <span>Eleição</span>
                <strong>{status?.eleicao ?? '2026'}</strong>
              </div>

              <div className="detail-row">
                <span>Turno</span>
                <strong>1º</strong>
              </div>

              <div className="detail-row">
                <span>UFs na base completa</span>
                <strong>{status?.total_ufs ?? 0}</strong>
              </div>

              <div className="detail-row">
                <span>Última coleta (UTC)</span>
                <strong className="date-value">
                  {formatarData(status?.ultima_coleta_utc)}
                </strong>
              </div>

              <div className="detail-row">
                <span>Data de geração na fonte</span>
                <strong>
                  {status?.data_geracao_fonte ?? 'Não informada'}
                </strong>
              </div>

              <div className="detail-row">
                <span>Horário de geração na fonte</span>
                <strong>
                  {status?.hora_geracao_fonte ?? 'Não informado'}
                </strong>
              </div>

              <button
                type="button"
                className="refresh-button"
                onClick={() =>
                  setAtualizacao((valor) => valor + 1)
                }
                disabled={carregando}
              >
                <RefreshCw size={16} />
                {carregando
                  ? 'Atualizando...'
                  : 'Atualizar painel'}
              </button>
            </article>
          </section>

          <section className="panel table-panel">
            <div className="panel-heading">
              <div>
                <h3>Detalhamento por estado</h3>
                <p>
                  Consulte os registros completos quando precisar
                  de mais detalhes.
                </p>
              </div>

              <div className="table-actions">
                <span className="record-count">
                  {formatarNumero(resultados.length)} registros
                </span>

                <button
                  type="button"
                  className="table-toggle-button"
                  onClick={() =>
                    setMostrarDetalhamento((mostrar) => !mostrar)
                  }
                  aria-expanded={mostrarDetalhamento}
                >
                  {mostrarDetalhamento
                    ? 'Ocultar registros'
                    : 'Ver todos os registros'}
                </button>
              </div>
            </div>

            {mostrarDetalhamento && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Estado</th>
                      <th>Candidato / opção</th>
                      <th>Partido</th>
                      <th>Votos</th>
                      <th>% dos votos válidos</th>
                    </tr>
                  </thead>

                  <tbody>
                    {resultados.map((item, index) => (
                      <tr
                        key={`${item.uf}-${item.candidato}-${index}`}
                      >
                        <td>
                          <span className="uf-badge">
                            {item.uf}
                          </span>
                        </td>

                        <td className="table-candidate">
                          {item.candidato}
                        </td>

                        <td>{item.partido || '—'}</td>

                        <td>
                          {formatarNumero(Number(item.votos || 0))}
                        </td>

                        <td>
                          {VOTOS_NAO_VALIDOS.has(
                            normalizarNome(item.candidato),
                          )
                            ? '—'
                            : formatarPercentual(
                              Number(
                                item.percentual_validos ??
                                item.percentual_fonte ??
                                0,
                              ),
                            )}
                        </td>
                      </tr>
                    ))}

                    {!carregando && resultados.length === 0 && (
                      <tr>
                        <td colSpan={5} className="empty-state">
                          Nenhum registro para exibir.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : (
        <section className="panel unavailable-panel">
          <div className="unavailable-icon">
            <Database size={24} />
          </div>

          <h3>Dados ainda não integrados</h3>

          <p>
            A API atual contém resultados presidenciais do primeiro turno.
            Não há dados integrados para{' '}
            {cargoSelecionado?.label ?? 'o cargo selecionado'} no{' '}
            {turno}º turno.
          </p>

          <p>
            Para exibir os números corretos, precisamos integrar a coleta
            desse cargo e turno no pipeline e na API.
          </p>

          <button
            type="button"
            className="refresh-button"
            onClick={() => {
              setCargo('PRESIDENTE')
              setTurno('1')
              setMostrarDetalhamento(false)
            }}
          >
            Voltar para Presidente · 1º turno
          </button>
        </section>
      )}

      <footer className="footer">
        <span>Eleição 2026 · Projeto de engenharia de dados</span>
        <span>{fonte}</span>
      </footer>
    </main>
  )
}

export default App