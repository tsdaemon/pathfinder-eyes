from setuptools import setup

package_name = "supervisord_bridge"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="anatolii",
    maintainer_email="tsdaemon@gmail.com",
    description="Bridge package for supervisord communication",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "supervisord_bridge = supervisord_bridge.supervisord_bridge_node:main",
            "watchdog = supervisord_bridge.watchdog_node:main",
        ],
    },
)
