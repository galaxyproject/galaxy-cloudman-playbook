"""
A script to automate installation of tool repositories from a Galaxy Tool Shed
into an instance of Galaxy.

Galaxy instance details and the installed tools need to be provided in YAML
format in a file called ``tool_shed_tool_list.yaml``. See
``tool_shed_tool_list.yaml.sample`` for a sample of such a file.

The script expects any `tool_panel_section_id` provided in the input file to
already exist on the target Galaxy instance. If the section does not exist,
the tool will be installed outside any section.

Usage:

    python install_tool_shed_tools.py

Required libraries:
    bioblend, pyyaml
"""
import yaml
import datetime as dt
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.toolshed import ToolShedClient
from bioblend.toolshed import ToolShedInstance
from bioblend.galaxy.client import ConnectionError


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


def main():
    """
    Parse the default input file and proceed to install listed tools.
    """
    tool_list_file = 'tool_shed_tool_list.yaml'
    tl = load_input_file(tool_list_file)  # Input file contents
    tools_info = tl['tools']  # The list of tools to install
    gi = galaxy_instance(tl['galaxy_instance'], tl['api_key'])
    tsc = tool_shed_client(gi)

    itl = installed_tools(tsc)  # installed tools list

    responses = []
    errored_tools = []
    skipped_tools = []
    counter = 1
    total_num_tools = len(tools_info)
    default_err_msg = 'All repositories that you are attempting to install have been previously installed.'
    for r in tools_info[:10]:
        already_installed = False
        # Check if the tool is already installed
        for it in itl:
            if r['name'] == it['name'] and r['owner'] == it['owner'] and \
               it['tool_shed'] in r['tool_shed_url'] and it['latest']:
                print ("\n({0}/{1}) Tool {2} already installed. Skipping..."
                       .format(counter, total_num_tools, r['name']))
                skipped_tools.append({'name': r['name'], 'owner': r['owner']})
                already_installed = True
                break
        if not already_installed:
            # Set the payload
            if 'install_tool_dependencies' not in r:
                r['install_tool_dependencies'] = True
            if 'install_repository_dependencies' not in r:
                r['install_repository_dependencies'] = True
            if 'tool_shed_url' not in r:
                r['tool_shed_url'] = 'http://toolshed.g2.bx.psu.edu'
            ts = ToolShedInstance(url=r['tool_shed_url'])
            if 'revision' not in r:
                r['revision'] = ts.repositories.get_ordered_installable_revisions(
                    r['name'], r['owner'])[-1]
            # Initate tool installation
            start = dt.datetime.now()
            print '\n(%s/%s) Installing tool %s from %s to section %s' % (counter,
                total_num_tools, r['name'], r['owner'], r['tool_panel_section_id'])
            try:
                response = tsc.install_repository_revision(r['tool_shed_url'], r['name'],
                    r['owner'], r['revision'], r['install_tool_dependencies'],
                    r['install_repository_dependencies'], r['tool_panel_section_id'])
                end = dt.datetime.now()
                print "Tool %s installed successfully (in %s) at revision %s" % (r['name'],
                    str(end - start), r['revision'])
            except ConnectionError, e:
                response = None
                end = dt.datetime.now()
                if default_err_msg in e.body:
                    print ("Tool %s already installed (at revision %s)" % (r['name'],
                           r['revision']))
                else:
                    print ("* Error installing a tool! Name: %s, owner: %s, revision: %s"
                           ", error: %s" % (r['name'], r['owner'], r['revision'], e.body))
                    errored_tools.append({'name': r['name'], 'owner': r['owner'],
                                          'revision': r['revision'], 'error': e.body})
            outcome = {'tool': r, 'response': response, 'duration': str(end - start)}
            responses.append(outcome)
        counter += 1

    print "\n\nSkipped tools: {0}".format(skipped_tools)
    print "\nErrored tools: {0}".format(errored_tools)
    print "\nAll tools listed in '{0}' have been processed.".format(tool_list_file)

if __name__ == "__main__":
    main()
    pass
