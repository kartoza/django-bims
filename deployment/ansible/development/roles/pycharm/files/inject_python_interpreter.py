#!/usr/local/bin/python
# coding=utf-8
import sys
from xml.etree import ElementTree as et

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'


def inject_python_interpreter(
        jdk_table, injected_interpreter):
    # target file
    tree = et.parse(jdk_table)

    # file to be injected
    injected_subtree = et.parse(injected_interpreter)
    injected_component = injected_subtree.getroot()
    python_interpreter_name = injected_component.find('name').attrib['value']

    # find run configuration
    interpreter_index = None
    interpreter_element = None

    for index, child in enumerate(tree.findall('component/jdk')):
        name_tag = child.find('name')
        child_has_interpreter_name = (
            name_tag.attrib['value'] == python_interpreter_name)
        if child_has_interpreter_name:
            interpreter_index = index
            interpreter_element = child
            break
    else:
        interpreter_index = 0
        print 'Not Found'

    if interpreter_index >= 0:
        # add only if not found
        root = tree.getroot()
        component = root.find('component')
        try:
            component.remove(interpreter_element)
        except ValueError:
            # in case it was not found
            pass

        component.insert(interpreter_index, injected_component)

    tree.write(jdk_table)
    return 0


if __name__ == '__main__':
    jdk_table_filename = sys.argv[1]
    injected_interpreter_filename = sys.argv[2]

    sys.exit(inject_python_interpreter(
        jdk_table_filename, injected_interpreter_filename))
