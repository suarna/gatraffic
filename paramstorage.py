import collections
import random
import shutil
import tempfile
import xml.etree.ElementTree as ET

import gatraffictoolbox


def get_flow(demand_file):
    """Obtain flow expected values from demand file

    :param demand_file: Demand xml file sumo compatible
    :return: A list containing the expected value for an hour of simulation
    """

    tree = ET.parse(demand_file)
    root = tree.getroot()
    lanes = list()
    gauge = list()
    gauge_list = []
    for flow in root.iter('flow'):
        lanes.append(flow.attrib.get('from'))
        gauge.append(float(flow.attrib.get('probability')) * 3600)
    log = idx_lanes(lanes)
    for key in log:
        idx = log[key]
        n = 0
        val = 0
        for n in range(len(idx)):
            val += gauge[idx[n]]
        gauge_list.append(int(val))
    return gauge_list


def set_flow(demand_file: str, change: float):
    """Set probability parameter in flow file

    :param demand_file: Route to the demand xml file sumo compatible
    :param change: The flow probability parameter to apply
    """
    tree = ET.parse(demand_file)
    root = tree.getroot()
    for flow in root.iter('flow'):
        current_flow = flow.attrib.get('probability')
        current_flow = str(float(current_flow) + (random.uniform(-change, change)))
        if float(current_flow) > 0:
            flow.set('probability', current_flow)
    for person_flow in root.iter('personFlow'):
        current_flow = person_flow.attrib.get('probability')
        current_flow = str(float(current_flow) + (random.uniform(-change, change)))
        if float(current_flow) > 0:
            person_flow.set('probability', current_flow)
    tree.write(demand_file)


def set_offset(tls_file: str, new_offset):
    """Function to update the offset parameter

    :param tls_file: The traffic light sumo compatible file
    :param new_offset: The offset parameter to be updated

    """
    tree = ET.parse(tls_file)
    root = tree.getroot()
    for offset in root.iter('tlLogic'):
        offset.set('offset', str(new_offset))
    tree.write(tls_file)


def idx_lanes(lanes):
    log = collections.defaultdict(list)
    for i, item in enumerate(lanes):
        log[item].append(i)
    return log


def create_xml_file(filename: str):
    """Create a new xml file

    :param filename: Name of the new file
    """
    intersection = ET.Element('intersection')
    file = open(filename, "wb")
    file.write(ET.tostring(intersection))


def add_plan(filename, id, intensity: list, bestplan: list, offset):
    """Function that adds a plan to a xml file

    :param filename: File name where store the plan
    :param id: Identity of the intersection
    :param intensity: Intensity flow
    :param bestplan: Best plan to be stored
    :param offset: Offset parameter to be stored

    """
    tree = ET.parse(filename)
    intersection = tree.getroot()
    plan = ET.SubElement(intersection, 'plan')
    plan.set('id', id)
    plan.set('offset', offset)
    plan.set('intensity', intensity)
    plan.set('bestplan', bestplan)
    tree.write(filename)


def temp_xml(path):
    """Creates a temporary file to save the parameters between executions

    :param path: Path to the file to copy
    :return: Temporary file
    """
    tmp = tempfile.NamedTemporaryFile(delete=True)
    shutil.copy2(path, tmp.name)
    return tmp

