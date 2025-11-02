"""Simulator module for EEG and drone data."""

from .eeg_simulator import EEGSimulator, simulate_eeg_stream
from .drone_simulator import DroneSimulator, simulate_drone_stream

__all__ = [
    "EEGSimulator",
    "DroneSimulator",
    "simulate_eeg_stream",
    "simulate_drone_stream"
]

