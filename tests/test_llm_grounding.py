from src.infrastructure.llm_client import UnifiedLLMClient


def test_unknown_product_never_receives_arbitrary_tariff():
    response = UnifiedLLMClient()._synthesize_grounded_maritime_response(
        "Cuanto cuesta traer un lapiz a Panama"
    )
    assert "Clasificación arancelaria pendiente" in response
    assert "0201" not in response
    assert "No se calcularon DAI" in response
