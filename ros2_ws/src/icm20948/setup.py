from setuptools import setup, find_packages
import os
import subprocess

def build_c_library():
    # Run make to build the C library
    subprocess.check_call('make', cwd=os.path.dirname(__file__))

# Build C dependencies before installing Python package
# build_c_library()

setup(
    name='icm20948',
    version='0.0.1',
    packages=find_packages(),
    package_data={
        'icm20948': ['*.so'],  # Include compiled .so file
    },
    install_requires=[],
    author='Anatolii Stehnii',
    author_email='anatolii.stehnii@gmail.com',
    description='Python wrapper for ICM20948 IMU sensor',
    license='MIT',
)
