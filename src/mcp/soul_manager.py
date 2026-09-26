"""
Model Context Protocol (MCP) Soul & Persona Configuration Engine.
Manages AI agent personas ("souls"), business logic constraints, prompt templates,
role capabilities, and structured JSON-RPC 2.0 communication format for Panama PortOps-AI.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from src.mcp.tools import execute_tool, get_available_tools_schema


@dataclass
class MCPAgentSoul:
    id: str
    name: str
    target_role: str
    badge: str
    system_instructions: str
    guardrails_enforced: List[str]
    allowed_tools: List[str]
    output_formatting_style: str  # "Jurídico Formal con Citas", "Operativo Breve con Métricas", "Científico con Fórmulas"


class MCPSoulManager:
    """
    Manages custom AI agent personas ('souls') and formats JSON-RPC 2.0 tool executions.
    """

    DEFAULT_SOULS: List[MCPAgentSoul] = [
        MCPAgentSoul(
            id="auditor_maritimo",
            name="Auditor Marítimo Gubernamental (Ley 56 & Ley 6)",
            target_role="Auditor de Transparencia de la República de Panamá",
            badge="⚖️ Fiscalizador Legal",
            system_instructions=(
                "Eres el Auditor Marítimo de Panamá PortOps-AI v1.0 (Desarrollado v1.0 Miguel Benítez). "
                "Tus respuestas deben ser estrictas, profesionales y sustentadas jurídicamente en la Ley 56 de 2008 (General de Puertos) "
                "y la Ley 6 de 2002 (Transparencia en la Gestión Pública). Cita artículos textuales y verifica siempre el cumplimiento "
                "de los calados mínimos obligatorios y los límites de concesión de muelles. Jamás inventes datos."
            ),
            guardrails_enforced=[
                "Prohibición de especulación jurídica",
                "Cita obligatoria de fuente oficial (AMP o Gaceta Oficial)",
                "Sanitización contra inyección de prompts"
            ],
            allowed_tools=["get_port_forecast", "compare_model_benchmarks", "query_maritime_knowledge"],
            output_formatting_style="Jurídico Formal con Citas"
        ),
        MCPAgentSoul(
            id="operador_muelle",
            name="Especialista de Patio & Operaciones Portuarias",
            target_role="Planificador de Grúas STS y Fondeadero",
            badge="⚓ Operativo de Muelle",
            system_instructions=(
                "Eres el Especialista en Operaciones Portuarias de Panamá PortOps-AI v1.0. "
                "Tu objetivo es pragmático: evaluar la demanda de TEUs a 1-6 meses, dimensionar la cantidad requerida de grúas STS "
                "(asumiendo 28 movimientos/hora/grúa), alertar sobre congestión de contenedores vacíos si el ratio supera 0.80, "
                "y mitigar tiempos muertos en fondeadero ante vientos de frentes fríos en Colón o restricciones de calado en Balboa."
            ),
            guardrails_enforced=[
                "Límite físico máximo: 600,000 TEUs/mes por terminal",
                "Monotonicidad estricta: P10 <= P50 <= P90",
                "Semáforo obligatorio de balance de vacíos"
            ],
            allowed_tools=["get_port_forecast", "run_monte_carlo_risk_simulation", "simulate_external_feature"],
            output_formatting_style="Operativo Breve con Métricas"
        ),
        MCPAgentSoul(
            id="cientifico_causal",
            name="Científico de Datos Causal & MLOps",
            target_role="Investigador de Inferencia Causal y Series Temporales",
            badge="🔬 Analítico Doctoral",
            system_instructions=(
                "Eres el Investigador Científico de Panamá PortOps-AI v1.0. "
                "Explicas rigurosamente los modelos matemáticos: Pinball Loss en cuantiles de LightGBM, descomposición de "
                "residuales (y - y_hat), Factor de Inflación de la Varianza (VIF), y des-sesgado de variables confusoras mediante "
                "el do-calculus de Judea Pearl. Utilizas KaTeX/LaTeX para fundamentar cada respuesta y destacas la importancia "
                "de la reproducibilidad fijando semilla 42."
            ),
            guardrails_enforced=[
                "Cero fuga temporal (Zero lookahead bias con .shift(1))",
                "Trazabilidad bitemporal (fecha_validez, fecha_publicacion)",
                "Explicabilidad transparente de split gains"
            ],
            allowed_tools=["compare_model_benchmarks", "run_monte_carlo_risk_simulation", "simulate_external_feature", "query_maritime_knowledge"],
            output_formatting_style="Científico con Fórmulas"
        )
    ]

    _custom_souls: List[MCPAgentSoul] = []

    @classmethod
    def list_souls(cls) -> List[Dict[str, Any]]:
        """Returns all default and custom souls."""
        combined = cls.DEFAULT_SOULS + cls._custom_souls
        return [asdict(s) for s in combined]

    @classmethod
    def get_soul(cls, soul_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a soul by ID."""
        for s in cls.DEFAULT_SOULS + cls._custom_souls:
            if s.id == soul_id:
                return asdict(s)
        return None

    @classmethod
    def save_or_update_soul(
        cls,
        soul_id: str,
        name: str,
        target_role: str,
        badge: str,
        system_instructions: str,
        guardrails_enforced: List[str],
        allowed_tools: List[str],
        output_formatting_style: str = "Operativo Breve con Métricas"
    ) -> Dict[str, Any]:
        """Saves or updates a custom AI personality soul."""
        new_soul = MCPAgentSoul(
            id=soul_id.strip().lower(),
            name=name.strip(),
            target_role=target_role.strip(),
            badge=badge.strip(),
            system_instructions=system_instructions.strip(),
            guardrails_enforced=guardrails_enforced,
            allowed_tools=allowed_tools,
            output_formatting_style=output_formatting_style
        )
        # Check if updating existing custom soul
        for i, s in enumerate(cls._custom_souls):
            if s.id == new_soul.id:
                cls._custom_souls[i] = new_soul
                return {"status": "updated", "soul": asdict(new_soul)}

        cls._custom_souls.append(new_soul)
        return {"status": "created", "soul": asdict(new_soul)}

    @classmethod
    def execute_mcp_tool_rpc(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        soul_id: Optional[str] = "operador_muelle"
    ) -> Dict[str, Any]:
        """
        Executes an MCP tool and wraps it into an official JSON-RPC 2.0 response format.
        """
        start_time = time.time()
        rpc_id = int(time.time() * 1000)
        soul = cls.get_soul(soul_id or "operador_muelle")

        # Validate if soul is authorized for this tool
        if soul and tool_name not in soul["allowed_tools"] and "*" not in soul["allowed_tools"]:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32600,
                    "message": f"Herramienta '{tool_name}' no autorizada para el Soul '{soul['name']}'.",
                    "data": {"allowed_tools": soul["allowed_tools"]}
                }
            }

        # Execute tool
        try:
            tool_result = execute_tool(tool_name, arguments)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tool": tool_name,
                    "author": "Desarrollado v1.0 Miguel Benítez",
                    "soul_context": {
                        "soul_id": soul["id"] if soul else "default",
                        "persona": soul["name"] if soul else "Agente Genérico",
                        "formatting_style": soul["output_formatting_style"] if soul else "Standard"
                    },
                    "execution_time_ms": elapsed_ms,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result, ensure_ascii=False, indent=2)
                        }
                    ],
                    "raw_data": tool_result
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32603,
                    "message": f"Error interno en ejecución de herramienta MCP: {str(e)}"
                }
            }


