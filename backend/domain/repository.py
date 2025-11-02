"""
Interface du repository pour Eve Online
Définit le contrat que doit respecter tout repository Eve (version asynchrone)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class EveRepository(ABC):
    """Interface abstraite pour le repository Eve Online (asynchrone)"""

    @abstractmethod
    async def get_regions_list(self) -> List[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions
        """
        pass

    @abstractmethod
    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une région

        Args:
            region_id: ID de la région

        Returns:
            Dictionnaire contenant les détails de la région
        """
        pass

    @abstractmethod
    async def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une constellation

        Args:
            constellation_id: ID de la constellation

        Returns:
            Dictionnaire contenant les détails de la constellation
        """
        pass

    @abstractmethod
    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un système solaire

        Args:
            system_id: ID du système

        Returns:
            Dictionnaire contenant les détails du système
        """
        pass

    @abstractmethod
    async def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """
        Récupère les informations d'un type d'item

        Args:
            type_id: ID du type d'item

        Returns:
            Dictionnaire contenant les informations de l'item
        """
        pass

    @abstractmethod
    async def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une stargate (porte stellaire)

        Args:
            stargate_id: ID de la stargate

        Returns:
            Dictionnaire contenant les détails de la stargate
        """
        pass

    @abstractmethod
    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une station

        Args:
            station_id: ID de la station

        Returns:
            Dictionnaire contenant les détails de la station
        """
        pass

    @abstractmethod
    async def get_market_groups_list(self) -> List[int]:
        """
        Récupère la liste des IDs de groupes de marché

        Returns:
            Liste des IDs de groupes de marché
        """
        pass

    @abstractmethod
    async def get_market_group_details(self, group_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un groupe de marché

        Args:
            group_id: ID du groupe de marché

        Returns:
            Dictionnaire contenant les détails du groupe de marché
        """
        pass

    @abstractmethod
    async def get_market_orders(
        self, region_id: int, type_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les ordres de marché pour une région, optionnellement filtrés par type

        Args:
            region_id: ID de la région
            type_id: Optionnel, ID du type d'item pour filtrer les ordres

        Returns:
            Liste des ordres de marché
        """
        pass

    @abstractmethod
    async def get_route(self, origin: int, destination: int) -> List[int]:
        """
        Calcule la route entre deux systèmes

        Args:
            origin: ID du système d'origine
            destination: ID du système de destination

        Returns:
            Liste des IDs de systèmes formant la route (incluant origin et destination)
            Si pas de route trouvée, retourne une liste vide
        """
        pass

    @abstractmethod
    async def get_route_with_details(
        self, origin: int, destination: int
    ) -> List[Dict[str, Any]]:
        """
        Calcule la route entre deux systèmes avec les détails de sécurité

        Args:
            origin: ID du système d'origine
            destination: ID du système de destination

        Returns:
            Liste de dictionnaires contenant les détails de chaque système de la route
            Chaque dictionnaire contient: system_id, name, security_status
            Si pas de route trouvée, retourne une liste vide
        """
        pass