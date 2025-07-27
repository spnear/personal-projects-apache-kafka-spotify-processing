#!/usr/bin/env python3
"""
Script de ejecución del productor de Spotify
"""
import os
import sys

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.kafka_producer_spotify.main import main

if __name__ == "__main__":
    main()
