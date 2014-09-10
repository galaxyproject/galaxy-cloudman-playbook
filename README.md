Role for building a base image for CloudMan
===========================================

This playbook is used to build a base machine image for [CloudMan][cloudman]
and [Galaxy on the Cloud][goc].

To build an image, make sure the default values provided in the
`roles/cloudman_image/defaults` directory suite you. Next, create a copy of
`inventory/cloud-builder.sample` as `inventory/cloud-builder`, launch a new
instance (this role has been developed and tested on Ubuntu 14.04) and set the
instance IP address for `cloudman-image` host in `cloud-builder`. Finally, run
the playbook with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "cloudman" --extra-vars vnc_password=<choose a password> --extra-vars cm_cleanup=true

On average, the build time takes about 30 minutes. *Note that after the playbook
has run to completion, you will no longer be able to ssh into the instance!* If
you still need to ssh, omit `--extra-vars cm_cleanup=true` from the above command.
Before creating the image, however, you must rerun the playbook with that flag set.

[cloudman]: http://usecloudman.org/
[goc]: https://wiki.galaxyproject.org/Cloud
