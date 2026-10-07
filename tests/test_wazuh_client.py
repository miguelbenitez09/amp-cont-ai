from src.infrastructure.security.wazuh_client import WazuhClient


def test_wazuh_unconfigured_is_explicit():
    client = WazuhClient(base_url="", username="", password="")
    assert client.health() == {"configured": False, "reachable": False, "status": "UNCONFIGURED"}


def test_wazuh_capabilities_remain_available_when_disabled():
    capabilities = WazuhClient(base_url="", username="", password="").capabilities()
    assert capabilities["status"] == "DISABLED_COMPATIBLE"
    assert "enroll_agent" in capabilities["operations"]


def test_wazuh_rejects_agent_path_injection():
    client = WazuhClient(base_url="http://wazuh", username="u", password="p")
    try:
        client.get_agent("1/../../admin")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe agent id was accepted")
