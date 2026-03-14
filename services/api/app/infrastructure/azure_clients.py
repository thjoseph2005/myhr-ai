from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import OpenAI

from app.core.config import Settings


def build_openai_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.azure_openai_api_key,
        base_url=f"{settings.azure_openai_endpoint.rstrip('/')}/openai/v1/",
    )


def build_search_client(settings: Settings) -> SearchClient:
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )


def build_search_index_client(settings: Settings) -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )
