from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path

import pandas as pd
import requests

from src.ingestion.aggregate_results import aggregate_results
from src.ingestion.collect_states import UF_LIST, extract_candidates
from src.ingestion.inspect_tse_results import fetch_results
from src.ingestion.transform_results import transform_results


OUTPUT_DIR = Path("data/processed")
RAW_FILE = OUTPUT_DIR / "resultados_por_uf.csv"
AGGREGATED_FILE = OUTPUT_DIR / "indicadores_por_uf.csv"

RAW_TEMP_FILE = OUTPUT_DIR / "resultados_por_uf.tmp.csv"
AGGREGATED_TEMP_FILE = OUTPUT_DIR / "indicadores_por_uf.tmp.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def collect_state(uf: str) -> list[dict]:
    """Coleta e valida os resultados de uma UF."""

    data = fetch_results(uf)

    if data.get("tpabr") != "uf":
        raise ValueError(
            f"Resposta inesperada para {uf.upper()}: "
            "abrangência diferente de UF."
        )

    if data.get("cdabr", "").lower() != uf.lower():
        raise ValueError(
            f"A UF retornada não corresponde a {uf.upper()}."
        )

    state_rows = extract_candidates(data, uf)

    logger.info(
        "%s: %d registros coletados",
        uf.upper(),
        len(state_rows),
    )

    return state_rows


def collect_all_states() -> pd.DataFrame:
    """Coleta as UFs com concorrência limitada."""

    rows = []
    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(collect_state, uf): uf
            for uf in UF_LIST
        }

        for future in as_completed(futures):
            uf = futures[future]

            try:
                rows.extend(future.result())
            except Exception:
                logger.exception(
                    "Falha ao coletar a UF %s.",
                    uf.upper(),
                )
                raise

    if not rows:
        raise ValueError("A coleta não retornou registros.")

    return pd.DataFrame(rows)


def save_csvs_safely(
    raw_data: pd.DataFrame,
    aggregated: pd.DataFrame,
) -> None:
    """Prepara os CSVs antes de substituir os arquivos atuais."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        raw_data.to_csv(
            RAW_TEMP_FILE,
            index=False,
            encoding="utf-8-sig",
        )

        aggregated.to_csv(
            AGGREGATED_TEMP_FILE,
            index=False,
            encoding="utf-8-sig",
        )

        # Substituições individuais: não são uma transação conjunta.
        RAW_TEMP_FILE.replace(RAW_FILE)
        AGGREGATED_TEMP_FILE.replace(AGGREGATED_FILE)

    finally:
        RAW_TEMP_FILE.unlink(missing_ok=True)
        AGGREGATED_TEMP_FILE.unlink(missing_ok=True)


def main() -> None:
    """Executa o pipeline de coleta e processamento eleitoral."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Iniciando pipeline eleitoral de simulação.")

    try:
        # 1. Coleta os dados das UFs.
        raw_data = collect_all_states()

        # 2. Transforma e valida os dados.
        transformed = transform_results(raw_data)

        # 3. Consolida os resultados.
        aggregated = aggregate_results(transformed)

        if aggregated.empty:
            raise ValueError(
                "A agregação não retornou resultados."
            )

        # 4. Atualiza os arquivos somente após o processamento.
        save_csvs_safely(raw_data, aggregated)

        logger.info("CSV bruto salvo: %s", RAW_FILE)
        logger.info("CSV consolidado salvo: %s", AGGREGATED_FILE)

        logger.info(
            "Pipeline concluído: %d registros brutos, "
            "%d registros consolidados e %d UFs.",
            len(raw_data),
            len(aggregated),
            aggregated["uf"].nunique(),
        )

    except (requests.RequestException, ValueError, KeyError):
        logger.exception("Pipeline interrompido.")
        raise


if __name__ == "__main__":
    main()