"""
Specialized Maritime AI Agents for Panama PortOps-AI v2.0
Implements:
1. AuditorMaritimoAgent (Legal compliance, Ley 6/2002, Ley 56/2008, ISO standards, WORM ledger).
2. OperadorMuelleAgent (Container yard management, STS cranes, berth allocation, empty ratio).
3. CausalRiskAgent (Monte Carlo simulations, Merton jumps, VaR/CVaR, geopolitical shocks).
4. AgenteAduaneroTariffAgent (Panama customs tariff HS codes, DAI/ITBMS liquidation, MIDA/MINSA permits).

Author: Desarrollado v1.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.infrastructure.llm_client import get_llm_client
from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase
from src.data.parsers.container_iso6346 import ISO6346ContainerValidator
from src.models.inference.engine import get_inference_engine


class BaseMaritimeAgent:
    """Base class for all maritime domain agents."""

    def __init__(self, agent_id: str, name: str, role_title: str, required_permission: str):
        self.agent_id = agent_id
        self.name = name
        self.role_title = role_title
        self.required_permission = required_permission
        self.llm = get_llm_client()

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError


class AuditorMaritimoAgent(BaseMaritimeAgent):
    """Compliance with Law 6 of 2002, Law 56 of 2008, ISO 27001/42001, and WORM certification."""

    def __init__(self):
        super().__init__(
            agent_id="agent_auditor_maritimo",
            name="Auditor Marítimo y Regulatorio",
            role_title="Oficial de Cumplimiento Normativo y Transparencia Pública",
            required_permission="audit.read"
        )

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sys_prompt = (
            "Eres el Auditor Marítimo y Regulatorio de la República de Panamá. Tu especialidad es la Ley 6 de 2002 "
            "(Transparencia y Datos Abiertos), la Ley 56 de 2008 (Ley General de Puertos de Panamá) y los estándares ISO 27001 / ISO 42001. "
            "Responde con rigor jurídico, citando artículos y asegurando que las operaciones mantengan trazabilidad inmutable WORM."
        )
        llm_res = self.llm.generate_chat_response(sys_prompt, query)
        return {
            "author": "Desarrollado v1.0 Miguel Benítez",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "response": llm_res["content"],
            "legal_citations": ["Ley 6 de 2002 (Panamá)", "Ley 56 de 2008 (AMP)", "ISO/IEC 27001:2022", "ISO 42001:2023"],
            "backend_telemetry": llm_res,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class OperadorMuelleAgent(BaseMaritimeAgent):
    """Yard management, STS cranes, berth allocation, and empty ratio traffic lights."""

    def __init__(self):
        super().__init__(
            agent_id="agent_operador_muelle",
            name="Operador de Muelle y Patios TOS",
            role_title="Superintendente de Operaciones Terminales Portuarias",
            required_permission="forecast.read"
        )

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        engine = get_inference_engine()
        forecast = engine.predict_terminal("Puerto Balboa")

        sys_prompt = (
            "Eres el Superintendente de Muelle y Patios Portuarios de Panamá (Balboa, MIT, Cristóbal, CCT, PSA). "
            "Tu misión es optimizar la asignación de grúas pórtico STS, la circulación de yard trucks y vigilar el semáforo "
            "de contenedores vacíos para evitar saturación de patios. Habla en términos operativos de logística marítima."
        )
        context_str = f"Pronóstico P50 Balboa: {forecast['forecast_quantiles_teus']['p50_median_central']} TEUs. Intervalo: {forecast['interval_width_teus']} TEUs."
        llm_res = self.llm.generate_chat_response(sys_prompt, f"{query}\nContexto Operativo: {context_str}")

        return {
            "author": "Desarrollado v1.0 Miguel Benítez",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "response": llm_res["content"],
            "terminal_kpis": forecast["forecast_quantiles_teus"],
            "backend_telemetry": llm_res,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class CausalRiskAgent(BaseMaritimeAgent):
    """Stochastic simulations, Merton jump diffusion, and VaR/CVaR risk evaluation."""

    def __init__(self):
        super().__init__(
            agent_id="agent_causal_risk",
            name="Científico de Riesgo Causal y Monte Carlo",
            role_title="Analista Cuantitativo de Estrés y Geopolítica Marítima",
            required_permission="simulation.run"
        )

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sys_prompt = (
            "Eres el Científico Cuantitativo de Riesgo Portuario de Panamá. Dominas la econometría de Judea Pearl (do-calculus), "
            "simulaciones de Monte Carlo con descomposición de Cholesky, difusión con saltos de Merton y cálculo de Value at Risk (VaR 95%) "
            "y Expected Shortfall (CVaR). Explica con claridad matemática cómo los choques exógenos afectan el flete y la demanda."
        )
        llm_res = self.llm.generate_chat_response(sys_prompt, query)
        return {
            "author": "Desarrollado v1.0 Miguel Benítez",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "response": llm_res["content"],
            "stochastic_framework": "Merton Jump Diffusion & Cholesky Correlated Monte Carlo",
            "backend_telemetry": llm_res,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class AgenteAduaneroTariffAgent(BaseMaritimeAgent):
    """HS Codes classification, Panama customs tariffs (ANA/SIECA), and institutional permits."""

    def __init__(self):
        super().__init__(
            agent_id="agent_aduanero_tariff",
            name="Agente Aduanal y Clasificador Arancelario",
            role_title="Especialista en Valoración Aduanera y Regímenes de Importación ANA",
            required_permission="data.dataset.read"
        )

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Search tariff database
        tariff_matches = PanamaTariffDatabase.search_by_text(query)
        customs_data = tariff_matches[0] if tariff_matches else None

        sys_prompt = (
            "Eres el Agente Aduanal Oficial de la República de Panamá. Tu especialidad es la clasificación arancelaria "
            "a 8, 10 y 12 dígitos de la Autoridad Nacional de Aduanas (ANA) y SIECA. Explicas con precisión las tasas DAI, "
            "el ITBMS (7%), las tasas de declaración aduanera y los permisos previos de MIDA (fitosanitario/zoosanitario), "
            "MINSA (farmacia/alimentos), MiAmbiente (CITES) o DIASP (armas/químicos)."
        )
        extra_ctx = ""
        if customs_data:
            extra_ctx = (
                f"\nInformación arancelaria oficial de la partida: {customs_data['hs_code_panama']} - {customs_data['descripcion']} | "
                f"DAI: {customs_data['arancel_dai_pct']}% | ITBMS: {customs_data['itbms_pct']}% | Permisos: {customs_data['permiso_requerido']}"
            )

        llm_res = self.llm.generate_chat_response(sys_prompt, f"{query}{extra_ctx}")

        return {
            "author": "Desarrollado v1.0 Miguel Benítez",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "response": llm_res["content"],
            "matched_tariff_item": customs_data,
            "backend_telemetry": llm_res,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
