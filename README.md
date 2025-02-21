# image-build

A wrapper around various `buildah` commands that makes creating images in layers easier.
There are two supported modes at the moment, a "base" type layer and an "ansible" type layer

# Running

The recommended way to run `image-build` is through the container as it avoids any Python dependency troubles.

## Container

The supported way for running the container is via [Podman](https://podman.io/).
To build an image using the container, the config file needs to be mapped into the container, as well as the FUSE filesystem device:

```
podman run \
  --rm \
  --device /dev/fuse \
  -v /path/to/config.yaml:/home/builder/config.yaml \
  ghcr.io/openchami/image-build:latest \
  image-build --config config.yaml
```

If the config.yaml pushes to S3, specify the credentials by adding `-e S3_ACCESS=<s3-user>` and `-e S3_SECRET=<s3-password>` to the command above. See [S3](#s3) below.

## Bare Metal

> [!WARNING]
> Python >= 3.7 is required!

Install the Python package dependencies:
```
pip install -r requirements.txt
```

Run the tool:
```
image-build --config /path/to/config.yaml
```

# Building Container

From the root of the repository:
```
buildah bud -t ghcr.io/openchami/image-buildi:latest -f src/dockerfiles/Dockerfile .
```

# Configuration

## Base Type Layer

The premise here is very simple. The `image-build` tool builds a base layer by starting a container, then using the provided package manager to install repos and packages. There is limited support for running basic commands inside the container. These settings are provided in a config file and command line options

An example config file:
```
repos:
  - alias: 'Rock_BaseOS'
    url: 'http://dl.rockylinux.org/pub/rocky/8/BaseOS/x86_64/os'
  - alias: 'Rock_AppStream'
    url: 'http://dl.rockylinux.org/pub/rocky/8/AppStream/x86_64/os'
  - alias: 'Rock_PowerTools'
    url: 'http://dl.rockylinux.org/pub/rocky/8/PowerTools/x86_64/os'
  - alias: 'Epel'
    url: 'http://dl.fedoraproject.org/pub/epel/8/Everything/x86_64/'

package_groups:
  - 'Minimal Install'
  - 'Development Tools'

packages:
  - kernel
  - wget

cmds:
  - cmd: 'echo hello'
```

Then you can use this config file to build an "base" layer:
```
image-build --name base-os \
    --config base.yaml \
    --pkg-manager dnf \
    --parent scratch \
    --publish-tags 8.8 \
    --layer-type base
```

You can then build on top of this base os with a new config file, just point the `--parent` flag at the base os container image

See [Publishing Images](#publishing-images) below for more explanation on how `image-build` publishes images.


## Ansible Type Layer

You can also run an ansible playbook against a buildah container. This type using the Buildah connection plugin in ansible to treat the container as a host.
```
image-build \
    --name ansible-layer \
    --parent base-os \
    --groups compute \
    --pb playbook.yaml \
    --inventory my_inventory/ \
    --publish-tags v1 \
    --layer-type ansible
```

This requires the parent to be setup to run ansible tasks


# Publishing Images

The `image-build` tool can publish the image layers to a few kinds of endpoints

## S3

Using the `--publish-s3 <URL>` flag or `publish-s3` config key will push to an S3 endpoint.

Credentials for S3 can be set via environment variables. Use `S3_ACCESS` for the username and `S3_SECRET` for the password.

## Registry

Using the `--publish-registry <URL>` flag or `publish-registry` config key will push to the passed registry base URL (not including image tag). Use `--registry-opts-push`/`registry-opts-push` to specify flags/args to pass to the `buildah push` command to push.

There is an equivalent flag/config option `--registry-opts-pull`/`registry-opts-pull` whose value is passed to the `buildah push` command to pull the parent OCI image.

## Local

Using the `--publish-local` flag or `publish-local` config key will push the resulting OCI image to the local podman registry using `buildah commit`.
