# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
#FROM python:3.9.13
FROM ubuntu:22.04
ARG arg

# Update apt cache, install packages, remove apt cache
RUN apt -y update && \
	apt -y install \
	python3 python3-pip \
	vim \
	net-tools \
	curl \
	telnet \
	less \
	openssh-client \
	dos2unix \
	jq \
	&& rm -rf /var/lib/apt/lists/*

# Install from Pipfile
COPY Pipfile ./
RUN pip3 install pipenv
#RUN pipenv install --system  --skip-lock
RUN if [ -z "$arg" ]; \
	then echo "Building prod..." && \
	pipenv install --system  --skip-lock; \
	else \
	echo "Building dev..."; \
	pipenv install --system  --skip-lock -d; \
	fi

# Copy source and create link under PATH
RUN mkdir /app
COPY src/ /app
#RUN ln -s /app/checkmk.py /usr/local/bin/checkmk

WORKDIR /app

#Env
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
# TODO: Missing timezone setting

#App env
ENV SITE_NAME=main
ENV REST_URL=https://checkmk.domain.com/main/check_mk/api/1.0
ENV CAFILE=/app/config/myca.pem
ENV USER=automation
ENV TOKENF=/app/config/secret/secret.token

#CMD is the command the container executes by default when you launch the built image. A Dockerfile will only use the final CMD defined. The CMD can be overridden when starting a container with docker run $image $other_command.
#ENTRYPOINT is also closely related to CMD and can modify the way a container starts an image.
#CMD ["checkmk"]
CMD ["fab", "-l"]
