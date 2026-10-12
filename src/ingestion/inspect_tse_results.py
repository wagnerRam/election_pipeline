
import argparse

import requests


BASE_URL = (
    "https://resultados-sim.tse.jus.br/"
    "simulado/simulado2026/ele2026/21270/"
    "dados"
)


def fetch_results(uf: str) -> dict:
    uf = uf.lower()

    url = (
        f"{BASE_URL}/{uf}/"
        f"{uf}-c0001-e021270-u.json"
    )

    response = requests.get(
        url,
        timeout=(5, 15),
        headers={"User-Agent": "ElectionPipeline/0.1"},
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("O arquivo recebido não contém um objeto JSON.")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Inspeciona resultados eleitorais da simulação do TSE."
    )
    parser.add_argument(
        "--uf",
        default="sp",
        help="UF a consultar, por exemplo: sp",
    )
    args = parser.parse_args()

    try:
        data = fetch_results(args.uf)

        print("Eleição:", data.get("ele"))
        print("Turno:", data.get("t"))
        print("Abrangência:", data.get("tpabr"))
        print("UF:", data.get("cdabr"))
        print("Data da geração:", data.get("dg"))
        print("Hora da geração:", data.get("hg"))

        for cargo in data.get("carg", []):
            print(f"\nCargo: {cargo.get('nmn')}")

            for agrupamento in cargo.get("agr", []):
                for partido in agrupamento.get("par", []):
                    for candidato in partido.get("cand", []):
                        print(
                            f"Candidato: {candidato.get('nm')} | "
                            f"Partido: {partido.get('sg')} | "
                            f"Votos: {candidato.get('vap')} | "
                            f"Percentual: {candidato.get('pvap')}%"
                        )

    except (requests.RequestException, ValueError) as error:
        print(f"Erro ao consultar resultados para {args.uf.upper()}: {error}")


if __name__ == "__main__":
    main()
