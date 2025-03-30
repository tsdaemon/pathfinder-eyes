.PHONY: build
build:
	python3 -m colcon build --packages-select icm20948 pathfinder

.PHONY: clean
clean:
	rm -rf build install log

.PHONY: convert_bag
convert_bag:
	rosbags-convert --src pathfinder_calibrate.bag --dst pathfinder_calibrate01.bag