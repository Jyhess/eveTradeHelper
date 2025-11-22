"""
Interface du repository pour Eve Online
Définit le contrat que doit respecter tout repository Eve (version asynchrone)
"""

from abc import ABC, abstractmethod

from .types import (
    ConstellationDetails,
    ItemType,
    MarketGroupDetails,
    Order,
    RegionDetails,
    RouteDetail,
    StargateDetails,
    StationDetails,
    SystemDetails,
)


class EveRepository(ABC):
    """Interface abstraite pour le repository Eve Online (asynchrone)"""

    @abstractmethod
    async def get_regions_list(self) -> list[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions
        """
        pass

    @abstractmethod
    async def get_region_details(self, region_id: int) -> RegionDetails:
        """
        Récupère les détails d'une région

        Args:
            region_id: ID de la région

        Returns:
            RegionDetails contenant les détails de la région
        """
        pass

    @abstractmethod
    async def get_constellation_details(self, constellation_id: int) -> ConstellationDetails:
        """
        Récupère les détails d'une constellation

        Args:
            constellation_id: ID de la constellation

        Returns:
            ConstellationDetails contenant les détails de la constellation
        """
        pass

    @abstractmethod
    async def get_system_details(self, system_id: int) -> SystemDetails:
        """
        Récupère les détails d'un système solaire

        Args:
            system_id: ID du système

        Returns:
            SystemDetails contenant les détails du système
        """
        pass

    @abstractmethod
    async def get_item_type(self, type_id: int) -> ItemType:
        """
        Récupère les informations d'un type d'item

        Args:
            type_id: ID du type d'item

        Returns:
            ItemType contenant les informations de l'item
        """
        pass

    @abstractmethod
    async def get_stargate_details(self, stargate_id: int) -> StargateDetails:
        """
        Récupère les détails d'une stargate (porte stellaire)

        Args:
            stargate_id: ID de la stargate

        Returns:
            StargateDetails contenant les détails de la stargate
        """
        pass

    @abstractmethod
    async def get_station_details(self, station_id: int) -> StationDetails:
        """
        Récupère les détails d'une station

        Args:
            station_id: ID de la station

        Returns:
            StationDetails contenant les détails de la station
        """
        pass

    @abstractmethod
    async def get_market_groups_list(self) -> list[int]:
        """
        Récupère la liste des IDs de groupes de marché

        Returns:
            Liste des IDs de groupes de marché
        """
        pass

    @abstractmethod
    async def get_market_group_details(self, group_id: int) -> MarketGroupDetails:
        """
        Récupère les détails d'un groupe de marché

        Args:
            group_id: ID du groupe de marché

        Returns:
            MarketGroupDetails contenant les détails du groupe de marché
        """
        pass

    @abstractmethod
    async def get_market_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
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
    async def get_route(self, origin: int, destination: int) -> list[int]:
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
    async def get_route_with_details(self, origin: int, destination: int) -> list[RouteDetail]:
        """
        Calcule la route entre deux systèmes avec les détails de sécurité

        Args:
            origin: ID du système d'origine
            destination: ID du système de destination

        Returns:
            Liste de RouteDetail contenant les détails de chaque système de la route
            Si pas de route trouvée, retourne une liste vide
        """
        pass
