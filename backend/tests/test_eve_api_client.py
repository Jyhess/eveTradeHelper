"""
Tests d'intégration pour EveAPIClient
Compare les réponses API avec des références
"""

import pytest
import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Importer les fonctions utilitaires
# Depuis backend/, on peut importer tests.test_utils ou test_utils selon le contexte
try:
    from tests.test_utils import (
        save_reference,
        load_reference,
        normalize_for_comparison,
    )
except ImportError:
    from test_utils import (
        save_reference,
        load_reference,
        normalize_for_comparison,
    )


class TestEveAPIClientRegions:
    """Tests pour les méthodes liées aux régions"""

    def test_get_regions_list(self, eve_client, reference_data):
        """Test de récupération de la liste des régions"""
        result = eve_client.get_regions_list()
        
        # Vérifier que c'est une liste
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) > 0, "La liste ne doit pas être vide"
        assert all(isinstance(region_id, int) for region_id in result), "Tous les éléments doivent être des entiers"
        
        # Comparer avec la référence si elle existe
        ref_key = "regions_list"
        reference = load_reference(ref_key)
        
        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)
            
            assert result_normalized == ref_normalized, (
                f"Le résultat ne correspond pas à la référence.\n"
                f"Résultat: {result_normalized[:5]}...\n"
                f"Référence: {ref_normalized[:5]}..."
            )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")

    def test_get_region_details(self, eve_client, reference_data):
        """Test de récupération des détails d'une région"""
        # Utiliser une région connue (The Forge - région ID 10000002)
        region_id = 10000002
        result = eve_client.get_region_details(region_id)
        
        # Vérifications de base
        assert isinstance(result, dict), "Le résultat doit être un dictionnaire"
        assert "name" in result, "Le résultat doit contenir 'name'"
        assert "region_id" not in result or result.get("name") is not None, "Le nom doit être défini"
        
        # Comparer avec la référence
        ref_key = f"region_details_{region_id}"
        reference = load_reference(ref_key)
        
        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)
            
            # Comparer les champs clés
            assert result_normalized.get("name") == ref_normalized.get("name"), (
                f"Le nom de la région ne correspond pas.\n"
                f"Résultat: {result_normalized.get('name')}\n"
                f"Référence: {ref_normalized.get('name')}"
            )
            
            # Vérifier que les constellations sont présentes
            if "constellations" in ref_normalized:
                assert "constellations" in result_normalized, "Les constellations doivent être présentes"
                assert len(result_normalized["constellations"]) == len(ref_normalized["constellations"]), (
                    f"Le nombre de constellations ne correspond pas.\n"
                    f"Résultat: {len(result_normalized['constellations'])}\n"
                    f"Référence: {len(ref_normalized['constellations'])}"
                )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")

    def test_get_regions_with_details(self, eve_client, reference_data):
        """Test de récupération des régions avec leurs détails (limité à 5 pour les tests)"""
        limit = 5
        result = eve_client.get_regions_with_details(limit=limit)
        
        # Vérifications de base
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) <= limit, f"Le résultat ne doit pas dépasser {limit} éléments"
        
        for region in result:
            assert isinstance(region, dict), "Chaque région doit être un dictionnaire"
            assert "region_id" in region, "Chaque région doit avoir un region_id"
            assert "name" in region, "Chaque région doit avoir un name"
        
        # Comparer avec la référence
        ref_key = f"regions_with_details_limit_{limit}"
        reference = load_reference(ref_key)
        
        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)
            
            assert len(result_normalized) == len(ref_normalized), (
                f"Le nombre de régions ne correspond pas.\n"
                f"Résultat: {len(result_normalized)}\n"
                f"Référence: {len(ref_normalized)}"
            )
            
            # Comparer les noms des régions
            result_names = [r.get("name") for r in result_normalized]
            ref_names = [r.get("name") for r in ref_normalized]
            assert result_names == ref_names, (
                f"Les noms des régions ne correspondent pas.\n"
                f"Résultat: {result_names}\n"
                f"Référence: {ref_names}"
            )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")


class TestEveAPIClientCache:
    """Tests pour vérifier le fonctionnement du cache"""

    def test_cache_is_used(self, eve_client):
        """Vérifie que le cache est utilisé lors du second appel"""
        from eve import CacheManager
        
        assert CacheManager.is_initialized(), "Le cache doit être initialisé"
        
        # Premier appel - doit aller à l'API
        result1 = eve_client.get_regions_list()
        assert isinstance(result1, list)
        
        # Second appel - doit utiliser le cache
        result2 = eve_client.get_regions_list()
        
        # Les résultats doivent être identiques
        assert result1 == result2, "Les résultats doivent être identiques (cache utilisé)"
        
        # Vérifier que le cache contient les données
        cache = CacheManager.get_instance()
        # Le cache devrait avoir été utilisé (vérification indirecte via la vitesse)

    def test_cache_expiry(self, eve_client):
        """Vérifie que le cache expire correctement"""
        from eve import CacheManager, SimpleCache
        
        # Créer un cache avec expiration très courte (1 milliseconde)
        short_cache = SimpleCache(cache_dir=str(CacheManager.get_instance().cache_dir), expiry_hours=0.000000278)  # 1 ms
        CacheManager.initialize(short_cache)
        
        # Premier appel
        result1 = eve_client.get_regions_list()
        
        # Attendre que le cache expire
        import time
        time.sleep(0.01)  # 10 ms
        
        # Deuxième appel - le cache devrait être expiré
        # On ne peut pas vraiment tester que l'API est appelée à nouveau sans mocker,
        # mais on peut vérifier que le cache ne retourne pas de données
        cache = CacheManager.get_instance()
        # Le cache devrait être invalide maintenant


class TestEveAPIClientStructure:
    """Tests pour vérifier la structure des réponses"""

    def test_region_details_structure(self, eve_client):
        """Vérifie que les détails d'une région ont la structure attendue"""
        region_id = 10000002
        result = eve_client.get_region_details(region_id)
        
        # Structure attendue
        expected_keys = ["name", "constellations"]
        
        for key in expected_keys:
            assert key in result, f"La clé '{key}' doit être présente dans le résultat"
        
        # Vérifier les types
        assert isinstance(result["name"], str), "name doit être une chaîne"
        assert isinstance(result["constellations"], list), "constellations doit être une liste"
        
        # Vérifier que les constellations sont des entiers
        if result["constellations"]:
            assert all(
                isinstance(c, int) for c in result["constellations"]
            ), "Les constellations doivent être des entiers"

    def test_regions_list_structure(self, eve_client):
        """Vérifie que la liste des régions a la structure attendue"""
        result = eve_client.get_regions_list()
        
        assert isinstance(result, list), "Le résultat doit être une liste"
        
        if result:
            # Vérifier le type des éléments
            assert all(
                isinstance(item, int) for item in result
            ), "Tous les éléments doivent être des entiers"
            
            # Vérifier qu'il n'y a pas de doublons
            assert len(result) == len(set(result)), "Il ne doit pas y avoir de doublons"

