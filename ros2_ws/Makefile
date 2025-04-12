.PHONY: build
build:
	python3 -m colcon build --packages-select icm20948 pathfinder

.PHONY: clean
clean:
	rm -rf build install log

.PHONY: convert-bag
convert-bag:
	rosbags-convert --src pathfinder_calibrate.bag --dst pathfinder_calibrate01.bag

.PHONY: run-kalibr
run-kalibr:
	docker run -it --rm -v $(pwd)/../kalibr:/kalibr kalibr
