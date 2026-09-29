/**
 * Panamá PortOps-AI v1.0.0 - Dicionário de Tradução em Português (pt)
 * Desenvolvido por Miguel Benítez | GNU GPL v3.0
 */
window.I18N_PT = {
  nav: {
    app_title: "Panamá PortOps-AI",
    version: "v1.0.0",
    author: "Desenvolvido v1.0.0 Miguel Benítez",
    developed_by: "developed by Miguel Benítez",
    theme_atlantic: "Atlântico Night (Ciano)",
    theme_amber: "Radar Balboa (Âmbar)",
    theme_emerald: "Bacia Canal (Esmeralda)",
    theme_tactical: "Titânio Tático (Mono)",
    theme_sunset: "Pacífico Sunset (Coral / Neon)",
    theme_cobalt: "Midnight Cobalt (Azul Profundo)",
    login_iam: "Iniciar Sessão | Login In",
    role_prefix: "Função:",
    worm_valid: "WORM: Válido",
    verifying: "Verificando...",
    healthy: "100% Operacional",
    settings: "Ajustes",
    openapi_docs: "OpenAPI Docs",
    lang_label: "Idioma:"
  },
  tabs: {
    landing: "Início & Visão Geral",
    cot_swarm: "🧠 Raciocínio CoT & Agentes",
    customs_lakehouse: "🛃 RAG Alfândega, Tarifas & Lakehouse",
    forecast: "Previsão & What-If",
    benchmark: "Comparativo Multi-Algoritmo",
    diagnostics: "Diagnóstico Estatístico & Erros",
    simulation: "Simulação Monte Carlo",
    methodology: "Metodologia & Arquitetura",
    data_platform: "Data Platform & 5D Qualidade",
    security_iam: "Segurança, IAM & WORM"
  },
  landing: {
    hero_title: "Inteligência Artificial Portuária, Inferência Quantílica e MLOps para o Hub Logístico do Panamá",
    hero_desc: "Plataforma analítica e industrial de código aberto desenvolvida para processar microdados reais da Autoridade Marítima do Panamá (AMP). Livre de custos proprietários de licenciamento, sob estrito cumprimento cívico da Lei 6 de 2002.",
    author_badge: "Autor: Miguel Benítez",
    license_badge: "Licença: GNU GPL v3.0",
    attribution_notice: "Atribuição de autoria obrigatória sob a Seção 7 da Licença GNU GPL v3.0.",
    stat_data_points: "140 Meses",
    stat_data_points_sub: "Microdados Reais (2015–2026)",
    stat_accuracy: "90.89% Precisão",
    stat_accuracy_sub: "Champion LightGBM (WAPE 9.11%)",
    stat_zero_mocks: "0% Mocks",
    stat_zero_mocks_sub: "Garantia de Dados Reais em Prod",
    stat_worm_ledger: "SHA-256",
    stat_worm_ledger_sub: "Ledger WORM Imutável"
  },
  cot: {
    title: "Cadeia de Raciocínio CoT, Guardrails e Almas Criptográficas",
    subtitle: "Inspeção em tempo real dos 5 marcos operacionais: Guardrails de Contexto, Selo Anti-Tamper, RAG Jurídico (Lei 6/56), Inferência Quantílica e Síntese Executiva.",
    native_tag: "v1.0.0 NATIVO",
    souls_tag: "🔐 4 SOULS SELADOS SHA-256",
    guardrails_tag: "🛡️ GUARDRAILS ATIVOS",
    model_interaction: "Interação com o Modelo",
    soul_label: "Alma de Agente / Soul Selecionado:",
    soul_customs: "🛃 Agente Aduaneiro (Tarifas, DAI, ITBMS, ANA)",
    soul_auditor: "⚖️ Auditor Regulatório (Lei 6/2002, Lei 56/2008, WORM)",
    soul_dock: "🚢 Operador de Cais (STS, Pátios, TOS Balboa)",
    soul_risk: "📈 Gestor de Risco & What-If (Monte Carlo, Seca)",
    engine_label: "Motor LLM de Inferência:",
    guardrail_label: "Nível de Guardrail:",
    guardrail_strict: "Estrito (Contexto Marítimo Obrigatório)",
    guardrail_balanced: "Balanceado (Auditoria Flexível)",
    guardrail_permissive: "Permissivo (Apenas Injeções Graves)",
    prompt_label: "Pergunta ou Instrução Operacional:",
    prompt_placeholder: "Digite sua consulta portuária, aduaneira ou de risco...",
    quick_queries: "Consultas Rápidas de Teste:",
    btn_run_cot: "Executar Inferência CoT em Tempo Real",
    step1_title: "Verificação de Guardrail de Entrada",
    step2_title: "Verificação Criptográfica de Soul Imutável",
    step3_title: "Recuperação de Evidência Normativa e RAG Marítimo",
    step4_title: "Inferência Numérica & Garantia Isotônica (P10 <= P50 <= P90)",
    step5_title: "Síntese Executiva e Formatação Formal",
    synthesis_title: "Síntese Executiva do Agente",
    copy_btn: "Copiar Resposta",
    legal_citations_title: "Fontes e Citações Normativas Panamenhas Rastreadas:",
    feedback_title: "Avaliação da Resposta & Feedback MLOps",
    feedback_useful: "Útil",
    feedback_not_useful: "Não Útil",
    feedback_category: "Categoria:",
    feedback_comment_placeholder: "Detalhe técnico ou correção observada...",
    btn_submit_feedback: "Enviar Feedback"
  },
  customs: {
    title: "Lakehouse Medallion & RAG Jurídico-Tarifário Panamenho",
    subtitle: "Consulta em tempo real de capítulos arancelários, códigos HS (2026), tratados bilaterais e cálculo dinâmico de liquidação fiscal de importação.",
    search_label: "Consulta RAG no Banco Tarifário:",
    search_placeholder: "Buscar por HS Code (ex. 0803, 8703, 0201) ou mercadoria...",
    btn_search: "Buscar RAG",
    calculator_title: "Calculadora de Liquidação Fiscal Aduaneira (ANA)",
    cif_value: "Valor CIF (USD):",
    btn_calculate: "Calcular Liquidação Fiscal"
  },
  forecast: {
    title: "Previsão Quantílica de Demanda Portuária & Simulação What-If",
    subtitle: "Horizonte dinâmico de 1 a 6 meses por terminal com bandas de incerteza operacional P10, P50 e P90.",
    terminal_label: "Terminal Portuário:",
    horizon_label: "Horizonte de Previsão:",
    btn_predict: "Executar Previsão Quantílica"
  },
  benchmark: {
    title: "Torneio de 8 Algoritmos de Machine Learning (Backtesting Temporal)",
    subtitle: "Comparação empírica de 8 modelos competitivos avaliados sobre 140 meses de microdados históricos.",
    btn_compare: "Atualizar Métricas de Benchmark"
  },
  footer: {
    legal: "Desenvolvido por Miguel Benítez • Engenheiro em Sistemas e Computação • Universidade Tecnológica do Panamá (UTP) • Licença GNU GPL v3.0 com Atribuição Obrigatória (Seção 7).",
    disclaimer: "Dados abertos protegidos sob a Lei 6 de 2002 da República do Panamá."
  }
};
