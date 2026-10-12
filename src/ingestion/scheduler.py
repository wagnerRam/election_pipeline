
import logging
import time

from src.ingestion.run_pipeline import main


INTERVAL_SECONDS = 15 * 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def run_scheduler() -> None:
    """Executa o pipeline em intervalos de 15 minutos."""

    logger.info(
        "Agendador iniciado. Intervalo: 15 minutos."
    )

    while True:
        inicio = time.monotonic()

        try:
            logger.info("Iniciando execução agendada.")
            main()
            logger.info("Execução concluída com sucesso.")

        except Exception:
            logger.exception(
                "Falha no pipeline. A próxima tentativa será agendada."
            )

        decorrido = time.monotonic() - inicio
        espera = max(0, INTERVAL_SECONDS - decorrido)

        logger.info(
            "Próxima execução em %.1f minutos.",
            espera / 60,
        )

        time.sleep(espera)


if __name__ == "__main__":
    run_scheduler()