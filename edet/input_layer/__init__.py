"""Input Layer: ingestion and dataset profiling."""

from edet.input_layer.loaders import load_dataset
from edet.input_layer.profiler import create_profile

__all__ = ["load_dataset", "create_profile"]
