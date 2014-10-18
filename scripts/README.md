Scripted tool installation
==========================

The Galaxy [Tool Shed][ts] provides a nice method for installing Galaxy
artifacts (e.g., tools, workflows) into a (remote) Galaxy instance. The task
of installing a significant number of artifacts can quickly become tedious if
using the GUI due to all the necessary clicking. For that reason, the Tool
Shed offers an [API][bb] that allows us to install any number of tools in an
automated way via a script.

`install_tool_shed_tools.py` is an example of such script. The tools to be
installed via the script should be provided in a file called `shed_tool_list.yaml`.
See `shed_tool_list.yaml.sample` for an example of the format of the file. To
run the script, create a copy of the sample file, list the desired tools, and
run the script via `python install_tool_shed_tools.py`.

File `shed_tool_list.yaml.cloud` contains the list of tool that are installed
for the *Galaxy on the Cloud*.


[ts]: http://genomebiology.com/2014/15/2/403
[bb]: http://bioblend.readthedocs.org/en/latest/api_docs/galaxy/all.html#module-bioblend.galaxy.toolshed
