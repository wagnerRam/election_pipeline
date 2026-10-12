import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "indicadores_oficiais_por_uf.csv"
)

app = FastAPI(
    title="Election Pipeline API",
    description=(
        "API de consulta de resultados eleitorais de 2026, "
        "com dados agregados a partir do arquivo publicado pelo TSE."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def carregar_dados() -> pd.DataFrame:
    """Carrega e valida o arquivo agregado de resultados eleitorais."""

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Arquivo de resultados indisponível. "
                "Execute o pipeline de agregação oficial primeiro."
            ),
        )

    try:
        data = pd.read_csv(DATA_FILE)

        if data.empty:
            raise HTTPException(
                status_code=503,
                detail="O arquivo de resultados está vazio.",
            )

        colunas_obrigatorias = {
            "uf",
            "turno",
            "eleicao",
            "candidato",
            "votos",
            "ambiente",
            "fonte",
        }

        colunas_ausentes = colunas_obrigatorias - set(data.columns)

        if colunas_ausentes:
            raise HTTPException(
                status_code=500,
                detail=(
                    "O arquivo não contém todas as colunas necessárias: "
                    + ", ".join(sorted(colunas_ausentes))
                ),
            )

        # Compatibilidade com o CSV da versão anterior.
        if "cargo" not in data.columns:
            data["cargo"] = "PRESIDENTE"

        if "cargo_descricao" not in data.columns:
            data["cargo_descricao"] = data["cargo"]

        if "id_candidato" not in data.columns:
            data["id_candidato"] = ""

        if "partido" not in data.columns:
            data["partido"] = ""

        data["uf"] = data["uf"].astype(str).str.strip().str.upper()
        data["cargo"] = (
            data["cargo"].astype(str).str.strip().str.upper()
        )
        data["turno"] = pd.to_numeric(data["turno"], errors="coerce")
        data["votos"] = pd.to_numeric(
            data["votos"], errors="coerce"
        ).fillna(0)

        if "percentual_validos" in data.columns:
            data["percentual_fonte"] = data["percentual_validos"]

        return data

    except HTTPException:
        raise
    except (OSError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler os resultados: {error}",
        ) from error


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "arquivo_disponivel": DATA_FILE.exists(),
    }


@app.get("/api/v1/resultados")
def get_results(
    uf: Optional[str] = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Sigla da UF, por exemplo SP",
    ),
    cargo: Optional[str] = Query(
        default=None,
        min_length=3,
        description="Cargo normalizado, por exemplo PRESIDENTE",
    ),
    turno: Optional[int] = Query(
        default=None,
        ge=1,
        le=2,
        description="Turno eleitoral: 1 ou 2",
    ),
):
    data = carregar_dados()

    if uf:
        uf = uf.strip().upper()
        data = data[data["uf"] == uf]

    if cargo:
        cargo = cargo.strip().upper()
        data = data[data["cargo"] == cargo]

    if turno is not None:
        data = data[data["turno"] == turno]

    data = data.sort_values(
        by="votos",
        ascending=False,
    )

    registros = json.loads(
        data.to_json(orient="records", force_ascii=False)
    )

    turnos_encontrados = sorted(
        int(valor)
        for valor in data["turno"].dropna().unique()
    )

    return {
        "ambiente": "oficial",
        "eleicao": "2026",
        "turno": turno if turno is not None else (
            turnos_encontrados[0] if len(turnos_encontrados) == 1 else None
        ),
        "filtro_uf": uf,
        "filtro_cargo": cargo,
        "filtro_turno": turno,
        "total_registros": len(registros),
        "total_ufs": int(data["uf"].nunique()),
        "cargos_disponiveis": sorted(data["cargo"].dropna().unique().tolist()),
        "turnos_disponiveis": turnos_encontrados,
        "resultados": registros,
    }


@app.get("/api/v1/status-dados")
def get_data_status():
    data = carregar_dados()

    return {
        "ambiente": "oficial",
        "eleicao": "2026",
        "total_registros": len(data),
        "total_ufs": int(data["uf"].nunique()),
        "total_cargos": int(data["cargo"].nunique()),
        "cargos_disponiveis": sorted(
            data["cargo"].dropna().unique().tolist()
        ),
        "turnos_disponiveis": sorted(
            int(valor)
            for valor in data["turno"].dropna().unique()
        ),
        "total_votos_agregados": int(data["votos"].sum()),
        "data_geracao_fonte": (
            data["data_geracao"].max()
            if "data_geracao" in data.columns
            else None
        ),
        "hora_geracao_fonte": (
            data["hora_geracao"].max()
            if "hora_geracao" in data.columns
            else None
        ),
        "ultima_coleta_utc": (
            data["coletado_em_utc"].max()
            if "coletado_em_utc" in data.columns
            else None
        ),
        "fonte": (
            data["fonte"].iloc[0]
            if "fonte" in data.columns and not data.empty
            else None
        ),
    }