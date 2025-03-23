from setuptools import setup, find_packages, Extension
import os
import subprocess

icm20948_module = Extension(
    'icm20948.ICM20948',                # Module path
    sources=['icm20948/ICM20948.c'],    # C source file(s)
    include_dirs=['icm20948'],  # or wherever the header lives
    extra_compile_args=['-fPIC', '-std=gnu99'],
    extra_link_args=['-lm'],
)


setup(
    name='icm20948',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[],
    ext_modules=[icm20948_module],
    author='Anatolii Stehnii',
    author_email='anatolii.stehnii@gmail.com',
    description='Python wrapper for ICM20948 IMU sensor',
    license='MIT',
)
