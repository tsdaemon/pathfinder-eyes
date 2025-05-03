#!/bin/bash
set -a
source install/setup.bash
mkdir -p log tmp
supervisord -n
