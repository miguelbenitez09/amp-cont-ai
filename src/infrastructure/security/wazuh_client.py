"""Minimal Wazuh API adapter with explicit configuration and bounded requests."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class WazuhClient:
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None, verify_tls: Optional[bool] = None, timeout: float = 5.0):
        self.base_url = (base_url or os.getenv("WAZUH_API_URL", "")).rstrip("/")
        self.username = username or os.getenv("WAZUH_API_USERNAME", "")
        self.password = password or os.getenv("WAZUH_API_PASSWORD", "")
        self.verify_tls = verify_tls if verify_tls is not None else os.getenv("WAZUH_VERIFY_TLS", "true").lower() == "true"
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.username and self.password)

    def authenticate(self) -> str:
        if not self.configured:
            raise RuntimeError("Wazuh API is not configured")
        response = self.session.post(
            f"{self.base_url}/security/user/authenticate",
            auth=(self.username, self.password),
            verify=self.verify_tls,
            timeout=self.timeout,
        )
        response.raise_for_status()
        token = response.json().get("data", {}).get("token")
        if not token:
            raise RuntimeError("Wazuh authentication response did not contain a token")
        return token

    def health(self) -> Dict[str, Any]:
        if not self.configured:
            return {"configured": False, "reachable": False, "status": "UNCONFIGURED"}
        try:
            token = self.authenticate()
            response = self.session.get(
                f"{self.base_url}/manager/status",
                headers={"Authorization": f"Bearer {token}"},
                verify=self.verify_tls,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return {"configured": True, "reachable": True, "status": "CONNECTED", "endpoint": self.base_url, "manager": response.json().get("data", {})}
        except (requests.RequestException, RuntimeError) as exc:
            return {"configured": True, "reachable": False, "status": "ERROR", "endpoint": self.base_url, "error": str(exc)}

    def capabilities(self) -> Dict[str, Any]:
        """Return the supported Wazuh control-plane operations.

        This is deliberately useful while Wazuh is disabled: callers can render
        the management UI and policy checks without pretending that a manager
        connection exists.
        """
        return {
            "configured": self.configured,
            "status": "READY" if self.configured else "DISABLED_COMPATIBLE",
            "operations": ["list_agents", "get_agent", "enroll_agent", "remove_agent", "rotate_agent_key"],
            "transport": "wazuh-api-v4",
        }

    def _request(self, method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Wazuh API is not configured")
        token = self.authenticate()
        response = self.session.request(
            method, f"{self.base_url}{path}", json=json_body,
            headers={"Authorization": f"Bearer {token}"}, verify=self.verify_tls,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", payload)

    def list_agents(self, *, status: Optional[str] = None, limit: int = 500) -> Dict[str, Any]:
        params = f"?limit={max(1, min(limit, 5000))}"
        if status:
            params += f"&status={status}"
        return self._request("GET", f"/agents{params}")

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        if not agent_id or "/" in agent_id:
            raise ValueError("agent_id must be a non-empty identifier")
        return self._request("GET", f"/agents/{agent_id}")

    def enroll_agent(self, name: str, ip: Optional[str] = None) -> Dict[str, Any]:
        if not name.strip():
            raise ValueError("agent name is required")
        body = {"name": name.strip()}
        if ip:
            body["ip"] = ip
        return self._request("POST", "/agents", json_body=body)

    def remove_agent(self, agent_id: str) -> Dict[str, Any]:
        if not agent_id or "/" in agent_id:
            raise ValueError("agent_id must be a non-empty identifier")
        return self._request("DELETE", f"/agents?agents_list={agent_id}")

    def rotate_agent_key(self, agent_id: str) -> Dict[str, Any]:
        if not agent_id or "/" in agent_id:
            raise ValueError("agent_id must be a non-empty identifier")
        return self._request("PUT", f"/agents/{agent_id}/restart")
