"""
A script to automate installation of tool repositories from a Galaxy Tool Shed
into an instance of Galaxy.

Galaxy instance details and the installed tools need to be provided in YAML
format in a file called ``shed_tool_list.yaml``. See
``shed_tool_list.yaml.sample`` for a sample of such a file.

The script expects any `tool_panel_section_id` provided in the input file to
already exist on the target Galaxy instance. If the section does not exist,
the tool will be installed outside any section. As part of the `galaxyFS`
tagged role(s), a sample file (`shed_tool_conf_cloud.xml`) with a number of
sections is uploaded to the target Galaxy instance and Galaxy's config file
updated to reflect this configuration.

Usage:

    python install_tool_shed_tools.py [-h]

Required libraries:
    bioblend, pyyaml
"""
import datetime as dt
import logging
import time
import yaml
from optparse import OptionParser

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.toolshed import ToolShedClient
from bioblend.toolshed import ToolShedInstance
from bioblend.galaxy.client import ConnectionError

# Omit (most of the) logging by external libraries
logging.getLogger('bioblend').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)


class ProgressConsoleHandler(logging.StreamHandler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    on_same_line = False

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            same_line = hasattr(record, 'same_line')
            if self.on_same_line and not same_line:
                stream.write('\r\n')
            stream.write(msg)
            if same_line:
                stream.write('.')
                self.on_same_line = True
            else:
                stream.write('\r\n')
                self.on_same_line = False
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def _setup_global_logger():
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s - %(message)s')
    progress = ProgressConsoleHandler()
    file_handler = logging.FileHandler('/tmp/galaxy_tool_install.log')
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(progress)
    logger.addHandler(file_handler)
    return logger


def load_input_file(tool_list_file='tool_shed_tool_list.yaml'):
    """
    Load YAML from the `tool_list_file` and return a dict with the content.
    """
    with open(tool_list_file, 'r') as f:
        tl = yaml.load(f)
    return tl


def galaxy_instance(url=None, api_key=None):
    """
    Get an instance of the `GalaxyInstance` object. If the arguments are not
    provided, load the default values using `load_input_file` method.
    """
    if not (url and api_key):
        tl = load_input_file()
        url = tl['galaxy_instance']
        api_key = tl['api_key']
    return GalaxyInstance(url, api_key)


def tool_shed_client(gi=None):
    """
    Get an instance of the `ToolShedClient` on a given Galaxy instance. If no
    value is provided for the `galaxy_instance`, use the default provided via
    `load_input_file`.
    """
    if not gi:
        gi = galaxy_instance()
    return ToolShedClient(gi)


def installed_tools(tsc=None):
    """
    Return a list of tools installed on the Galaxy instance via the tool shed
    client `tsc`. If the `tsc` is not specified, use the default one by calling
    `tool_shed_client` method.
    """
    if not tsc:
        tsc = tool_shed_client()
    installed_tools_list = []
    itl = tsc.get_repositories()
    for it in itl:
        if it['status'] == 'Installed':
            installed_tools_list.append({'name': it['name'],
                                         'owner': it['owner'],
                                         'tool_shed': it['tool_shed'],
                                         'latest': it['tool_shed_status']['latest_installable_revision']})
    return installed_tools_list


def update_tool_status(tool_shed_client, tool_id):
    """
    Given a `tool_shed_client` handle and and Tool Shed `tool_id`, return the
    installation status of the tool.
    """
    try:
        r = tool_shed_client.show_repository(tool_id)
        return r.get('status', 'NA')
    except Exception, e:
        log.warning('\tException checking tool {0} status: {1}'.format(tool_id, e))
        return 'NA'


def _tools_to_install(owners=['devteam', 'iuc'], return_formatted=False):
    """
    This is mostly a convenience method to jumpstart the tools list.

    Get a list of tools that should be installed. This list is composed by
    including all the non-package tools that are owned by `owners` from the Main
    Tool Shed.
    If `return_formatted` is set, return a list of dicts that have been formatted
    according to the required input file for installing tools (see other methods).

    *Note*: there is no way to programatically get a category a tool belongs in
    a Tool Shed so the returned list cannot simply be used as the input file but
    (manual!?!) adjustment is necessesary to provide tool categort for each tool.
    """
    tsi = ToolShedInstance('https://toolshed.g2.bx.psu.edu')
    repos = tsi.repositories.get_repositories()
    tti = []  # tools to install
    for repo in repos:
        if repo['owner'] in owners and 'package' not in repo['name']:
            if return_formatted:
                repo = {'name': repo['name'], 'owner': repo['owner'],
                        'tool_shed_url': 'https://toolshed.g2.bx.psu.edu',
                        'tool_panel_section_id': ''}
            tti.append(repo)
    return tti


def _parse_tool_list(tl):
    """
    A convenience method for parsing the output from an API call to a Galaxy
    instance listing all the tools installed on the given instance and
    formatting it for use by functions in this file. Sample API call:
    `https://test.galaxyproject.org/api/tools?in_panel=true`

    :type tl: list
    :param tl: A list of dicts with info about the tools

    :rtype: tuple of lists
    :return: The returned tuple contains two lists: the first one being a list
             of tools that were installed on the target Galaxy instance from
             the Tool Shed and the second one being a list of custom-installed
             tools. The ToolShed-list is YAML-formatted.

    Note that this method is rather coarse and likely to need some handholding.
    """
    ts_tools = []
    custom_tools = []

    for ts in tl:
        # print "%s (%s): %s" % (ts['name'], ts['id'], len(ts.get('elems', [])))
        for t in ts.get('elems', []):
            tid = t['id'].split('/')
            if len(tid) > 3:
                tool_already_added = False
                for added_tool in ts_tools:
                    if tid[3] in added_tool['name']:
                        tool_already_added = True
                if not tool_already_added:
                    ts_tools.append({'tool_shed_url': "https://{0}".format(tid[0]),
                                     'owner': tid[2],
                                     'name': tid[3],
                                     'tool_panel_section_id': ts['id']})
                # print "\t%s, %s, %s" % (tid[0], tid[2], tid[3])
            else:
                # print "\t%s" % t['id']
                custom_tools.append(t['id'])
    return ts_tools, custom_tools


def _parse_cli_options():
    """
    Parse command line options, returning `options` from `OptionParser`
    """
    parser = OptionParser(usage="usage: python %prog <options>")
    parser.add_option("-t", "--toolsfile",
                      dest="tool_list_file",
                      default=None,
                      help="Tools file to use (see shed_tool_list.yaml.sample)",)
    parser.add_option("-d", "--dbkeysfile",
                      dest="dbkeys_list_file",
                      default=None,
                      help="Reference genome dbkeys to install (see "
                           "dbkeys_list.yaml.sample)",)
    parser.add_option("-a", "--apikey",
                      dest="api_key",
                      default=None,
                      help="Galaxy admin user API key",)
    parser.add_option("-g", "--galaxy",
                      dest="galaxy_url",
                      default=None,
                      help="URL for the Galaxy instance",)
    (options, args) = parser.parse_args()
    return options


def run_data_managers(options):
    """
    Run Galaxy Data Manager to download, index, and install reference genome
    data into Galaxy.

    :type options: OptionParser object
    :param options: command line arguments parsed by OptionParser
    """
    dbkeys_list_file = options.dbkeys_list_file
    kl = load_input_file(dbkeys_list_file)  # Input file contents
    dbkeys = kl['dbkeys']  # The list of dbkeys to install
    dms = kl['data_managers']  # The list of data managers to run
    galaxy_url = options.galaxy_url or kl['galaxy_instance']
    api_key = options.api_key or kl['api_key']
    gi = galaxy_instance(galaxy_url, api_key)

    istart = dt.datetime.now()
    errored_dms = []
    dbkey_counter = 0
    for dbkey in dbkeys:
        dbkey_counter += 1
        dbkey_name = dbkey.get('dbkey')
        dm_counter = 0
        for dm in dms:
            dm_counter += 1
            dm_tool = dm.get('id')
            # Initate tool installation
            start = dt.datetime.now()
            log.debug('[dbkey {0}/{1}; DM: {2}/{3}] Installing dbkey {4} with '
                      'DM {5}'.format(dbkey_counter, len(dbkeys), dm_counter,
                      len(dms), dbkey_name, dm_tool))
            tool_input = dbkey
            try:
                response = gi.tools.run_tool('', dm_tool, tool_input)
                jobs = response.get('jobs', [])
                # Check if a job is actually running
                if len(jobs) == 0:
                    log.warning("\t(!) No '{0}' job found for '{1}'".format(dm_tool,
                                dbkey_name))
                    errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
                else:
                    # Monitor the job(s)
                    log.debug("\tJob running", extra={'same_line': True})
                    done_count = 0
                    while done_count < len(jobs):
                        done_count = 0
                        for job in jobs:
                            job_id = job.get('id')
                            job_state = gi.jobs.show_job(job_id).get('state', '')
                            if job_state == 'ok':
                                done_count += 1
                            elif job_state == 'error':
                                done_count += 1
                                errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
                        log.debug("", extra={'same_line': True})
                        time.sleep(10)
                    log.debug("\tDbkey '{0}' installed successfully in '{1}'".format(
                              dbkey.get('dbkey'), dt.datetime.now() - start))
            except ConnectionError, e:
                response = None
                end = dt.datetime.now()
                log.error("\t* Error installing dbkey {0} for DM {1} (after {2}): {3}"
                          .format(dbkey_name, dm_tool, end - start, e.body))
                errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
    log.info("All dbkeys & DMs listed in '{0}' have been processed.".format(dbkeys_list_file))
    log.info("Errored DMs: {0}".format(errored_dms))
    log.info("Total run time: {0}".format(dt.datetime.now() - istart))


def install_tools(options):
    """
    Parse the default input file and proceed to install listed tools.

    :type options: OptionParser object
    :param options: command line arguments parsed by OptionParser
    """
    istart = dt.datetime.now()
    tool_list_file = options.tool_list_file
    tl = load_input_file(tool_list_file)  # Input file contents
    tools_info = tl['tools']  # The list of tools to install
    galaxy_url = options.galaxy_url or tl['galaxy_instance']
    api_key = options.api_key or tl['api_key']
    gi = galaxy_instance(galaxy_url, api_key)
    tsc = tool_shed_client(gi)
    itl = installed_tools(tsc)  # installed tools list

    responses = []
    errored_tools = []
    skipped_tools = []
    counter = 1
    total_num_tools = len(tools_info)
    default_err_msg = 'All repositories that you are attempting to install have been previously installed.'
    for r in tools_info:
        already_installed = False
        if 'install_tool_dependencies' not in r:
            r['install_tool_dependencies'] = True
        if 'install_repository_dependencies' not in r:
            r['install_repository_dependencies'] = True
        if 'tool_shed_url' not in r:
            r['tool_shed_url'] = 'https://toolshed.g2.bx.psu.edu'
        # Check if the tool is already installed
        for it in itl:
            if r['name'] == it['name'] and r['owner'] == it['owner'] and \
               it['tool_shed'] in r['tool_shed_url'] and it['latest']:
                log.debug("({0}/{1}) Tool {2} already installed. Skipping..."
                       .format(counter, total_num_tools, r['name']))
                skipped_tools.append({'name': r['name'], 'owner': r['owner']})
                already_installed = True
                break
        if not already_installed:
            # Set the payload
            ts = ToolShedInstance(url=r['tool_shed_url'])
            if 'revision' not in r:
                r['revision'] = ts.repositories.get_ordered_installable_revisions(
                    r['name'], r['owner'])[-1]
            # Initate tool installation
            start = dt.datetime.now()
            log.debug('(%s/%s) Installing tool %s from %s to section %s' % (counter,
                total_num_tools, r['name'], r['owner'], r.get('tool_panel_section_id', 'N/A')))
            try:
                response = tsc.install_repository_revision(r['tool_shed_url'], r['name'],
                    r['owner'], r['revision'], r['install_tool_dependencies'],
                    r['install_repository_dependencies'], r.get('tool_panel_section_id', ''))
                tool_id = None
                tool_status = None
                if len(response) > 0:
                    tool_id = response[0].get('id', None)
                    tool_status = response[0].get('status', None)
                if tool_id and tool_status:
                    # Possibly an infinite loop here. Introduce a kick-out counter?
                    log.debug("\tTool installing", extra={'same_line': True})
                    while tool_status not in ['Installed', 'Error']:
                        log.debug("", extra={'same_line': True})
                        time.sleep(10)
                        tool_status = update_tool_status(tsc, tool_id)
                    end = dt.datetime.now()
                    log.debug("\tTool %s installed successfully (in %s) at revision %s"
                              % (r['name'], str(end - start), r['revision']))
                else:
                    end = dt.datetime.now()
                    log.error("\tCould not retrieve tool status for {0}".format(r['name']))
            except ConnectionError, e:
                response = None
                end = dt.datetime.now()
                if default_err_msg in e.body:
                    log.debug("\tTool %s already installed (at revision %s)" % (r['name'],
                           r['revision']))
                else:
                    log.error("\t* Error installing a tool (after %s)! Name: %s,"
                              "owner: %s, revision: %s, error: %s" % (r['name'],
                              str(end - start), r['owner'], r['revision'], e.body))
                    errored_tools.append({'name': r['name'], 'owner': r['owner'],
                                          'revision': r['revision'], 'error': e.body})
            outcome = {'tool': r, 'response': response, 'duration': str(end - start)}
            responses.append(outcome)
        counter += 1

    log.info("Skipped tools: {0}".format(skipped_tools))
    log.info("Errored tools: {0}".format(errored_tools))
    log.info("All tools listed in '{0}' have been processed.".format(tool_list_file))
    log.info("Total run time: {0}".format(dt.datetime.now() - istart))

if __name__ == "__main__":
    global log
    log = _setup_global_logger()
    options = _parse_cli_options()
    if options.tool_list_file:
        install_tools(options)
    elif options.dbkeys_list_file:
        run_data_managers(options)
    else:
        log.error("Must provide tool list file or dbkeys list file. Look at usage.")
