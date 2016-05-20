This [Ansible][ansible] playbook is used to build [Galaxy on the Cloud][goc]
system or any of its components. The playbook
is used by the [Galaxy project][gp] and is intended for anyone
wanting to deploy their own version of Galaxy on the Cloud, whether it is
on a private or public cloud.

This playbook is intended to be run on a Ubuntu (14.04) system.

## Table of Contents

- [Build the entire *Galaxy on the Cloud*](#build-the-entire-galaxy-on-the-cloud)
- [Building individual components](#building-individual-components)
  - [Machine Image](#machine-image)
  - [Galaxy File System](#galaxy-file-system)
- [Tying it all together](#tying-it-all-together)

Build the entire *Galaxy on the Cloud*
--------------------------------------
The *Galaxy on the Cloud* system is composed of several components that are all necessary
before the complete system can be used. This playbook was created to build those as
simply as possible. We strongly recommend reading through [this page][building] before
starting the build process as it has more background information. Overall,
after you have gotten some of the preliminaries completed, all the components can be
built with the following command (more information about Packer, including how to
install it, is available [here][packer]):

    packer build galaxy_on_the_cloud.json

Above command will launch a builder an instance, configure it for use by Galaxy and
[CloudMan][cloudman], build the galaxy file system (`galaxyFS`; see below), upload
an archive of the file system to an S3 bucket, build an machine image, and clean
everything up. Having said that, this process assumes all the Galaxy tools and data
(assuming those are being installed; see *galaxyFS* notes
below) get installed properly and require no manual intervention. If that is not the
case or you would like to have more insight into the process, see below for
building components individually.
*At the end of the run, to be able to launch instances of
the system, it is necessary to update the launch information. See 'Tying it all
together section' below.*

#### Required configuration
The playbook configuration options are stored in `group_vars/all` and they need to
be updated before using this playbook. Additional cloud configuration options are
stored in `image.json` and `galaxy_on_the_cloud.json`. The following options must be
set before running the playbook:

 - Create an S3 bucket where the galaxyFS will be uploaded and provide
 the bucket name for `galaxy_archive_bucket` variable;
 - Export the following local environment variables:
   - `AWS_ACCESS_KEY`: your Amazon Web Services access key
   - `AWS_SECRET_KEY`: your Amazon Web Services secret key
   - `CM_VNC_PWD`: a throwaway password used for a bridge between VNC and noVNC
   - `CM_GALAXY_FTP_PWD`: a password Galaxy will use to auth to PostgreSQL DB for FTP
   - `CM_GALAXY_ADMIN_PWD`: a Galaxy admin account password for a user that will be
      created to install any Galaxy tools during the build process
 - For building components on an OpenStack cloud, it is also necessary to define
  several environment variables (additional config options can also be defined;
  see [Packer documentation for OpenStack][pos] for more). If using identity v2,
  set the following env variables: `OS_PASSWORD`, `OS_USERNAME`, `OS_TENANT_NAME`,
  `OS_AUTH_URL`. If using identity v3, set the following ones: `OS_PROJECT_DOMAIN_NAME`,
  `OS_USER_DOMAIN_NAME`, `OS_PROJECT_NAME`, `OS_TENANT_NAME`, `OS_USERNAME`,
  `OS_PASSWORD`, `OS_AUTH_URL`, `OS_IDENTITY_API_VERSION`.
  These variables can be obtained from your OpenStack account Dashboard by
  downloading  the OpenStack RC file (from *Instances* -> *Access & Security*
  -> *API Access*) and sourcing it.

#### Optional configuration options ####
Majority of the configuration options are stored in `group_vars/all` and they represent
reasonable defaults. If you would like to change any of the variables, descriptions
of the available options are provided in README files for individual roles that
are included in this playbook.

#### Multiple Clouds ####
The Packer system and the build scripts support the ability to build the image on
multiple destinations simultaneously. This is the default behavior. The destinations
are defined as `builders` sections inside the `image.json` file. At the moment,
`builders` define the following destinations: `amazon-ebs` (us-east-1 region),
`nectar` ([NeCTAR cloud][nectar]), and `chameleon`
([Chameleon cloud](https://www.chameleoncloud.org/)). Note that only one of the
OpenStack clouds can be used at a time, for whichever one the environment variables
credentials have been sourced. To build the select destinations, use:

    packer build -only=amazon-ebs|nectar|chameleon galaxy_on_the_cloud.json

The defined builders user the `default` security group. Make sure the security
group allows SSH access to the launched instances. To get more debugging info,
you can run the command as follows `packer build -debug galaxy_on_the_cloud.json`.
To increase the Packer logging verbosity, run the command as follows:
`env PACKER_LOG=1 packer build galaxy_on_the_cloud.json`.

Building individual components
------------------------------
As stated above, there are several roles contained in this playbook. Subsets of those
roles can be used to build individual components. The following is a list of available
components:
 * *CloudMan*: (i.e., cluster-in-the cloud) only the machine image is necessary
 * *galaxyFS*: the file system used by *Galaxy on the Cloud*; it contains the Galaxy
    application and all of the Galaxy tools

Particularly when building the system for the first time, it is advisable to
build individual components rather than all the pieces at once because it gives
more insight into what is going.

Machine Image
-------------
To build the machine image, run the following command (unless parameterized,
this will run the build process for all the clouds defined in `image.json`, see
*Multiple Clouds* above):

    packer build -only=amazon-ebs|nectar|chameleon image.json

Note that this command requires the same environment variables to be defined as
specified above. Additional options can be set by editing `image.json`, under
`extra_arguments` section. If you have made changes to `image.json` configuration file,
before you run the `build` command, it's a good idea to execute
`packer validate image.json` and make sure things are formatted correctly. The
`build` command will provision an instance, run the Ansible `cloudman-image` role,
create an AMI, and terminate the builder instance. The image build process
typically takes about an hour. You can also run the build command with
`-debug` option to get more feedback during the build process.

#### Running without Packer ####
To build an image without Packer, make sure the default values provided in the
`group_vars/all` file suit you. Create a copy of `inventory/builders.sample` as
`inventory/builders`, manually launch a new instance and set the instance IP address
under `image-builder` host group in the `builders` file. Also set the path to your
private ssh key for the `ansible_ssh_private_key_file` variable. This option also
requires you to edit `image.yml` file to set `hosts` line to `image-builder` while
commenting out `connection: local` line. Finally, run the role with

    ansible-playbook -i inventory/builders image.yml --extra-vars vnc_password=<choose a password> --extra-vars psql_galaxyftp_password=<a_different_password> --extra-vars cleanup=yes

On average, the build time takes about an hour. *Note that after the playbook
has run to completion, you will no longer be able to ssh into the instance!* If
you still need to ssh, set `--extra-vars cleanup=no` in the above command.
Before creating the image, however, you must rerun the entire playbook with that
flag set or run it with `--extra-vars only_cleanup=yes` to run the cleanup tasks only.

### Customizing
A configuration file exposing adjustable options is available under
`group_vars/all`. Besides allowing you to set some
of the image configuration options, this file allows you to easily control which
steps of the image building process run. This can be quite useful if a step fails
and you want to rerun only it or if you're just trying to run a certain steps.

Galaxy File System
------------------
The Galaxy File System (galaxyFS) can be built two different ways: as an archive
or a volume. The archive option creates a tarball of the entire galaxyFS and
uploads it to S3. When instances are launched, the archive is downloaded and
extracted onto a local file system. Note that a single archive can be downloaded
from multiple cloud availability zones and even multiple clouds. *Galaxy on the Cloud*
releases (Mid 2015 onwards) use this option and this is the default action
for this playbook.

Alternatively, *galaxyFS* can be built as a volume and converted into a snapshot.
The created snapshot can then be shared (or made public). Launched instances
will, at runtime, create a volume based on the available snapshot. For this
option, a volume snapshot needs to exist in each region and on every cloud
instances want to be deployed.

In addition to the conceptual choices, this role requires a number of configuration
options for the Galaxy application, CloudMan application, PostgreSQL database,
as well as the glue linking those. The configuration options have been aggregated
under `group_vars/all` and represent reasonable defaults but you can change them
as you feel is more appropriate. Keep in mind that changing the options that
influence how the system is deployed and/or managed may also require changes in
CloudMan.

#### Playbook-specific variables
Each of the included roles have their own README file capturing the available
variables. The list of variables provided below represents only the variables
that are specific to this playbook and do not otherwise show up in the
included roles. These variables can be changed in `group_vars/all` file:

 - `cm_create_archive`: (default: `yes`) if set, create a tarball archive
    of the galaxyFS file system
 - `galaxy_archive_path`: (default: `/mnt/galaxyFS_archive`) the directory
    where to place the file system tarball archive. Keep in mind that this
    directory needs to have sufficient disk space to hold the archive.
 - `galaxy_archive_name`: (default: `galaxyFS-latest.tar.gz`) the file name
    for the archive
 - `galaxy_timestamped_archive_name`: (default:
    `galaxyFS-{{ lookup('pipe', 'date +%Y%m%d') }}.tar.gz`) timestamped
    file name for the archive that will be uploaded to S3 in addition to
    `galaxy_archive_name`
 - `galaxy_archive_bucket`: (default: `cloudman/fs-archives`) after it's
    created, the archive will be uploaded to S3. Specify the bucket (and folder)
    where to upload the archive.
 - `aws_access_key`: (default: `{{ lookup('env','AWS_ACCESS_KEY') }}`) the AWS
    access key. The default value will lookup specified environment variable.
 - `aws_secret_key`: (default: `{{ lookup('env','AWS_SECRET_KEY') }}`) the AWS
    secret key. The default value will lookup specified environment variable.

### Installing Galaxy tools
Before building the file system, you may choose to have Galaxy tools automatically
installed as part of the build process (by setting the value of variable
`galaxy_install_tools` to `yes` in file `group_vars/all`. The list of tools to
be installed from a Tool Shed needs to be provided. A sample of the file can be
found in `files/shed_tool_list.yaml`. Which file to use can be specified via
`tool_list_file` variable in file `group_vars/all`. If you do not wish to have
the tools installed as part of the build process, set the variable
`galaxy_install_tools` to `no`.

If you wish to use this playbook only to install some Galaxy tools, comment out
all roles except `galaxyprojectdotorg.tools` in `galaxyFS.yml`
file. You may also want to comment out the `pre_tasks`, depending on where you
are running this.

*Warning:* When running the `galaxy` role, a clean copy of
`shed_tool_conf_cloud.xml` is placed into the `config` dir.
The implication is that if you have already installed tools (e.g., by hand or
by having run this role earlier), it will replace that file (and
this file contains information about already existing tool installations). To
prevent the role from replacing this file, comment out the file name in
`group_vars/all` under `galaxy_config_files`.

### Building or updating galaxyFS
When building a fresh version of galaxyFS or updating an existing one, start by
launching an instance of the image created above.
Once CloudMan starts, choose `Cluster only` with `Transient storage` cluster type
if you're building an archive or `Persistent storage` with desired volume size
if you're building a volume/snapshot. If you are updating an existing file system,
launch an instance with the functional file system (i.e., either transient or
volume based) and run this playbook 'over' it (see more below).

Once an instance has launched, edit `galaxyFS.yml` to set `galaxyFS-builder`
`hosts` field and comment out `connection: local` entry. Next, set the launched
instance IP address under `galaxyFS-builder` host group in the `inventory/builders`
file and invoke the following command (having filled in the required variables):

    ansible-playbook -i inventory/builders galaxyFS.yml --extra-vars psql_galaxyftp_password=<psql_galaxyftp_password from image above> --extra-vars galaxy_admin_user_password=<a password>

 > **If you are updating an existing file system**, note the Warning
 > note in the previous section. Remember to update the value of
 > `galaxy_changeset_id` variable in `variables/all`. Finally, if you already
 > have a registered admin user, provide the admin user API key and set variable
 > `galaxy_tools_create_bootstrap_user` to `no`. Then run the following command:
 >
 > `ansible-playbook -i inventory/builders galaxyFS.yml --extra-vars galaxy_tools_api_key=<API KEY> --tags "update"`

This will download and configure Galaxy as well as install any specified tools.
Note that depending on the number of tools you are installing, this build process
may take several hours. At the end, if building the file system from scratch, a
file system archive will be created and uploaded to S3. It is often desirable
(and necessary) to do double check that tools installed properly and repair any
failed ones. In that case (or if you are updating an existing file system),
after we've made the changes, it is necessary to explicitly create the archive
and upload it to the object store. To achieve this, via CloudMan, stop Galaxy,
ProFTPd, and Postgres services on the running instance and rerun the above
command with `--tags "filesystem"`.

When completed, terminate the builder instance via CloudMan.

#### galaxyFS as a volume
After you have launched an instance, go to CloudMan's Admin page and add a
new-volume-based file system of desired size (e.g., 10GB). Set variable
`cm_create_archive` to `no`. Then, run the above `ansible-playbook` command.
After the process has completed, back on CloudMan's Admin page, create a
snapshot of the file system.

### Accessing Galaxy on the build system
After the build process has completed, you can access the Galaxy application.
To do so, visit CloudMan's Admin page. First, disable CloudMan's service
dependency framework (under *System Controls*). Then, start Postgres, ProFTPd,
and Galaxy services - in that order, while waiting for each of them to enter
`Running` state before staring the next one. Once Galaxy is running, the
*Access Galaxy* button will become active.

### Troubleshooting
Despite the best effort, especially when installing tools, it is likely that
the build process will not go quite as expected and manual intervention will
be necessary. In this case, start Galaxy as described in the previous
sub-section, and login as the bootstrap user (use the login info you defined
for variables `galaxy_admin_user` and `galaxy_admin_user_password`). Tools can
then be 'repaired' from the Galaxy Admin page.

Keep in mind that whatever actions you perform in Galaxy at this stage will be
preserved in the final build. For example, if you create a user, upload data,
or run jobs - all of these will be preserved after the file system build
process is completed. It it thus a good idea to see what has broken, find a
permanent fix for it, update the build process and build everything again.
Unfortunately, this does not apply to tools installed from the Toolshed because
it is likely you will not have control over those tools. Those tools need to be
repaired manually/via Galaxy.

After you are done troubleshooting, stop Galaxy, ProFTPd, and Postgres from
CloudMan's Admin page and run the playbook with only `cm_create_archive` enabled.

Tying it all together
---------------------
After all the components have been built, we need a little bit of glue to tie
it all together. See [this page][building] (section `Tie it all together`) for
the required details.


Galaxy Server Branch - this is probably not working any more
-------------
This role will build a standalone Galaxy Server that is configured to be
[production-ready][production]. The Server does not contain any of the cloud or
CloudMan components but instead focuses on providing a well-configured standalone
instance of the Galaxy application for a dedicated server. As part of the
installation, Galaxy will be configured to use the local job runner. Note that
this role will install a number of system packages, system users, as well as
Galaxy-required software and configurations and thus requires *root* access; it
is best used on a dedicated system or a VM.

To run this role, you must switch to the `server` branch of the repository. The
configuration options used to setup the Server are available within the individual files
in the `group_vars` folder. Make sure to change the value of `psql_galaxyftp_password`
in `group_vars/all`! Next, create a copy of `inventory/builders.sample` as
`inventory/builders` and provide the IP address of the target machine under both
under `image-builder` and `galaxyFS-builder` host groups. Once the settings are to your
liking, run the role with

    ansible-playbook -i inventory/builders cloud.yml --tags "server"

Once the run has completed and you'd like to install Galaxy tools, take a look at the
`scripts` directory in this repository for an automated method of installing the tools.


[ansible]: http://www.ansible.com/
[cloudman]: http://usecloudman.org/
[goc]: https://wiki.galaxyproject.org/Cloud
[gp]: http://galaxyproject.org/
[building]: https://wiki.galaxyproject.org/CloudMan/Building
[production]: https://wiki.galaxyproject.org/Admin/Config/Performance/ProductionServer
[packer]: https://packer.io/
[nectar]: https://www.nectar.org.au/research-cloud
[pos]: https://packer.io/docs/builders/openstack.html
