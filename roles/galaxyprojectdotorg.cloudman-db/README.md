This role is used to setup a PostgreSQL database for use with Galaxy CloudMan,
specifically, as part of *galaxyFS*.

Requirements
------------
The role has been developed and tested on Ubuntu 14.04. It requires `sudo`
access and assumes it is being run on a [`ansible-cloudman`][acm] image.

Variables
---------
Note that these variables should match equaly named ones from the
[`ansible-cloudman`][acm] role.

### Required variables ###
 - `psql_galaxyftp_password`: a password that must match the one that was baked
    into the image when [`ansible-cloudman`][acm] role was run. In general, it
    allows Galaxy to authenticate FTP users.

### Optional variables ###
 - `galaxy_user_name`: (default: `galaxy`) system username to be used for for
    Galaxy
 - `galaxyFS_base_dir`: (default: `/mnt/galaxy`) the base path under which the
    galaxy file system is planned to be placed
 - `galaxy_server_dir`: (default: `"{{ galaxyFS_base_dir }}/galaxy-app"`) the
    location where the Galaxy application is planend to be placed
 - `galaxy_db_dir`: (default: `"{{ galaxyFS_base_dir }}/db"`) the location wher
    Galaxy's PostgreSQL database will be placed
 - `galaxy_db_port`: (default: `5930`) the port set for Galaxy's PostgrSQL database
 - `postgresql_bin_dir`: (default: `/usr/lib/postgresql/9.3/bin`) the path where
    PostgreSQL binary files are stored. This path will be added to `$PATH`
 - `galaxy_db_log`: (default: `/tmp/pSQL.log`) the location for the log file for
    this database.

Dependencies
------------
None explicitly but see *Requirements* above.

Example Playbook
----------------
To use the role, wrap it into a playbook as follows (the following assumes the
role has been placed into directory `roles/galaxyprojectdotorg.cloudman-database`):

    - hosts: galaxyFS-builder
      sudo: yes
      pre_tasks:
        - name: Assure galaxyFS dir exists
          file: path={{ galaxyFS_base_dir }} state=directory owner={{ galaxy_user_name }} group={{ galaxy_user_name }}
          sudo_user: root
        - name: Create database dir
          file: path={{ galaxy_db_dir }} state=directory owner=postgres group=postgres
          sudo_user: root
      roles:
        - role: galaxyprojectdotorg.cloudman-database
          sudo_user: postgres
          psql_galaxyftp_password: <password_matching_the_one_on_the_image>

Next, create a `hosts` file:

    [galaxyFS-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Finally, run the playbook as follows:

    $ ansible-playbook playbook.yml -i hosts


[acm]: https://github.com/galaxyproject/ansible-cloudman
