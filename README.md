
# Description

This is an Ansible script that should help you build & install ros2 on multiple devices (Raspberry Pi) with ***just one command***.

# What it is does?

It should do exactly those steps: https://docs.ros.org/en/eloquent/Installation/Linux-Development-Setup.html

But before it starts it changes the size of swap and after the build it changes it back.


# Before you run the script

Please make sure that your devices are ready with enough free space (~4GB).
1. SSH is enabled,
2. Keys are generated and distributed, or use password,
3. Ansible is installed on you computer,
4. Devices are up and running,
5. Read known issues,
6. Update the inventory.yml file.

_(I won't cover these topics they could be extensive, please use search engine.)_

# How to

Just checkout(download) those files, change at least the inventory file.

And run it with following command:
```
ansible-playbook -i inventory.yml main.yml
```
or with passing password (requires: sshpass package)
```
ansible-playbook -i inventory.yml main.yml -k
```
With those two variables you can change the release of ros2:
- ros2_distro
- ros2_repo_url

See default.yml for details.

# Experiment planning & analysis

For data-heavy field experiments (e.g., autonomous cabbage collection), a reproducible workflow is documented in `docs/experiment_plan.md`. It covers terrain matrix, RPM regimes, measurement points, and a simulation-to-real pipeline using 3D Gaussian Splatting.

## Lightweight simulation (no ROS required)

Generate synthetic traversals across the full terrain × RPM matrix using the included Python model:

```
python simulations/cabbage_simulation.py --output data/simulated_traversals.parquet --segment-length 20 --dt 0.05 --seed 42
```

- Outputs parquet (default) or CSV if `--format csv` is provided.
- Telemetry columns cover distance, speed, acceleration, vibration, and control error at 20 Hz, with flags on the official measurement points (1 m, 3 m, 5 m, 7 m, 10 m).
- Use this to validate analysis notebooks and plotting before connecting to ROS 2 bags.

To process logs and train perception models, create the dedicated conda environment:

```
conda env create -f environment.yml
conda activate cabbage-collector
```

Use this environment for ROS 2 bag parsing, visualization, and AI/3D reconstruction tooling.


# Tested

I tested my self on my Raspberry 3 with fresh image of Raspberry Pi OS Lite version from January 11th 2021.
I install Foxy and Eloquent several times.

# Known issues

1) Several times I had an issue installing those two packages
      - python3-colcon-common-extensions
      - python3-vcstool
 I could install them manually (not desired way). But sometimes I just rerun the script and it worked. Not solved yet.
 
2) I ament RVIZ since I was not able to solve errors from the compiler. So it's not there.

3) (solved) I added -latomic to rcutils/CmakeLists.txt to be able to compile it. see workarounds.yml for details.

4) Watch your devices for overheating during the compilation, use cooler.


# Contribute

Please help me make it better. I know it's not much but I sincerely hope it's a good start.
