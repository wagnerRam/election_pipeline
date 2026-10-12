
import json
import requests

CONFIG_URL = (
    "https://resultados-sim.tse.jus.br/"
    "simulado/simulado2026/comum/config/ele-c.json"
)


def main():
    print("Consultando configuração do ambiente de simulação do TSE...")

    try:
        response = requests.get(
            CONFIG_URL,
            timeout=(5, 15),
            headers={"User-Agent": "ElectionPipeline/0.1"},
        )

        print(f"Status HTTP: {response.status_code}")

        if response.status_code == 404:
            print("Arquivo não encontrado neste ambiente.")
            print("Não serão feitas novas tentativas automáticas.")
            return

        response.raise_for_status()
        data = response.json()

        print("\nJSON recebido com sucesso.")
        print("Tipo:", type(data).__name__)

        print("\nConteúdo:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:5000])

    except requests.RequestException as error:
        print(f"Erro na requisição: {error}")
    except ValueError:
        print("A resposta não contém JSON válido.")


if __name__ == "__main__":
    main()
