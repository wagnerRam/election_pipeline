from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import requests

URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "votacao_secao/votacao_secao_2026_BR.zip"
)


def main():
    print("Baixando arquivo oficial do TSE...")

    response = requests.get(
        URL,
        timeout=(10, 180),
        headers={"User-Agent": "ElectionPipeline/0.2"},
    )
    response.raise_for_status()

    totals = {}
    candidates = set()
    total_rows = 0

    with ZipFile(BytesIO(response.content)) as archive:
        csv_name = next(
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
        )

        with archive.open(csv_name) as csv_file:
            for chunk in pd.read_csv(
                csv_file,
                sep=";",
                encoding="latin-1",
                dtype=str,
                chunksize=200_000,
            ):
                chunk.columns = (
                    chunk.columns.str.strip().str.strip('"')
                )

                chunk["NR_TURNO"] = chunk["NR_TURNO"].astype(str).str.strip()
                chunk["DS_CARGO"] = chunk["DS_CARGO"].astype(str).str.strip()
                chunk["QT_VOTOS"] = pd.to_numeric(
                    chunk["QT_VOTOS"], errors="coerce"
                ).fillna(0)

                total_rows += len(chunk)

                grouped = chunk.groupby(
                    ["NR_TURNO", "DS_CARGO"],
                    dropna=False,
                )["QT_VOTOS"].sum()

                for key, value in grouped.items():
                    totals[key] = totals.get(key, 0) + int(value)

                president = chunk[
                    chunk["DS_CARGO"].str.casefold() == "presidente"
                ]

                candidates.update(
                    president["NM_VOTAVEL"].dropna().unique()
                )

    print(f"\nLinhas processadas: {total_rows:,}")
    print("\nVotos somados por turno e cargo:")

    for (turno, cargo), votos in sorted(totals.items()):
        print(f"Turno {turno} | {cargo}: {votos:,} votos")

    print("\nOpções de votação encontradas para Presidente:")
    for candidate in sorted(candidates):
        print(f"- {candidate}")


if __name__ == "__main__":
    main()