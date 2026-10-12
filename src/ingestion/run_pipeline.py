
import logging
from pathlib import Path

import pandas as pd
import requests

from src.ingestion.inspect_tse_results import fetch_results
from src.ingestion.transform_results import transform_results
from src.ingestion.aggregate_results import aggregate_results
from src.ingestion.collect_states import UF_LIST


OUTPUT_DIR = Path("data/processed")
RAW_FILE = OUTPUT_DIR / "resultados_por_uf.csv"
AGGREGATED_FILE = OUTPUT_DIR / "indicadores_por_uf.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def collect_all_states() -> pd.DataFrame:
    rows = []

    for uf in UF_LIST:
        data = fetch_results(uf)

        if data.get("tpabr") != "uf":
            raise ValueError(
                f"Resposta inesperada para {uf.upper()}: "
                "abrangência diferente de UF."
            )

        if data.get("cdabr", "").lower() != uf:
            raise ValueError(
                f"A UF retornada não corresponde a {uf.upper()}."
            )

        from src.ingestion.collect_states import extract_candidates

        state_rows = extract_candidates(data, uf)
        rows.extend(state_rows)

        logger.info(
            "%s: %d registros coletados",
            uf.upper(),
            len(state_rows),
        )

    if not rows:
        raise ValueError("A coleta não retornou registros.")

    return pd.DataFrame(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Iniciando pipeline eleitoral de simulação.")

    try:
        raw_data = collect_all_states()
        raw_data.to_csv(
            RAW_FILE,
            index=False,
            encoding="utf-8-sig",
        )
        logger.info("CSV bruto salvo: %s", RAW_FILE)

        transformed = transform_results(raw_data)
        aggregated = aggregate_results(transformed)

        aggregated.to_csv(
            AGGREGATED_FILE,
            index=False,
            encoding="utf-8-sig",
        )
        logger.info("CSV consolidado salvo: %s", AGGREGATED_FILE)

        logger.info(
            "Pipeline concluído: %d registros brutos, "
            "%d registros consolidados e %d UFs.",
            len(raw_data),
            len(aggregated),
            aggregated["uf"].nunique(),
        )

    except (requests.RequestException, ValueError, KeyError) as error:
        logger.error("Pipeline interrompido: %s", error)
        raise


if __name__ == "__main__":
    main()
