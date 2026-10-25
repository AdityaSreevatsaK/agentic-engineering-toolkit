"""A framework-neutral provider contract; no cloud or model SDK dependencies."""
from .contract import (
    GenerateRequest,
    GenerateResponse,
    ProviderContractError,
    ProviderUnavailableError,
    TextProvider,
    assert_provider_contract,
)
from .adapters import MockProvider, OllamaProvider, LegacyTextAdapter

__version__ = "0.1.0"
__all__ = [
    "GenerateRequest", "GenerateResponse", "ProviderContractError",
    "ProviderUnavailableError", "TextProvider", "assert_provider_contract",
    "MockProvider", "OllamaProvider", "LegacyTextAdapter",
]
