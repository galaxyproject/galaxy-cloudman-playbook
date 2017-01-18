This [Ansible][ansible] playbook is used to build [Galaxy on the Cloud][goc]
system or any of its components. The playbook is used by the [Galaxy
project][gp] and is intended for anyone wanting to deploy their own version of
Galaxy on the Cloud, whether it is on a private or public cloud.

The *Galaxy on the Cloud* system is composed of several components that are all
necessary before the complete system can be used. This playbook was created to
build those as simply as possible. We strongly recommend reading through [this
page][building] before starting the build process as it has more background
information.

This playbook is intended to be run on a Ubuntu 14.04 system.

## Table of Contents

- [Installation](#installation)
- [Building individual components](#building-individual-components)
  - [Machine Image](#machine-image)
  - [Galaxy File System](#galaxy-file-system)
- [Tying it all together](#tying-it-all-together)

Installation
------------

Clone this repository and run the following command to install any roles that
are not included in the repo:
```
git clone https://github.com/galaxyproject/galaxy-cloudman-playbook.git
ansible-galaxy install -r requirements_roles.yml -p roles -f
```
If you are looking to update your local roles to the tip of their respective
repositories, the same `ansible-galaxy` command should be used.

#### Required configuration

The playbook configuration options are stored in `group_vars/all` and they need
to be updated before using this playbook. Additional cloud configuration
options are stored in `image.json`. The following options must be set before
running the playbook:

 - Create an AWS S3 bucket where the galaxyFS archive will be uploaded and
   provide the bucket name for `galaxy_archive_bucket` variable; an S3 bucket
   is required for this step (if you really don't want to use S3, you will need
   to disable the upload tasks and then manually upload the archive to the
   desired location);
 - Export the following local environment variables:
   - `AWS_ACCESS_KEY`: your Amazon Web Services access key
   - `AWS_SECRET_KEY`: your Amazon Web Services secret key
   - `CM_VNC_PWD`: a throwaway password used for a bridge between VNC and noVNC
   - `CM_GALAXY_FTP_PWD`: a password Galaxy will use to auth to PostgreSQL DB for FTP
   - `CM_GALAXY_ADMIN_PWD`: a Galaxy admin account password for a user that will be
      created to install any Galaxy tools during the build process
 - For building components on an OpenStack cloud, it is also necessary to define
  following environment variables (additional config options can also be defined;
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
`nectar` ([NeCTAR cloud][nectar]), `chameleon`
([Chameleon cloud](https://www.chameleoncloud.org/)), and `jetstream`
([Jetstream cloud](http://jetstream-cloud.org/)). Note that only one of the
OpenStack clouds can be used at a time, for whichever one the environment variables
credentials have been sourced. To build the select destinations, use:

    packer build -only=amazon-ebs|nectar|chameleon image.json

The defined builders use the `default` security group. Make sure the security
group allows SSH access to the launched instances. To get more debugging info,
you can run the command as follows `packer build -debug image.json`.
To increase the Packer logging verbosity, run the command as follows:
`env PACKER_LOG=1 packer build galaxy_on_the_cloud.json`.

##### Building on OpenStack #####

Current implementation of CloudMan and CloudLaunch rely on the OpenStack
EC2 API using [boto library](https://github.com/boto/boto). As a consequence,
the target OpenStack cloud must have the
[EC2-compatibility layer](https://github.com/openstack/ec2-api) enabled. New
versions of CloudLaunch and CloudMan are planned (and under development) that
will use native OpenStack APIs, hence removing this requirement.

Building the components
-----------------------
As stated above, there are several roles contained in this playbook. Subsets of those
roles can be used to build individual components. The following is a list of available
components:
 * *CloudMan*: (i.e., cluster-in-the cloud) only the machine image is necessary
 * *galaxyFS*: the file system used by *Galaxy on the Cloud*; it contains the
   Galaxy application and all of the Galaxy tools

Machine Image
-------------

> There appears to be a bug in combination of Packer/Ansible/Ubuntu where the
> required packages don't get installed for Ansible to run. To work around this
> run `packer` command with the `--debug` option, ssh to the builder instance
> and run the following command before packer attempt to ssh into the instance:
> `sudo apt-get update && sudo apt-get install -y build-essential libssl-dev libffi-dev python-dev`
>
> Further, there appears to be an issue with Packer running on OpenStack lately
> so building the image without Packer is the currently recommended method.

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
commenting out `connection: local` line. Run the role with:

    ansible-playbook -i inventory/builders image.yml --extra-vars vnc_password=<choose a password> --extra-vars psql_galaxyftp_password=<a_different_password> [--extra-vars cleanup=yes]

On average, the build time takes 30 minutes. The `cleanup` var should not be
set for AWS instances (see the next paragraph).

For AWS, to enable [enhanced networking](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking.html),
it is necessary to stop the instance and modify its attribute with the following
command. This step must be run using the [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-set-up.html).

    aws ec2 modify-instance-attribute --instance-id <instance-id> --sriov-net-support simple

Start the instance, update the IP address in the `builders` file, and run the
following command:

    ansible-playbook -i inventory/builders image.yml --extra-vars only_cleanup=yes

*Note that after this step, you will no longer be able to ssh into the instance!*
After the build process completes, create a machine image using the API or the
cloud dashboard. The size of the image root file system should be set to 50GB.

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

### Building or updating galaxyFS
When building a fresh version of galaxyFS or updating an existing one, start by
launching an instance of the image created above. To launch it, it is best to
use the [CloudLaunch app](https://github.com/galaxyproject/cloudlaunch/). You
can install your own instance or contact us and ask to have your cloud added
to the list of clouds available on the public instance running at
https://launch.usegalaxy.org/. Either way, it is necessary to get an
AWS-compatible image ID for the image you built. Take a look at
[this snippet of code](https://gist.github.com/afgane/f9c0c729a36830125ed4)
for an example connection setup.

When launching CloudMan, choose `Cluster only` with `Transient storage` cluster
type if you're building an archive or `Persistent storage` with desired volume
size if you're building a volume/snapshot. If you are updating an existing file
system, launch an instance with the functional file system (i.e., either
transient or volume based) and run this playbook 'over' it (see more below).

Once an instance has launched, edit `galaxyFS.yml` to set `galaxyFS-builder`
`hosts` field and comment out `connection: local` entry. Next, set the launched
instance IP address under `galaxyFS-builder` host group in the `inventory/builders`
file and invoke the following command (having filled in the required variables):

    ansible-playbook -i inventory/builders galaxyFS.yml --extra-vars psql_galaxyftp_password=<psql_galaxyftp_password from image above> --extra-vars galaxy_tools_admin_user_password=<a password>

 > **If you are updating an existing file system**, wait for CloudMan to start
all services before proceeding. Note that for this step, it is not necessary
to shut down any services. Update the value of  `galaxy_changeset_id`
variable in `variables/all`. Finally, if you already have a registered admin
user and want to install/update tools, provide the  admin user API key and
set variable `galaxy_tools_create_bootstrap_user` to `no`. If you don't want to
install/update any tools, set variable `galaxy_install_tools` to `no`. Then run
the following command:

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
process is completed. It is thus a good idea to see what has broken, find a
permanent fix for it, update the build process and build everything again.
Unfortunately, this does not apply to tools installed from the Toolshed because
it is likely you will not have control over those tools. Those tools need to be
repaired manually or via Galaxy.

After you are done troubleshooting, stop Galaxy, ProFTPd, and Postgres from
CloudMan's Admin page and run the playbook with only `cm_create_archive` enabled.

Tying it all together
---------------------
After all the components have been built, we need a little bit of glue to tie
it all together. See [this page][building] (section `Tie it all together`) for
the required details.


[ansible]: http://www.ansible.com/
[cloudman]: http://usecloudman.org/
[goc]: https://wiki.galaxyproject.org/Cloud
[gp]: http://galaxyproject.org/
[building]: https://wiki.galaxyproject.org/CloudMan/Building
[production]: https://wiki.galaxyproject.org/Admin/Config/Performance/ProductionServer
[packer]: https://packer.io/
[nectar]: https://www.nectar.org.au/research-cloud
[pos]: https://packer.io/docs/builders/openstack.html
