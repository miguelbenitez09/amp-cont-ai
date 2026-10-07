from src.infrastructure.llm_client import UnifiedLLMClient


def test_sse_parser_excludes_reasoning_and_done_marker():
    lines = [
        'data: {"choices":[{"delta":{"reasoning":"internal"}}]}',
        'data: {"choices":[{"delta":{"content":"Hola"}}]}',
        'data: {"choices":[{"delta":{"content":" mundo"}}]}',
        "data: [DONE]",
    ]
    assert UnifiedLLMClient.parse_openai_sse(lines) == "Hola mundo"
