"""
FastAgent Streamlit Interface
============================

Interfaz web para el sistema FastAgent de procesamiento multi-agente.
"""

__version__ = "0.1.0"
__author__ = "Pablo Toledo"

from .app import main, run_streamlit

__all__ = ["main", "run_streamlit"]