"""
Interface du repository pour Eve Online
Définit le contrat que doit respecter tout repository Eve
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EveRepository(ABC):
    """Interface abstraite pour le repository Eve Online"""

    @abstractmethod
    def get_regions_list(self) -> List[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions
        """
        pass

    @abstractmethod
    def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une région

        Args:
            region_id: ID de la région

        Returns:
            Dictionnaire contenant les détails de la région
        """
        pass

    @abstractmethod
    def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une constellation

        Args:
            constellation_id: ID de la constellation

        Returns:
            Dictionnaire contenant les détails de la constellation
        """
        pass

    @abstractmethod
    def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un système solaire

        Args:
            system_id: ID du système

        Returns:
            Dictionnaire contenant les détails du système
        """
        pass

    @abstractmethod
    def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """
        Récupère les informations d'un type d'item

        Args:
            type_id: ID du type d'item

        Returns:
            Dictionnaire contenant les informations de l'item
        """
        pass

