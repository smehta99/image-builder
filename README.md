# image-build

A wrapper around various `buildah` commands that makes creating images in layers easier.
There are two supported modes at the moment, a "base" type layer and an "ansible" type layer

# Setup

> [!NOTE]
> Python >= 3.7 is required.

```
pip install -r requirements.txt
```

# Base Type layer
The premise here is very simple. The `image-build` tool builds a base layer by starting a container, then using the provided package manager to install repos and packages. There is limited support for running basic commands inside the container. These settings are provided in a config file and command line options

An example config file:
```
repos:
  - alias: 'Rock_BaseOS'
    url: 'http://<repo_server>/repo/pub/rocky/8/BaseOS/x86_64/os'
  - alias: 'Rock_AppStream'
    url: 'http://<repo_server>/repo/pub/rocky/8/AppStream/x86_64/os'
  - alias: 'Rock_PowerTools'
    url: 'http://<repo_server>/repo/pub/rocky/8/PowerTools/x86_64/os'
  - alias: 'Epel'
    url: 'http://<repo_server>/repo/pub/rocky/epel/8/Everything/x86_64/'

package_groups:
  - 'Minimal Install'
  - 'Development Tools'

packages:
  - kernel
  - wget

cmds:
  - 'echo hello'
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


# Ansible Type Layer
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


# Publish images
The `image-build` tool can publish the image layers to a few kinds of endpoints

## S3
using the `--publish-s3 <URL>` option will push to an s3 endpoint defined in an ENV variable: `S3_URL`.
You can also set the access and secret values with `S3_ACCESS` and `S3_SECRET` respectively

## Registry
Using the `--publish-registry <URL>` option will push to a docker registry defined in an ENV variable: `REGISTRY_EP`. You can point to a certs directory by setting `REGISTRY_CERTS_DIR`.

## Local
Using the `--publish-local` option will squash the layer and copy it to a destination defined in `--publish-dest`.
