from setuptools import find_packages, setup

package_name = "pico_control"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pymavlink"],
    zip_safe=True,
    maintainer="anatolii",
    maintainer_email="tsdaemon@gmail.com",
    description="",
    license="",
    entry_points={
        "console_scripts": [
            "vel_to_mavlink = pico_control.vel_to_mavlink:main",
        ],
    },
)
