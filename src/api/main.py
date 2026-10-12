
import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "indicadores_por_uf.csv"

app = FastAPI(
    title="Election Pipeline API",
    description=(
        "API de consulta de resultados eleitorais. "
        "Os dados disponíveis nesta versão são de simulação."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/resultados")
def get_results(
    uf: Optional[str] = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Sigla da UF, por exemplo SP",
    ),
):
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Arquivo de resultados indisponível. Execute o pipeline primeiro.",
        )

    try:
        data = pd.read_csv(DATA_FILE)

        if uf:
            uf = uf.upper()
            data = data[data["uf"].str.upper() == uf]

        records = json.loads(
            data.to_json(orient="records", force_ascii=False)
        )

        return {
            "ambiente": "simulacao",
            "eleicao": "2026",
            "turno": 1,
            "total_registros": len(records),
            "filtro_uf": uf,
            "resultados": records,
        }

    except (OSError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler os resultados: {error}",
        ) from error


@app.get("/api/v1/status-dados")
def get_data_status():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Arquivo de resultados indisponível. Execute o pipeline primeiro.",
        )

    try:
        data = pd.read_csv(DATA_FILE)

        if data.empty:
            raise HTTPException(
                status_code=503,
                detail="O arquivo de resultados está vazio.",
            )

        return {
            "ambiente": "simulacao",
            "eleicao": "2026",
            "turno": int(data["turno"].iloc[0]),
            "total_registros": len(data),
            "total_ufs": int(data["uf"].nunique()),
            "data_geracao_fonte": data["data_geracao"].max()
            if "data_geracao" in data.columns
            else None,
            "hora_geracao_fonte": data["hora_geracao"].max()
            if "hora_geracao" in data.columns
            else None,
            "ultima_coleta_utc": data["coletado_em_utc"].max()
            if "coletado_em_utc" in data.columns
            else None,
        }

    except (OSError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar metadados: {error}",
        ) from error
