"""Lightweight simulation for the autonomous cabbage harvester experiment.

This module approximates closed-loop motion across multiple terrains and RPM
regimes, emitting synthetic telemetry aligned with the experiment plan.
It is intentionally dependency-light so it can run inside the provided
``environment.yml`` conda environment.
"""
from __future__ import annotations

import argparse
import math
import pathlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


@dataclass
class TerrainProfile:
    """Defines surface-dependent dynamics and noise."""

    name: str
    friction_coeff: float  # higher -> slower acceleration
    vibration_rms: float  # baseline vibration magnitude (m/s^2)
    roughness: float  # additional process noise on acceleration


@dataclass
class RpmProfile:
    """Target RPM regime mapped to wheel linear speed."""

    name: str
    wheel_rpm: float
    target_speed_mps: float
    controller_tau: float  # time constant for first-order speed response


@dataclass
class SimulationResult:
    """Container for time-series telemetry and measurement snapshots."""

    telemetry: pd.DataFrame
    measurement_points: pd.DataFrame

    def save(self, output: pathlib.Path) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix == ".parquet":
            self.telemetry.to_parquet(output)
        else:
            self.telemetry.to_csv(output, index=False)

        # Store measurement point slices alongside the main log for quick lookups.
        measurement_path = output.with_name(output.stem + "_measurements" + output.suffix)
        if output.suffix == ".parquet":
            self.measurement_points.to_parquet(measurement_path)
        else:
            self.measurement_points.to_csv(measurement_path, index=False)


def seed_everything(seed: Optional[int]) -> None:
    if seed is None:
        return
    np.random.seed(seed)


def simulate_leg(
    terrain: TerrainProfile,
    rpm_profile: RpmProfile,
    segment_length_m: float,
    measurement_distances: Iterable[float],
    dt: float,
    seed: Optional[int] = None,
) -> SimulationResult:
    """Simulate a single 20 m traversal with coarse vehicle dynamics.

    The model is intentionally simple (first-order speed response with friction
    and vibration noise) but captures distinct behaviors per terrain and RPM
    regime. Telemetry includes speed, acceleration, vibration, and control
    error traces at 20 Hz by default.
    """

    seed_everything(seed)
    measurement_distances = sorted(measurement_distances)

    distance = 0.0
    velocity = 0.0
    time_s = 0.0

    rows: List[Dict[str, float]] = []
    measurement_rows: List[Dict[str, float]] = []

    next_measure_idx = 0
    max_steps = int(math.ceil(segment_length_m / (rpm_profile.target_speed_mps * dt)) * 3)

    while distance < segment_length_m and len(rows) < max_steps:
        speed_error = rpm_profile.target_speed_mps - velocity
        # First-order response toward target speed with frictional drag.
        accel_command = (speed_error / rpm_profile.controller_tau) - (
            terrain.friction_coeff * velocity
        )

        # Inject terrain-dependent disturbance and vibration.
        disturbance = np.random.normal(scale=terrain.roughness)
        vibration = np.random.normal(scale=terrain.vibration_rms)
        acceleration = accel_command + disturbance

        velocity = max(0.0, velocity + acceleration * dt)
        distance += velocity * dt
        time_s += dt

        rows.append(
            {
                "time_s": time_s,
                "distance_m": distance,
                "speed_mps": velocity,
                "accel_mps2": acceleration,
                "vibration_mps2": vibration,
                "speed_error_mps": speed_error,
                "terrain": terrain.name,
                "rpm_profile": rpm_profile.name,
            }
        )

        # Capture the nearest data point at each requested measurement distance.
        if (
            next_measure_idx < len(measurement_distances)
            and distance >= measurement_distances[next_measure_idx]
        ):
            measurement_rows.append(rows[-1].copy())
            next_measure_idx += 1

    telemetry_df = pd.DataFrame(rows)
    measurement_df = pd.DataFrame(measurement_rows)
    return SimulationResult(telemetry=telemetry_df, measurement_points=measurement_df)


def default_terrains() -> Dict[str, TerrainProfile]:
    return {
        "cabbage_field": TerrainProfile("cabbage_field", friction_coeff=0.28, vibration_rms=0.6, roughness=0.35),
        "loose_soil": TerrainProfile("loose_soil", friction_coeff=0.22, vibration_rms=0.45, roughness=0.22),
        "paved": TerrainProfile("paved", friction_coeff=0.12, vibration_rms=0.12, roughness=0.08),
    }


def default_rpm_profiles(wheel_radius_m: float = 0.15) -> Dict[str, RpmProfile]:
    # Convert RPM to linear speed: v = (rpm * 2πr) / 60.
    rpm_map = {
        "low": 40,
        "medium": 90,
        "high": 140,
    }
    rpm_profiles = {}
    for name, rpm in rpm_map.items():
        target_speed = (rpm * 2 * math.pi * wheel_radius_m) / 60.0
        # Faster regimes respond more slowly because of higher vibration and controller saturation.
        tau = 0.8 if name == "low" else 1.1 if name == "medium" else 1.4
        rpm_profiles[name] = RpmProfile(name=name, wheel_rpm=float(rpm), target_speed_mps=target_speed, controller_tau=tau)
    return rpm_profiles


def run_matrix(
    terrains: Dict[str, TerrainProfile],
    rpm_profiles: Dict[str, RpmProfile],
    segment_length_m: float,
    measurement_distances: Iterable[float],
    dt: float,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Run the full environment × RPM matrix and return concatenated telemetry."""

    logs: List[pd.DataFrame] = []
    for terrain in terrains.values():
        for rpm_profile in rpm_profiles.values():
            result = simulate_leg(
                terrain=terrain,
                rpm_profile=rpm_profile,
                segment_length_m=segment_length_m,
                measurement_distances=measurement_distances,
                dt=dt,
                seed=None if seed is None else seed + hash((terrain.name, rpm_profile.name)) % 10000,
            )
            # Tag measurement points for post-processing.
            result.measurement_points["is_measurement_point"] = True
            logs.append(result.telemetry)
            logs.append(result.measurement_points)
    return pd.concat(logs, ignore_index=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic traversal simulation for cabbage harvester trials.")
    parser.add_argument(
        "--segment-length",
        type=float,
        default=20.0,
        help="Traversal distance in meters for each terrain (default: 20 m)",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.05,
        help="Simulation timestep in seconds (default: 0.05s => 20 Hz)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("data/simulated_traversals.parquet"),
        help="Path to write telemetry parquet/csv (default: data/simulated_traversals.parquet)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (parquet or csv). Overrides the extension if necessary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_path = args.output
    if args.format == "csv" and output_path.suffix != ".csv":
        output_path = output_path.with_suffix(".csv")
    elif args.format == "parquet" and output_path.suffix != ".parquet":
        output_path = output_path.with_suffix(".parquet")

    terrains = default_terrains()
    rpm_profiles = default_rpm_profiles()

    measurements = [1, 3, 5, 7, 10]
    telemetry = run_matrix(
        terrains=terrains,
        rpm_profiles=rpm_profiles,
        segment_length_m=args.segment_length,
        measurement_distances=measurements,
        dt=args.dt,
        seed=args.seed,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "parquet":
        telemetry.to_parquet(output_path)
    else:
        telemetry.to_csv(output_path, index=False)

    print(f"Saved synthetic telemetry to {output_path.resolve()}")
    print(f"Rows: {len(telemetry)} across {len(terrains)} terrains × {len(rpm_profiles)} RPM regimes")


if __name__ == "__main__":
    main()
