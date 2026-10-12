
import requests

BASE_URL = "https://resultados-sim.tse.jus.br"
CONFIG_URL = (
    f"{BASE_URL}/simulado/simulado2026/"
    "comum/config/ele-c.json"
)


def fetch_election_config() -> dict:
    response = requests.get(
        CONFIG_URL,
        timeout=(5, 15),
        headers={"User-Agent": "ElectionPipeline/0.1"},
    )
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("A configuração recebida não é um objeto JSON.")

    return payload


def find_presidential_elections(config: dict) -> list[dict]:
    elections_found = []

    for cycle in config.get("pl", []):
        for election in cycle.get("e", []):
            for region in election.get("abr", []):
                for position in region.get("cp", []):
                    if position.get("ds", "").strip().casefold() == "presidente":
                        elections_found.append({
                            "cycle": cycle.get("c"),
                            "election_code": election.get("cd"),
                            "second_round_code": election.get("cdt2") or None,
                            "election_name": election.get("nm"),
                            "region": region.get("cd"),
                            "office_code": position.get("cd"),
                            "environment": "simulation",
                        })

    return elections_found


def main():
    print("Consultando configuração eleitoral do TSE (SIMULAÇÃO)...")

    try:
        config = fetch_election_config()
        elections = find_presidential_elections(config)

        if not elections:
            print("Nenhuma eleição presidencial encontrada.")
            return

        for election in elections:
            print("\nEleição presidencial identificada:")
            for key, value in election.items():
                print(f"{key}: {value}")

    except (requests.RequestException, ValueError) as error:
        print(f"Erro ao processar a configuração: {error}")


if __name__ == "__main__":
    main()
