# Autonomous Cabbage Harvester Experiment Plan

## Objective
Establish a reproducible workflow that starts with ROS 2-based autonomy in simulation and ends with full-scale validation in real cabbage fields. The workflow emphasizes AI-driven perception, high-fidelity logging, and 3D Gaussian Splatting to bridge simulation and real-world deployment.

## Environments
- **Cabbage field**: Crop rows with uneven soil and foliage occlusion.
- **Loose soil path**: General off-road dirt path to stress traction and vibration robustness.
- **Paved road**: Baseline surface for calibration and speed references.

Each environment uses **20 m** traversals with identical layout and target waypoints.

## Speed Profiles
Command wheel RPMs in three regimes to exercise the controller:
- **Low**: Stable crawl for high-accuracy sensing.
- **Medium**: Nominal operating speed.
- **High**: Stress test for vibration and controller robustness.

## Measurement Points
Collect sensor ground truth and controller telemetry at path distances **1 m, 3 m, 5 m, 7 m, and 10 m** for every speed regime and environment.

## Sensors and Signals
Capture the richest possible dataset, then select features for analysis/visualization:
- **Localization**: RTK-GNSS (if available) + wheel odometry + IMU fusion.
- **Perception**: Stereo/RGB-D camera, LiDAR/solid-state depth, crop row detection masks.
- **Platform health**: Motor currents, RPM feedback, battery voltage, temperatures.
- **Dynamics**: Linear/angular velocity, accelerations, vibration spectra.
- **Environment**: Weather (temp/humidity), soil moisture if available.

## Control & Safety Targets
- Lateral/longitudinal tracking error within **±70 mm** for 95% of samples along each leg.
- Maintain **<3%** packet loss in telemetry/logging networks.
- No unsafe events: collision, rollover, or emergency stop trigger.

## Simulation-to-Real Procedure
1. **Simulation build**: Use Gazebo (or Isaac) with ROS 2 (Eloquent/Foxy) to validate autonomy stack on the three terrains. Inject noise that matches real sensors.
2. **Policy refinement**: Train/finetune perception models with domain randomization; validate closed-loop control in sim with the three RPM regimes.
3. **Data logger dry-run**: Record rosbag2 with the full sensor suite at simulated waypoints; ensure topic bandwidth and compression are acceptable.
4. **Field deployment**: Run the same launch and logging configurations on hardware; verify waypoint hitting and safety limits.
5. **Post-run checks**: Compare real vs. sim trajectories and frequency spectra to update controllers and perception thresholds.

### Lightweight simulation implementation
- A runnable Python model lives in `simulations/cabbage_simulation.py` to stress-test the terrain × RPM matrix without ROS 2 or Gazebo.
- It generates telemetry (speed, acceleration, vibration, control error) at 20 Hz for each terrain and RPM regime, tagging the official measurement points (1 m, 3 m, 5 m, 7 m, 10 m).
- Example: `python simulations/cabbage_simulation.py --output data/simulated_traversals.parquet --segment-length 20 --dt 0.05 --seed 1234`.
- Outputs are parquet or CSV (choose with `--format`) and can be ingested directly into notebooks for plotting and control tuning prior to ROS-based trials.

## Data Logging Blueprint
- **ROS 2 launch**: one command to start autonomy, safety supervisor, and `rosbag2` recording with compression (e.g., zstd).
- **Topic selection**: log raw + fused localization, camera images, LiDAR scans, control commands, motor currents/RPMs, IMU, weather/soil telemetry.
- **Metadata**: environment tag, RPM regime, run ID, waypoint timestamps, operator notes.
- **Storage**: Sync logs to a central NAS; mirror to object storage for model training.

## 3D Gaussian Splatting Pipeline
1. **Input**: Calibrated multi-view images + poses from the logged runs.
2. **Preprocess**: Undistort images, align poses to a common frame, and prune blurred frames using IMU vibration thresholds.
3. **Training**: Run Gaussian Splatting to reconstruct the field; use meshes/point clouds for ground-truth row geometry.
4. **Usage**: Validate obstacle maps, crop-row centrelines, and simulate occlusions for perception stress tests.

## Metrics & Visualization
- **Tracking**: lateral/longitudinal error at each measurement point; RMSE across 20 m.
- **Speed**: commanded vs. measured RPM, overshoot, settling time.
- **Perception**: row detection precision/recall, point cloud density per meter.
- **Comfort/robustness**: vibration RMS by axis; packet loss; CPU/GPU utilization.
- **Plots**: time-series overlays, error envelopes, terrain comparison bar charts, and 3D reconstructions.

## Conda Workflow
1. Create the analysis environment via `environment.yml` (see repository root).
2. Use Jupyter/VS Code inside the environment to explore rosbags (via `rosbag2_py`), process trajectories, and train perception models.
3. Export cleaned datasets and visualizations for reports; keep raw logs immutable.

## Roles and Responsibilities
- **Project lead**: globally coordinates methodology, data quality gates, and safety reviews.
- **AI/perception team**: maintains detection/segmentation models and 3D reconstruction pipeline.
- **Controls team**: tunes motion controller, validates RPM regimes, and enforces safety watchdogs.
- **Systems team**: maintains logging, storage, and deployment automation.

## Next Steps
- Validate the `environment.yml` on your target workstation or CI.
- Finalize ROS 2 launch files that combine autonomy + logger for both sim and field.
- Dry-run a 20 m traversal on each surface, then scale to full experimental matrix.
