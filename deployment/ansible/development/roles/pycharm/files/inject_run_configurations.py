#!/usr/local/bin/python
# coding=utf-8
import sys
from xml.etree import ElementTree as et

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'


def inject_run_configurations(
        workspace, injected_workspace):
    injected_subtree = et.parse(injected_workspace)
    injected_component = injected_subtree.getroot()

    tree = et.parse(workspace)

    # find run configuration
    component_index = None
    component_element = None

    for index, child in enumerate(tree.findall('component')):
        child_is_run_manager = child.attrib['name'] == 'RunManager'
        if child_is_run_manager:
            component_index = index
            component_element = child
            break
    else:
        component_index = 0
        print 'Not Found'

    if component_index >= 0:
        root = tree.getroot()
        try:
            root.remove(component_element)
        except ValueError:
            # in case not found
            pass

        root.insert(component_index, injected_component)

    tree.write(workspace)
    return 0

if __name__ == '__main__':
    workspace_filename = sys.argv[1]
    injected_workspace_filename = sys.argv[2]
    sys.exit(inject_run_configurations(
        workspace_filename,
        injected_workspace_filename))
