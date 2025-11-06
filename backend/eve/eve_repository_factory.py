from .eve_api_client import EveAPIClient
from .eve_repository_impl import EveRepositoryImpl


def make_eve_repository() :
    return EveRepositoryImpl(EveAPIClient())
