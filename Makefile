DOCKER_IMAGE := fopina/semgrep-on-sonar
DOCKER_VERSION := 1
DOCKER_PLATFORMS := linux/amd64,linux/arm64

build:
	docker buildx build \
				  --platform $(DOCKER_PLATFORMS) \
				  --build-arg VERSION=$(DOCKER_VERSION) \
				  -f docker/Dockerfile \
				  $(EXTRA) \
				  .

local:
	make build EXTRA="--load -t $(DOCKER_IMAGE):local" DOCKER_PLATFORMS=linux/arm64

push: CNT = $(shell git rev-parse --short HEAD)
push:
	make build EXTRA="--push -t $(DOCKER_IMAGE):$(DOCKER_VERSION) -t $(DOCKER_IMAGE):$(DOCKER_VERSION)-$(CNT)"

latest: push
	make build EXTRA="--push -t $(DOCKER_IMAGE):latest"
