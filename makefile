docker_prod := "checkmk-rest:1.2"
docker_dev := "checkmk-rest-dev:1.2"

all: buildprod builddev

run:
	docker run -it -d --rm -v $(shell pwd)/config:/app/config "$(docker_prod)" /bin/bash
rundev:
	docker run -it -d --rm -v $(shell pwd)/src:/app -v $(shell pwd)/config:/app/config "$(docker_dev)" /bin/bash
buildprod:
	docker build -t "$(docker_prod)" .
builddev:
	docker build -t "$(docker_dev)" . --build-arg arg="dev"
stop:
	docker ps | grep -i "$(docker_prod)" | awk '{print $1}' | xargs docker rm -f
stopdev:
	docker ps | grep -i "$(docker_dev)" | awk '{print $1}' | xargs docker rm -f
clean:
	docker rmi "$(docker_prod)" "$(docker_dev)"
