# Examples
Below is a step-by-step tutorial on how to build your first image with the `image-build` tool. The tutorial assumes you are starting from the base of this repository

## Dependencies
`buildah`
`podman`

## Building Container Image
First we will create a container image that will be use to run the `image-build` tool. The dockerfile we will be using for this is specified under the path `dockerfiles/dnf/Dockerfile_live`
```
buildah bud -t image-builder-test -f ../dockerfiles/dnf/Dockerfile_live
```

Onced Finished, you should see the image listed when running the following command
```
buildah images
```

From here, you can run the container image using podman by executing the following command
```
podman run \
        --name image-build-test \
        --rm \
        --device /dev/fuse \
        -it \
        -v $PWD:/data/configs:ro \
	image-builder-test
	bash
```

# Base Layer

Use the `base.yaml` config file to build a "base" layer. We will be running the `image-build` tool with buildah unshare:
``` bash
buildah unshare bash -c "image-build --config /data/configs/base.yaml"
```

You can then build on top of this base os with a new config file, just point the `--parent` flag at the base os container image


# Ansible Type Layer
You can also run an ansible playbook against a buildah container.  Using the Buildah connection plugin in ansible, the parent container as a host. Use the `compute-ansible.yaml` config file to build an "ansible" layer:
```bash
buildah unshare bash -c "image-build --config /data/configs/compute-ansible.yaml"
```

This requires the parent to be setup to run ansible tasks. In our example, the "base" layer created by `base.yaml` is.


# Publish images
The `image-build` tool can publish the image layers to a few kinds of endpoints. In the examples above, both the "base" layer and the "ansible" layer are published local. Lets look at the 3 publishing options `image-build` contains:

### S3
using the `--publish-s3 <URL>` option will push to an s3 endpoint defined in `publish_dest`
You can also set the access and secret values with `S3_ACCESS` and `S3_SECRET` respectively

### Registry
Using the `--publish-registry <URL>` option will push to a docker registry defined in `publish_dest`. You can point to a certs directory by setting `REGISTRY_CERTS_DIR`.

### Local
Using the `--publish-local` option will squash the layer and copy it to buildah's local image destination .
