This role is used to setup a Trackster genome browser in Galaxy.

Requirements
------------
The role has been developed and tested on Ubuntu 14.04. It uses `sudo`
(but could easily be adjusted not to rely on it).

Variables
---------
Note that some of these variables should match equaly named ones from the
[`ansible-cloudman`][acm] role.

 - `galaxy_manage_trackster`: (default: `yes`) if set, the role will run
 - `galaxy_user_name`: (default: `galaxy`) system username used for Galaxy
 - `galaxyFS_base_dir`: (default: `/mnt/galaxy`) the base path under which the
    galaxy file system is planned to be placed
 - `len_file_path`: (default: `"{{ galaxyFS_base_dir }}/configuration_data/len"`)
    the default location where Trackster's `.len` files should be placed
 - `bedtools_version`: (default: `2.20.1`) the version of BED tools to download
    and `make`

Dependencies
------------
None.

Example Playbook
----------------
To use the role, wrap it into a playbook as follows (the following assumes the
role has been placed into directory `roles/galaxyprojectdotorg.trackster`):

    - hosts: galaxyFS-builder
      sudo: yes
      pre_tasks:
        - name: Assure galaxyFS dir exists
          file: path={{ galaxyFS_base_dir }} state=directory owner={{ galaxy_user_name }} group={{ galaxy_user_name }}
          sudo_user: root
      roles:
        - role: galaxyprojectdotorg.trackster

Next, create a `hosts` file:

    [galaxyFS-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Finally, run the playbook as follows:

    $ ansible-playbook playbook.yml -i hosts


[acm]: https://github.com/galaxyproject/ansible-cloudman