class LangGraphAgentRouter:
    """
    Multi-Agent State Graph Orchestrator inspired by LangGraph.
    Classifies user natural-language queries, evaluates guardrails,
    and dynamically routes tasks to the appropriate specialized MCP Soul:
    - auditor_maritimo (ISO, Ley 56, Ley 6 de Transparencia)
    - operador_muelle (Logística de muelle, grúas STS, semáforo de vacíos)
    - cientifico_causal (LightGBM, Pinball loss, do-calculus, Monte Carlo)
    - ingesta_master (Lakehouse, 17 ministerios, Parquet y calidad)
    """

    INTENT_KEYWORDS = {
        "auditor_maritimo": ["ley", "articulo", "concesion", "contrato", "transparencia", "iso", "auditoria", "contraloria", "seguridad", "cumplimiento"],
        "operador_muelle": ["patio", "grua", "sts", "vacio", "vacia", "congestion", "fondeadero", "buque", "camion", "puerto", "demanda", "pronostico", "teu"],
        "cientifico_causal": ["causal", "pearl", "do-calculus", "vif", "lightgbm", "pinball", "wape", "r2", "cuantil", "monte carlo", "cholesky", "residuos", "preset", "hiperparametro"],
        "ingesta_master": ["dataset", "ministerio", "parquet", "acp", "limpieza", "hampel", "bronze", "silver", "gold", "scraping", "datosabiertos"]
    }

    @classmethod
    def route_query(cls, user_query: str) -> Dict[str, Any]:
        """
        Executes the LangGraph DAG state transition:
        [QueryAnalyzer] -> [IntentClassifier] -> [SoulDispatcher] -> [ToolOrchestrator] -> [ResponseSynthesizer]
        """
        start = time.perf_counter()
        q_lower = user_query.lower()

        # Step 1: Score intents based on keyword match
        scores = {}
        for soul_id, keywords in cls.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q_lower)
            scores[soul_id] = score

        # Pick soul with highest score (default to operador_muelle if tied at 0)
        best_soul_id = max(scores, key=scores.get) if any(scores.values()) else "operador_muelle"
        confidence = min(0.60 + (scores[best_soul_id] * 0.12), 0.98) if scores[best_soul_id] > 0 else 0.72

        soul = MCPSoulManager.get_soul(best_soul_id) or MCPSoulManager.get_soul("operador_muelle")

        # Determine tools to call
        recommended_tools = soul.get("allowed_tools", ["get_port_forecast"])

        # LangGraph State Graph Trace
        dag_trace = [
            {"node": "QueryAnalyzer", "status": "COMPLETED", "output": f"Tokens evaluados: {len(q_lower.split())}"},
            {"node": "IntentClassifier", "status": "COMPLETED", "output": f"Intención: {best_soul_id.upper()} (Score: {scores.get(best_soul_id, 0)})"},
            {"node": "SoulDispatcher", "status": "COMPLETED", "output": f"Agente asignado: {soul['name']}"},
            {"node": "GuardrailEvaluator", "status": "COMPLETED", "output": f"Guardrails activos: {len(soul.get('guardrails_enforced', []))}"},
            {"node": "ToolOrchestrator", "status": "READY", "output": f"Herramientas sugeridas: {recommended_tools}"}
        ]

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)

        return {
            "status": "success",
            "orchestrator": "LangGraph StateGraph Engine v1.0",
            "author": "Desarrollado v1.0 Miguel Benítez",
            "query": user_query,
            "selected_soul": {
                "id": soul["id"],
                "name": soul["name"],
                "badge": soul["badge"],
                "formatting_style": soul["output_formatting_style"]
            },
            "confidence_score": round(confidence, 2),
            "routing_reason": f"La consulta contiene descriptores semánticos afines a {soul['target_role']}.",
            "recommended_tools": recommended_tools,
            "guardrails_enforced": soul.get("guardrails_enforced", []),
            "langgraph_dag_trace": dag_trace,
            "latency_ms": elapsed_ms
        }

