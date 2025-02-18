# Name of the Docker image.
IMAGE_NAME = latency-check

# Build the Docker image.
.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

# Run the container, mounting the current directory into /app so that the log file appears locally.
.PHONY: run
run:
	docker run --rm \
		-v $(PWD):/app \
		-v /etc/hostname:/host_hostname:ro \
		-v /etc/localtime:/etc/localtime:ro \
		-v /etc/timezone:/etc/timezone:ro \
		$(IMAGE_NAME)


.PHONY: build-graph
build-graph:
	docker build -t $(IMAGE_NAME)-graph -f Dockerfile.graph .

.PHONY: run-graph
run-graph:
	docker run --rm \
		-p 8888:8888 \
		-v $(PWD):/home/jovyan/work/ \
		-v /etc/hostname:/host_hostname:ro \
		-v /etc/localtime:/etc/localtime:ro \
		-v /etc/timezone:/etc/timezone:ro \
		$(IMAGE_NAME)-graph

.PHONY: exportpdf
exportpdf:
	mkdir -p reports && chmod 777 reports && \
	docker run --rm -it \
		-p 8888:8888 \
		-v $(PWD):/home/jovyan/work/ \
		-v /etc/hostname:/host_hostname:ro \
		-v /etc/localtime:/etc/localtime:ro \
		-v /etc/timezone:/etc/timezone:ro \
		-e PYDEVD_DISABLE_FILE_VALIDATION=1 \
		$(IMAGE_NAME)-graph \
		jupyter nbconvert --execute --to pdf LogGraph.ipynb  --output-dir=/home/jovyan/work/reports

