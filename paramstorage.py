import collections
import random
import shutil
import tempfile
import xml.etree.ElementTree as ET

import numpy as np


def get_flow(demand_file):
    tree = ET.parse(demand_file)
    root = tree.getroot()
    lanes = list()
    gauge = list()
    gauge_list = list()
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
        gauge_list.append(val)
    return np.round(gauge_list)


def set_flow(demand_file):
    tree = ET.parse(demand_file)
    root = tree.getroot()
    for flow in root.iter('flow'):
        current_flow = flow.attrib.get('probability')
        current_flow = str(float(current_flow) + (random.uniform(-1, 1) / 200))
        if float(current_flow) > 0:
            flow.set('probability', current_flow)
    tree.write(demand_file)


def set_offset(tls_file, new_offset):
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
    # Create xml structure
    intersection = ET.Element('intersection')
    file = open(filename, "wb")
    file.write(ET.tostring(intersection))


def add_plan(filename, id, intensity: list, bestplan: list, offset):
    tree = ET.parse(filename)
    intersection = tree.getroot()
    plan = ET.SubElement(intersection, 'plan')
    plan.set('id', id)
    plan.set('offset', offset)
    plan.set('intensity', intensity)
    plan.set('bestplan', bestplan)
    tree.write(filename)


def temp_xml(path):
    tmp = tempfile.NamedTemporaryFile(delete=True)
    shutil.copy2(path, tmp.name)
    return tmp

