# Docker for work with Check MK
Author: Blaž Poje

Description: A docker that uses Python & REST API to connect to remote Check MK server an perform operations.

Prebuild images are available on [Docker Hub](https://hub.docker.com/r/bpoje/checkmk-rest/tags).

## Build docker


Build and run dev:
```
$ make builddev
$ make rundev
```

Build prod:
```
$ make buildprod
$ make run
```

Build both:
```
$ make
```

## Configure docker

Config in volume:
```
-v $(shell pwd)/config:/app/config
```

```
$ ls -Alh config/
    total 0
    drwx------ 2 user user   26 Jul 30 17:48 secret

$ ls -Alh config/secret/
    total 4.0K
    -rw------- 1 user user 21 Jul 30 17:34 secret.token

$ cat config/secret/secret.token
    xxmykey1xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Environment variables:
```
#Env
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

#App env
ENV SITE_NAME=main
ENV REST_URL=https://checkmk.domain.com/main/check_mk/api/1.0
ENV CAFILE=/app/config/myca.pem
ENV USER=automation
ENV TOKENF=/app/config/secret/secret.token
```

## Use docker
```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2
    Available tasks:
    
      activate (a)                    check mk: activate
      create-host (c)                 check mk: create host
      delete-host (d)                 check mk: delete host
      discover (di)                   check mk: discover services on check mk hosts
      discover-fixall (df)            check mk: Fix all services on check mk hosts
      get-all-folders (gaf)           check mk: lists subfolders (and the hosts in
                                      subfolders) of folder x. It won't show the files
                                      that are in folder x.
      get-all-hosts (ah)              check mk: get all hosts in json
      get-all-hosts-in-folder (ahf)   check mk: get all hosts in folder
      get-all-tag-group (atg)         Iterate over all tag groups and their possible
                                      values (enums) in CSV form
      get-all-tags (at)               Iterate over all hosts and extract their tags in
                                      CSV form
      get-etag (etag)                 check mk: get etag value (value that changes on
                                      every modification of check mk host)
      get-host (h)                    check mk: get host
      get-tag-group (gtg)             check mk: Get a host tag group with all its values
      get-tag-hist (th)               Get all tag groups and their possible values and
                                      left join them with hosts that use them. In CSV
                                      form
      remove-host-ip (ri)             check mk: remove host ip
      remove-host-tag (rt)            check mk: remove host tag
      test (tes)                      test
      update-host (u)                 check mk: update host
      update-host-ip (ui)             check mk: update host ip
      update-host-tag (ut)            check mk: update host tag
```

Call docker with set envs:
```
$ docker run -it --rm -e REST_URL="https://checkmk.domain.com/main/check_mk/api/1.0" -e SITE_NAME="main" -e CAFILE="/app/config/CA.pem" -e TOKENF="/app/config/secret/secret.token" -v "$(pwd)/config":/app/config checkmk-rest:1.2 /bin/bash
```

Get info about host:
```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2 fab get-host -h myhost
```

Get info about host and use bash command jq:
```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2 fab get-host -h myhost | jq .id
    "myhost"
```

Update host IP:
```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2 fab update-host-ip -h myhost -i "10.5.6.3" -d
    ...
```

Display help for activate function:
```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2 fab -h activate
    Usage: fab [--core-opts] activate [--options] [other tasks here ...]
    
    Docstring:
      check mk: activate
    
    Options:
      -d, --doit
      -f, --force-foreign-changes
```

Activate changes on Check MK:

```
$ docker run -it --rm -v "$(pwd)/config":/app/config checkmk-rest:1.2 fab activate -d -f
```

