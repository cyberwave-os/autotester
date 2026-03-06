DOCKER_COMPOSE_TEST = docker compose -f tests/docker-compose.yml

.PHONY: test-docker-build test-docker

test-docker-build:
	$(DOCKER_COMPOSE_TEST) build

test-docker:
	$(DOCKER_COMPOSE_TEST) run --rm test
