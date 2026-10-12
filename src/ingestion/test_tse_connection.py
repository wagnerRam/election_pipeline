import requests

URL = "https://resultados.tse.jus.br/"


def main():
    print("Testando conexão com o servidor do TSE...")

    try:
        response = requests.get(
            URL,
            timeout=(5, 15),
            headers={"User-Agent": "ElectionPipeline/0.1"},
            allow_redirects=True,
        )

        print(f"Status HTTP final: {response.status_code}")
        print(f"URL final: {response.url}")
        print(f"Redirecionamentos: {len(response.history)}")

        if response.ok:
            print("Conexão HTTP estabelecida com sucesso.")
        else:
            print("O servidor respondeu com um status HTTP de erro.")

    except requests.RequestException as error:
        print(f"Falha na requisição: {error}")


if __name__ == "__main__":
    main()