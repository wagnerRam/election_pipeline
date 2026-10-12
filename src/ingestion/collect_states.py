
import csv
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.ingestion.inspect_tse_results import fetch_results


UF_LIST = [
    "ac", "al", "ap", "am", "ba", "ce", "df",
    "es", "go", "ma", "mt", "ms", "mg", "pa",
    "pb", "pr", "pe", "pi", "rj", "rn", "rs",
    "ro", "rr", "sc", "sp", "se", "to",
]

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "resultados_por_uf.csv"


def extract_candidates(data: dict, uf: str) -> list[dict]:
    rows = []

    for cargo in data.get("carg", []):
        for agrupamento in cargo.get("agr", []):
            for partido in agrupamento.get("par", []):
                for candidato in partido.get("cand", []):
                    rows.append({
                        "uf": uf.upper(),
                        "eleicao": data.get("ele"),
                        "turno": data.get("t"),
                        "cargo": cargo.get("nmn"),
                        "candidato": candidato.get("nm"),
                        "partido": partido.get("sg"),
                        "votos": candidato.get("vap"),
                        "percentual": candidato.get("pvap"),
                        "data_geracao": data.get("dg"),
                        "hora_geracao": data.get("hg"),
                        "coletado_em_utc": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "ambiente": "simulacao",
                    })

    return rows


def main():
    all_rows = []
    failed = []

    for uf in UF_LIST:
        try:
            data = fetch_results(uf)

            if data.get("tpabr") != "uf":
                raise ValueError("Abrangência inesperada no arquivo.")

            if data.get("cdabr", "").lower() != uf:
                raise ValueError("A UF retornada não corresponde à solicitada.")

            rows = extract_candidates(data, uf)
            all_rows.extend(rows)

            print(f"OK | {uf.upper()} | {len(rows)} registros")

        except (requests.RequestException, ValueError) as error:
            print(f"ERRO | {uf.upper()} | {error}")
            failed.append(uf.upper())

    if all_rows:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        fieldnames = list(all_rows[0].keys())

        with OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"\nCSV salvo em: {OUTPUT_FILE}")
        print(f"Total de registros: {len(all_rows)}")

    print(f"UFs com falha: {len(failed)}")
    if failed:
        print(", ".join(failed))


if __name__ == "__main__":
    main()
