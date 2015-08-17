This role is used to setup Galaxy for use with CloudMan.

Requirements
------------
None explicitly, but it's largely intended to be used in the context of the
larger [CloudMan playbook][cmpb]. Also see the [Galaxy Tools role][tr] as it
is useful to run it after this role has been run.

Variables
---------
##### Optional variables #####
Note that some of these variables should match equaly named ones from the
[CloudMan playbook][cmpb].

 - `galaxyFS_base_dir`: (default: `/mnt/galaxy`) the base path under which the
    galaxy file system is planned to be placed
 - `galaxy_user_name`: (default: `galaxy`) system username used for Galaxy
 - `galaxy_server_dir`: (default: `/mnt/galaxy/galaxy-app`) The default
    location where the Galaxy application is stored
 - `galaxy_venv_dir`: (default: `{{ galaxy_server_dir }}/.venv`) The location
    of virtual env used by Galaxy
 - `galaxy_config_file`: (default: `{{ galaxy_server_dir }}/config/galaxy.ini`)
    The location of Galaxy's main configuration file
 - `cmg_setup_files`: A list of files to be copied from this role into Galaxy's
    source tree. See `defaults/main.yml` for the defaults.
 - `cmg_extra_files`: Provides a hook to copy a list of extra, user-defined files
    into Galaxy's source tree. The default is an empty list, but should be in a
    format similar to cmg_setup_files.

##### Control-flow variables #####
Use the following control-flow variables to decide which parts of the role
you'd like to run:

 - `cm_setup_galaxy`: (default: `yes`) whether to run the Galaxy setup step

Dependencies
------------
None.

Example Playbook
----------------
To use the role, wrap it into a playbook file called `playbook.yml` as follows
(the following assumes the role has been placed into directory
`roles/galaxyprojectdotorg.cloudman-galaxy-setup`):

    - hosts: galaxyFS-builder
      sudo: yes
      roles:
        - role: galaxyprojectdotorg.cloudman-galaxy-setup
          sudo_user: "{{ galaxy_user_name }}"

Next, create a `hosts` file:

    [galaxyFS-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Finally, run the playbook as follows:

    $ ansible-playbook playbook.yml -i hosts


[cmpb]: https://github.com/galaxyproject/cloudman-image-playbook
[tr]: https://github.com/galaxyproject/ansible-galaxy-tools
