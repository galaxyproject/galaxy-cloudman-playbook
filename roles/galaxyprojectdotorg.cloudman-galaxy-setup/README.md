This role is used to setup Galaxy for use with CloudMan.

Requirements
------------
None explicitly, but it's largely intended to be used in the context of the
larger [CloudMan playbook][cmpb]

Variables
---------
##### Required variables #####
 - `galaxy_admin_user_password`: a string to be used for the bootstrap Galaxy
    admin user

##### Optional variables #####
Note that some of these variables should match equaly named ones from the
[CloudMan playbook][cmpb].

 - `galaxy_user_name`: (default: `galaxy`) system username used for Galaxy
 - `galaxy_admin_user`: (default: `cloud@galaxyprojec.org`) a Galaxy Admin
    user that will be created and used when installing the tools/data
 - `galaxy_server_dir`: (default: `/mnt/galaxy/galaxy-app`) The default
    location where the Galaxy application is stored
 - `galaxy_venv_dir`: (default: `{{ galaxy_server_dir }}/.venv`) The location
    of virtual env used by Galaxy
 - `galaxy_config_file`: (default: `{{ galaxy_server_dir }}/config/galaxy.ini`)
    The location of Galaxy's main configuration file
 - `cmg_setup_files`: A list of files to be copied from this role into Galaxy's
    source tree. See `defaults/main.yml` for the defaults.
 - `shed_tool_list_file`: (default `scripts/shed_tool_list.yaml.sample` - note
    that the default path is relative `files` subdirectory) The list of tools
    to be installed from the Tool Shed into the given Galaxy instance.
    See the default file for sample of the format.
 - `dbkeys_list_file`: (default: `scripts/dbkeys_list.yaml.sample` - note
    that the default path is relative `files` subdirectory) The list of
    reference genomes and desired formats to be installed via Galaxy
    [Data Managers][dm]. See the default file for sample of the format.

##### Control-flow variables #####
Use the following control-flow variables to decide which parts of the role
you'd like to run:

 - `cm_setup_galaxy`: (default: `yes`) whether to run the Galaxy setup step
 - `cm_install_tools`: (default: `yes`) whether to install Galaxy tools. Also
    see `shed_tool_list_file`
 - `cm_install_data`: (default: `yes`) whether to install Galaxy reference
    data. Also see `dbkeys_list_file`

Dependencies
------------
None.

Example Playbook
----------------
To use the role, wrap it into a playbook as follows (the following assumes the
role has been placed into directory
`roles/galaxyprojectdotorg.cloudman-galaxy-setup`):

    - hosts: galaxyFS-builder
      sudo: yes
      roles:
        - role: galaxyprojectdotorg.cloudman-galaxy-setup
          sudo_user: "{{ galaxy_user_name }}"
          galaxy_admin_user_password: <a_password>

Next, create a `hosts` file:

    [galaxyFS-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Finally, run the playbook as follows:

    $ ansible-playbook playbook.yml -i hosts


[cmpb]: https://github.com/galaxyproject/cloudman-image-playbook
[dm]: https://wiki.galaxyproject.org/Admin/Tools/DataManagers
