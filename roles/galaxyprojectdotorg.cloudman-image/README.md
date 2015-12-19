This Ansible role is for building the machine image required to run CloudMan.
It is likely to be used in the context of the Galaxy on the Cloud playbook.

Requirements
------------
The role has been developed and tested on Ubuntu 14.04. It requires `sudo` access.

Dependencies
------------
This role leverages Oracle Java on the target system and uses [`smola.java` role][java]
for this purpose. It also uses [`galaxyprojectdotorg.galaxy-os` role][gos].
To satisfy these requirements it is necessary to install the required roles with
the following commands (this will download the given roles from Ansible Galaxy
and place them in `roles` subdirectory; unfortunately, Ansible does not have an
option to have this done automatically):

    $ ansible-galaxy install smola.java -p roles
    $ ansible-galaxy install galaxyprojectdotorg.galaxy-os -p roles

Role variables
--------------
All of the listed variabls are stored in `defaults/main.yml`. Check that file
for all the available variables.

Individual variables can be set or overridden by setting them directly in a
playbook for this role (see an example below for `vnc_password`). Alternatively,
they can be set by creating `group_vars` directory in the root directory of the
playbook used to execute this role and placing a file with the variables there.
Note that the name of this file must match the value of `hosts` setting in the
corresponding playbook (e.g., `image-builder` for the sample playbook provided
below).

### Required variables ###
 - `vnc_password`: a password that will be baked into the image and used as a
    bridge bewteen VNC and noVNC servers
 - `psql_galaxyftp_password`: a password that will also be baked into the image
    and allows Galaxy to authenticate FTP users

### Optional variables ###
 - `galaxy_user_name`: (default: `galaxy`) system username to be used for
    Galaxy
 - `galaxyFS_base_dir`: (default: `/mnt/galaxy`) the base path under which the
    galaxy file system will be placed
 - `galaxy_server_dir`: (default: `"{{ galaxyFS_base_dir }}/galaxy-app"`) the
    location where the Galaxy application will be placed
 - `galaxy_db_dir`: (default: `"{{ galaxyFS_base_dir }}/db"`) the location wher
    Galaxy's PostgreSQL database will be placed
 - `galaxy_db_port`: (default: `5930`) the port set for Galaxy's PostgrSQL database
 - `postgresql_bin_dir`: (default: `/usr/lib/postgresql/9.3/bin`) the path where
    PostgreSQL binary files are stored. This path will be added to `$PATH`.
 - `nginx_upload_store_path`: (default: `"{{ galaxyFS_base_dir }}/upload_store"`)
    the path to which Nginx's configuration for the `upload_store` will be set
 - `indicesFS_base_dir`: (default: `/mnt/galaxyIndices`) the path where Galaxy
    reference genomes indices will be stored. Also Galaxy Data Managers will be
    installed here (via the Tool Shed, as designed by Galaxy).
 - `cm_docker_image`: name of the Docker container to preload on the image

### Control flow variables ###
The following variables can be set to either `yes` or `no` to indicate if the
given part of the role should be executed:
 - `cm_install_packages`: (default: `yes`) install system level packages
 - `cm_venvburrito`: (default: `yes`) whether to setup virtual burrito virtual
    environment for CloudMan
 - `cm_system_environment`: (default: `yes`) setup system-level configurations
    *Note* that setting this option also requires `cm_venvburrito` to be set.
 - `cm_system_tools`: (default: `yes`) install given tools system wide
 - `cm_docker`: (default: `yes`) pull Docker containers on the image
 - `cm_install_s3fs`: (default: `yes`) whether to install S3FS or not
 - `cm_configure_nginx`: (default: `yes`) whether to configure Nginx
 - `cm_install_proftpd`: (default: `yes`) whether to install ProFTPd server
 - `cm_install_novnc`: (default: `no`) whether to install and configure VNC and
    noVNC bridge for in-browser remote desktop. *Note* that there are issues
    with setting this on AWS due to how AWS exposes graphics card hardware.
 - `cm_install_r_packages`: (default: `yes`) whether to install R and Bioconductor
    packages
 - `cleanup`: (default: `no`) whether to clean up the instance and make it ready
    for bundling into an image. This must be set before an image is created!
 - `only_cleanup`: (default: `no`) when set, only the cleanup tasks will run and
    no other. This is primarily intended to be set as a command line variable.

Example playbook
----------------
To use the role, it is necessary to launch a cloud instance, create a `hosts`
file that contains access information for the instance, for example:

    [image-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Next, set any variables as desired and place the role into a playbook file
(e.g., `playbook.yml`). This playbook assumes the role has been placed into
`roles/galaxyprojectdotorg.cloudman-image` directory:

    - hosts: image-builder
      sudo: yes
      roles:
        - galaxyprojectdotorg.cloudman-image
          vnc_password: <some_password>
          psql_galaxyftp_password: <a_different_password>

Finally, run the playbook with:

    $ ansible-playbook playbook.yml -i hosts [--extra-vars cleanup=yes]

**NOTE**: setting the `cleanup` variable will disable *ssh* access to the current
instance! While this is not set as the default value, an instance *must* be cleaned
before creating an image.

Upon completion, an image can be create using the cloud console.

[java]: https://galaxy.ansible.com/list#/roles/1209
[gos]: https://galaxy.ansible.com/list#/roles/2746
