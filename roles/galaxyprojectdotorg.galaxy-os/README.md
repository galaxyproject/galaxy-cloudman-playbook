This Ansible role is for configuring the base operating system useful for
running Galaxy.

Requirements
------------
The role has been developed and tested on Ubuntu 14.04. It requires `sudo` access.

Dependencies
------------
None

Role variables
--------------
All of the listed variabls are stored in `defaults/main.yml`. Individual variables
can be set or overridden by setting them directly in a playbook for this role
(see an example below for `galaxy_user_uid`). Alternatively, they can be set by
creating `group_vars` directory in the root directory of the playbook used to
execute this role and placing a file with the variables there. Note that the
name of this file must match the value of `hosts` setting in the corresponding
playbook (e.g., `os-builder` for the sample playbook provided below).

 - `galaxy_user_name`: (default: `galaxy`) system username to be used for
    Galaxy
 - `galaxy_user_uid`: (default: `1001`) UID for the `galaxy_user_name`

### Control flow variables ###
The following variables can be set to either `yes` or `no` to indicate if the
given part of the role should be executed:
 - `install_packages`: (default: `yes`) install system level packages
 - `add_system_users`: (default: `yes`) configure system level users

Example playbook
----------------
To use the role, it is create a `hosts` file that contains access information
for the target machine, for example:

    [os-builder]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Next, set any variables as desired and place the role into a playbook file
(e.g., `playbook.yml`). This playbook assumes the role has been placed into
`roles/galaxyprojectdotorg.galaxy-os` directory:

    - hosts: os-builder
      sudo: yes
      roles:
        - role: galaxyprojectdotorg.galaxy-os
          galaxy_user_uid: 1055

Finally, run the playbook with:

    $ ansible-playbook playbook.yml -i hosts
