"""
Cliente de Spotify API usando patrón Strategy y Factory
"""
import base64
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger

from .models import SpotifyTrack, SpotifyCountryStats
from .config import config


class SpotifyAuthStrategy(ABC):
    """Estrategia abstracta para autenticación con Spotify"""
    
    @abstractmethod
    def get_access_token(self) -> str:
        """Obtiene el token de acceso"""
        pass


class ClientCredentialsAuth(SpotifyAuthStrategy):
    """Implementación de autenticación Client Credentials"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
    
    def get_access_token(self) -> str:
        """Obtiene token usando Client Credentials Flow"""
        if self._access_token:
            return self._access_token
            
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            logger.info("Token de acceso obtenido exitosamente")
            return self._access_token
            
        except requests.RequestException as e:
            logger.error(f"Error obteniendo token de acceso: {e}")
            raise


class SpotifyDataFetcher(ABC):
    """Interfaz abstracta para obtener datos de Spotify"""
    
    @abstractmethod
    def fetch_country_top_tracks(self, country_code: str, limit: int = 50) -> SpotifyCountryStats:
        """Obtiene las canciones más populares de un país"""
        pass


class SpotifyAPIClient(SpotifyDataFetcher):
    """Cliente principal de la API de Spotify"""
    
    def __init__(self, auth_strategy: SpotifyAuthStrategy):
        self.auth_strategy = auth_strategy
        self.base_url = "https://api.spotify.com/v1"
        self._country_names = {
            "US": "United States", "GB": "United Kingdom", "CA": "Canada",
            "AU": "Australia", "DE": "Germany", "FR": "France", "ES": "Spain",
            "IT": "Italy", "BR": "Brazil", "MX": "Mexico", "AR": "Argentina",
            "CO": "Colombia", "CL": "Chile", "PE": "Peru", "JP": "Japan",
            "KR": "South Korea", "IN": "India", "SE": "Sweden", "NO": "Norway"
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con token de autorización"""
        token = self.auth_strategy.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _parse_track(self, track_data: Dict[str, Any]) -> SpotifyTrack:
        """Convierte datos de track de la API a modelo SpotifyTrack"""
        try:
            return SpotifyTrack(
                track_id=track_data.get("id", "unknown"),
                name=track_data.get("name", "Unknown Track"),
                artist=track_data.get("artists", [{}])[0].get("name", "Unknown Artist") if track_data.get("artists") else "Unknown Artist",
                album=track_data.get("album", {}).get("name", "Unknown Album"),
                popularity=track_data.get("popularity", 0),
                duration_ms=track_data.get("duration_ms", 0),
                explicit=track_data.get("explicit", False),
                preview_url=track_data.get("preview_url")
            )
        except Exception as e:
            logger.warning(f"Error parseando track data: {e}, usando valores por defecto")
            return SpotifyTrack(
                track_id="unknown",
                name="Unknown Track",
                artist="Unknown Artist", 
                album="Unknown Album",
                popularity=0,
                duration_ms=0,
                explicit=False,
                preview_url=None
            )
    
    def fetch_country_top_tracks(self, country_code: str, limit: int = 50) -> SpotifyCountryStats:
        """
        Obtiene las canciones más populares de un país específico
        Nota: Spotify no tiene endpoint directo para top tracks por país,
        por lo que usamos playlists populares como aproximación
        """
        try:
            headers = self._get_headers()
            
            # Buscar playlists populares del país
            search_url = f"{self.base_url}/search"
            params = {
                "q": f"top {country_code} hits",
                "type": "playlist",
                "market": country_code,
                "limit": 1
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            search_data = response.json()
            playlists = search_data.get("playlists", {})
            
            if not playlists or not playlists.get("items"):
                logger.warning(f"No se encontraron playlists para {country_code}")
                return SpotifyCountryStats(
                    country_code=country_code,
                    country_name=self._country_names.get(country_code, country_code),
                    top_tracks=[],
                    total_tracks=0
                )
            
            playlist_items = playlists.get("items", [])
            if not playlist_items:
                logger.warning(f"Lista de playlists vacía para {country_code}")
                return SpotifyCountryStats(
                    country_code=country_code,
                    country_name=self._country_names.get(country_code, country_code),
                    top_tracks=[],
                    total_tracks=0
                )
            
            # Obtener tracks de la primera playlist
            playlist_id = playlist_items[0].get("id")
            if not playlist_id:
                logger.warning(f"No se pudo obtener ID de playlist para {country_code}")
                return SpotifyCountryStats(
                    country_code=country_code,
                    country_name=self._country_names.get(country_code, country_code),
                    top_tracks=[],
                    total_tracks=0
                )
            
            tracks_url = f"{self.base_url}/playlists/{playlist_id}/tracks"
            tracks_params = {
                "market": country_code,
                "limit": min(limit, 50),
                "fields": "items(track(id,name,artists,album,popularity,duration_ms,explicit,preview_url))"
            }
            
            tracks_response = requests.get(tracks_url, headers=headers, params=tracks_params, timeout=30)
            tracks_response.raise_for_status()
            
            tracks_data = tracks_response.json()
            tracks = []
            
            for item in tracks_data.get("items", []):
                track_info = item.get("track")
                if track_info and track_info.get("id"):  # Verificar que el track existe
                    try:
                        track = self._parse_track(track_info)
                        tracks.append(track)
                    except Exception as e:
                        logger.warning(f"Error parseando track: {e}")
                        continue
            
            logger.info(f"Obtenidos {len(tracks)} tracks para {country_code}")
            
            return SpotifyCountryStats(
                country_code=country_code,
                country_name=self._country_names.get(country_code, country_code),
                top_tracks=tracks,
                total_tracks=len(tracks)
            )
            
        except requests.RequestException as e:
            logger.error(f"Error de request para {country_code}: {e}")
            return SpotifyCountryStats(
                country_code=country_code,
                country_name=self._country_names.get(country_code, country_code),
                top_tracks=[],
                total_tracks=0
            )
        except Exception as e:
            logger.error(f"Error inesperado para {country_code}: {e}")
            return SpotifyCountryStats(
                country_code=country_code,
                country_name=self._country_names.get(country_code, country_code),
                top_tracks=[],
                total_tracks=0
            )


class SpotifyClientFactory:
    """Factory para crear clientes de Spotify"""
    
    @staticmethod
    def create_client() -> SpotifyAPIClient:
        """Crea un cliente de Spotify con configuración por defecto"""
        auth_strategy = ClientCredentialsAuth(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret
        )
        return SpotifyAPIClient(auth_strategy)
