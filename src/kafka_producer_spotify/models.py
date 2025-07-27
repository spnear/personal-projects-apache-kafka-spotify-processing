"""
Modelos de datos para las estadísticas de Spotify
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SpotifyTrack(BaseModel):
    """Modelo para una canción de Spotify"""
    track_id: str = Field(..., description="ID único de la canción")
    name: str = Field(..., description="Nombre de la canción")
    artist: str = Field(..., description="Artista principal")
    album: str = Field(..., description="Nombre del álbum")
    popularity: int = Field(..., ge=0, le=100, description="Popularidad de 0 a 100")
    duration_ms: int = Field(..., description="Duración en milisegundos")
    explicit: bool = Field(..., description="Si la canción es explícita")
    preview_url: Optional[str] = Field(None, description="URL de preview")


class SpotifyCountryStats(BaseModel):
    """Modelo para estadísticas de un país"""
    country_code: str = Field(..., description="Código ISO del país")
    country_name: str = Field(..., description="Nombre del país")
    top_tracks: List[SpotifyTrack] = Field(..., description="Top tracks del país")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la consulta")
    total_tracks: int = Field(..., description="Total de tracks obtenidos")


class SpotifyMessage(BaseModel):
    """Modelo para el mensaje que se envía a Kafka"""
    message_id: str = Field(..., description="ID único del mensaje")
    country_stats: SpotifyCountryStats = Field(..., description="Estadísticas del país")
    producer_info: Dict[str, Any] = Field(..., description="Información del productor")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
