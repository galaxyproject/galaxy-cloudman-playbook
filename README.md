A playbook for building the *Galaxy on the Cloud*
=================================================

This [Ansible][ansible] playbook is used to build the components required to run
[CloudMan][cloudman], [Galaxy on the Cloud][goc], or Galaxy Server. The playbook is
used by the [Galaxy project][gp] itself and is intended for anyone
wanting to deploy their own instance of the listed platforms.

There are several roles contained in this playbook; the roles manage
the build process of different components:
 * *CloudMan*: you only need to build the Machine Image
 * *Galaxy on the Cloud*: you need to build the Machine Image first, then the galaxyFS
 * *Galaxy Server*: you only need to build the Galaxy Server
 * *Galaxy Tools*: see the `scripts` directory

Additional instructions about the build process can be found [here][building].

These roles are intended to be run on a Ubuntu system.

Machine Image
-------------
To build an image, make sure the default values provided in the `group_vars/all`
and `group_vars/image-builder.yml` files suite you. Make sure to change the value
of `psql_galaxyftp_password` in `group_vars/all`! Next, create a copy of
`inventory/cloud-builder.sample` as `inventory/cloud-builder`, launch a new
instance (this role has been developed and tested on Ubuntu 14.04) and set the
instance IP address under `image-builder` host group in the `cloud-builder` file.
Finally, run the role with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "machine-image" --extra-vars vnc_password=<choose a password> --extra-vars cleanup=true

On average, the build time takes about 30 minutes. *Note that after the playbook
has run to completion, you will no longer be able to ssh into the instance!* If
you still need to ssh, set `--extra-vars cleanup=false` in the above command.
Before creating the image, however, you must rerun the playbook with that flag
set to `true`.

### Customizing
A configuration file exposing adjustable options is available under
`group_vars/image-builder.yml`. Besides allowing you to set some
of the image configuration options, this file allows you to easily control which
steps of the image building process run. This can be quite useful if a step fails
and you want to rerun only it or if you're just trying to run a certain steps.
Common variables for all the roles in the playbook are stored in `group_vars/all`.

Galaxy File System (galaxyFS)
-----------------------------
Launch an instance of the machine image built in the previous step and attach a
new volume to it. Create a (`XFS`) file system on that volume and mount it
(under `/mnt/galaxy`). Note that this can also be done from the CloudMan's
Admin page by adding a new-volume-based file system. Change the value
of `psql_galaxyftp_password` in `group_vars/all` and set the launched instance
IP in `inventory/cloud-builder` under `galaxyFS-builder` host group and run the
role with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "galaxyFS"

After the run has completed (typically ~15 minutes), you can start the Galaxy
application by hand and install desired tools via the Tool Shed. To start Galaxy,
change into the `galaxy` user and from the `galaxy_server_dir` (e.g.,
*/mnt/galaxy/galaxy-app*) just run `sh run.sh`. Take a look at the `scripts`
directory in this repository for an automated method of installing the tools.

Once the tools have been installed, you need to create a snapshot of the file
system. Before doing so, stop any services that might still be using the file
system, unmount the file system and create a snapshot of it from the Cloud's console.

### Customizing
This role requires a number of configuration options for the Galaxy application,
CloudMan application, PostgreSQL the database, as well as the glue linking those.
The configuration options have been aggregated under
`group_vars/galaxyFS-builder.yml` and represent reasonable defaults.
Keep in mind that changing the options that influence how the system is deployed
and/or managed may also require changes in CloudMan. Common variables for all the
roles in the playbook are stored in `group_vars/all`.

Galaxy Server
-------------
This role will build a standalone Galaxy Server that is configured to be
[production-ready][production]. Note that this role will install a number of system
packages, system users, as well as Galaxy-required software and configurations and
thus requires *root* access; it is best used on a dedicated system or a VM.

To run this role, you must switch to the `server` branch of the repository. The
configuration options used to setup the Server are available within the individual files
in the `group_vars` folder. Make sure to change the value of `psql_galaxyftp_password`
in `group_vars/all`! Next, create a copy of `inventory/cloud-builder.sample` as
`inventory/cloud-builder` and provide the IP address of the target machine under both
under `image-builder` and `galaxyFS-builder` host groups. Once the settings are to your
liking, run the role with

    ansible-playbook -i inventory/cloud-builder cloud.yml --tags "server"

Once the run has completed and you'd like to install Galaxy tools, take a look at the
`scripts` directory in this repository for an automated method of installing the tools.


[ansible]: http://www.ansible.com/
[cloudman]: http://usecloudman.org/
[goc]: https://wiki.galaxyproject.org/Cloud
[gp]: http://galaxyproject.org/
[building]: https://wiki.galaxyproject.org/CloudMan/Building
[production]: https://wiki.galaxyproject.org/Admin/Config/Performance/ProductionServer
