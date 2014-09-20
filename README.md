Role for building a base image for CloudMan
===========================================

This playbook is used to build the components required to run
[CloudMan][cloudman] and [Galaxy on the Cloud][goc]. The playbook is
used by th [Galaxy project][gp] itself and is intended for anyone
wanting to deploy their own instance, either on a public or private
cloud.

There are several roles contained in this playbook; the roles manage
the build process of different components. To get a complete built,
you will first need to build the machine image. Then launch an instance
of that machine image and build the rest of the componts off of it.
More insturctions about the build process can be found [here][building].

Machine Image
-------------
To build an image, make sure the default values provided in the
`roles/cloudman_image/defaults` directory suite you. Next, create a copy of
`inventory/cloud-builder.sample` as `inventory/cloud-builder`, launch a new
instance (this role has been developed and tested on Ubuntu 14.04) and set the
instance IP address for `cloudman-image` host in `cloud-builder`. Finally, run
the role with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "cloudman" --extra-vars vnc_password=<choose a password> --extra-vars cm_cleanup=yes

On average, the build time takes about 30 minutes. *Note that after the playbook
has run to completion, you will no longer be able to ssh into the instance!* If
you still need to ssh, omit `--extra-vars cm_cleanup=yes` from the above command.
Before creating the image, however, you must rerun the playbook with that flag set.

Galaxy File System (galaxyFS)
-----------------------------
Launch an instance of the machine image built in the previous step and attach a
new volume to it. Create a (`XFS`) file system on that volume and mount it
(under `/mnt/galaxy`). Note that this can also be done from the CloudMan's
Admin page by adding a new-volume-based file system. Set the lauched instance
IP in `inventory/cloud-builder` and run the role with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "galaxyFS" --extra-vars psql_galaxyftp_password=<choose a password>

After the run has completed, stop any services that might still be using the
file system, unmount the file system and create a snapshot of it from the Cloud's
console.

[cloudman]: http://usecloudman.org/
[goc]: https://wiki.galaxyproject.org/Cloud
[gp]: http://galaxyproject.org/
[building]: https://wiki.galaxyproject.org/CloudMan/Building
