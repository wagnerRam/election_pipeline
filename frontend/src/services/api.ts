
const API_BASE_URL = "http://127.0.0.1:8000";

export interface ResultadoEleitoral {
  uf: string;
  turno: number;
  cargo?: string;
  candidato: string;
  partido: string;
  votos: number;

  percentual_fonte: number;
  percentual_validos?: number;
  percentual_total_uf?: number;

  total_votos_uf?: number;
  votos_validos_uf?: number;

  eleicao: number | string;
  data_geracao: string | null;
  hora_geracao: string | null;
  coletado_em_utc: string | null;
  ambiente: string;
  fonte?: string;
}

export interface RespostaResultados {
  ambiente: string;
  eleicao: string;
  turno: number;
  total_registros: number;
  filtro_uf: string | null;
  resultados: ResultadoEleitoral[];
}

export interface StatusDados {
  ambiente: string;
  eleicao: string;
  turno: number;
  total_registros: number;
  total_ufs: number;
  total_votos_agregados?: number;
  data_geracao_fonte: string | null;
  hora_geracao_fonte: string | null;
  ultima_coleta_utc: string | null;
  fonte?: string | null;
}

export async function buscarResultados(
  uf?: string,
): Promise<RespostaResultados> {
  const params = new URLSearchParams();

  if (uf) {
    params.set("uf", uf);
  }

  const query = params.toString();

  const url = `${API_BASE_URL}/api/v1/resultados${
    query ? `?${query}` : ""
  }`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      `Erro ao consultar resultados: ${response.status}`,
    );
  }

  return response.json() as Promise<RespostaResultados>;
}

export async function buscarStatus(): Promise<StatusDados> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/status-dados`,
  );

  if (!response.ok) {
    throw new Error(
      `Erro ao consultar status: ${response.status}`,
    );
  }

  return response.json() as Promise<StatusDados>;
}