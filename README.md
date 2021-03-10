
# Description

This is an Ansible script that should help you build & install ros2 on multiple devices (Raspberry Pi) with ***just one command***.

# What is does?

It should do exactly those steps: https://docs.ros.org/en/eloquent/Installation/Linux-Development-Setup.html

But before it starts it changes the size of swap and after the build it changes it back.


# Before you run the script

Please make sure that your devices are ready with enough free space (~4GB).
1. SSH is enabled,
2. keys are generated and distributed, or use password,
3. Ansible is installed on you computer,
4. Devices are up and running,
5. Read known issues.

_(I won't cover these topics they could be extensive, please use search engine.)_

# How to

Just download those files, change at least the inventory file.

And run it with following command:
```
ansible-playbook -i inventory.yml main.yml
```

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
