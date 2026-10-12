
from src.ingestion.tse_config import find_presidential_elections


def test_finds_presidential_election():
    config = {
        "pl": [
            {
                "c": "ele2026",
                "e": [
                    {
                        "cd": "21270",
                        "cdt2": "21271",
                        "nm": "Eleição Federal de Teste",
                        "abr": [
                            {
                                "cd": "br",
                                "cp": [
                                    {
                                        "cd": "1",
                                        "ds": "Presidente",
                                        "tp": "1",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    elections = find_presidential_elections(config)

    assert len(elections) == 1
    assert elections[0]["election_code"] == "21270"
    assert elections[0]["second_round_code"] == "21271"
    assert elections[0]["office_code"] == "1"
    assert elections[0]["environment"] == "simulation"


def test_returns_empty_when_no_president():
    config = {"pl": []}

    assert find_presidential_elections(config) == []


def test_missing_second_round_code():
    config = {
        "pl": [
            {
                "c": "ele2026",
                "e": [
                    {
                        "cd": "12345",
                        "cdt2": "",
                        "nm": "Eleição de teste",
                        "abr": [
                            {
                                "cd": "br",
                                "cp": [
                                    {"cd": "1", "ds": "Presidente"}
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    elections = find_presidential_elections(config)

    assert len(elections) == 1
    assert elections[0]["second_round_code"] is None

