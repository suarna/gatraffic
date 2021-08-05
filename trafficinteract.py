from xml.dom import minidom

import numpy as np
import sumolib

import paramstorage
import tlenvironment


def getinfo(tls_file_route: str, net_file_route: str, additional_file_route: str, demand_file_route: str):
    # Parsing xml files
    tls_file = minidom.parse(tls_file_route)
    net_file = minidom.parse(net_file_route)
    additional_file = minidom.parse(additional_file_route)
    phases = tls_file.getElementsByTagName('phase')
    logic = tls_file.getElementsByTagName('tlLogic')
    junctions = net_file.getElementsByTagName('junction')
    detectors = additional_file.getElementsByTagName('e2Detector')

    # Detector list
    det_list = list()
    for element in detectors:
        det_list.append(element.attributes['id'].value)
    print("The detectors are: ", det_list)
    n_lanes = 0
    for element in junctions:
        if element.attributes['type'].value == 'traffic_light':
            n_lanes = len(element.attributes['incLanes'].value.split(":")[0].split(" ")) - 1
    print("The number of incoming lanes is: ", n_lanes)

    # Number of phases
    n_phases = 0
    np_phases = 0
    for element in phases:
        if element.attributes['duration']:
            n_phases += 1
        if int(element.attributes['duration'].value) > 3:
            np_phases += 1

    # Init state
    init_state = np.ndarray((np_phases,), dtype=np.float32)
    count = 0
    for element in phases:
        if int(element.attributes['duration'].value) > 3:
            init_state[count] = float(element.attributes['duration'].value)
            count += 1

    # Demand flows
    demand_list = []
    for flow in sumolib.output.parse_fast(demand_file_route, "flow", ["begin", "end"]):
        demand_list.append(float(flow.end) - float(flow.begin))
    n_steps = demand_list[0]

    for element in logic:
        offset = element.attributes['offset'].value

    # Info output
    print("The initial principal phases are: ", init_state)
    print("The number of phases in the TLS logic is: ", n_phases)
    print("The number of principal phases in the TLS logic is: ", np_phases)
    print("The simulation duration is: ", n_steps)
    return init_state, n_phases, np_phases, np.int(n_steps), det_list, offset


class TrafficEnv:

    def __init__(self, config_file_route, n_steps, n_phases, det_ids_list, single: bool, fit_list: list):
        self.config_file_route = config_file_route
        self.n_steps = n_steps
        self.n_phases = n_phases
        self.det_ids_list = det_ids_list
        self.fit_list = fit_list
        self.single = single

    def runs(self):
        tlenvironment.start_sim(self.config_file_route)

    def rune(self, label):
        env = tlenvironment.SimulationEnv(label,
                                          self.n_phases,
                                          self.n_steps,
                                          self.config_file_route,
                                          self.det_ids_list,
                                          self.fit_list)
        env()
        return env

    def v2c(self, plan, intensity):
        v2c = []
        phases = plan[0:len(plan)-1]
        # Two 3 second transitory per stable phase
        cycle = sum(phases)+len(phases)*6
        for n in range(len(self.det_ids_list)):
            capacity = (phases[n]/cycle)*1900
            # Estimated
            v2c.append(intensity[n]/capacity)
        return np.mean(v2c)

    def get_score(self, individual, env: tlenvironment.SimulationEnv):
        verbose = True
        ctr = 0
        ts = env.reset()
        array = np.array((self.n_phases, ), dtype=np.float32)
        paramstorage.set_offset("Nets/SimpleNet/tls.xml", individual[len(individual) - 1])
        # Always sends the same individual to the simulation for all steps of the episode
        for ctr in range(self.n_steps):
            ts = env.step(individual)
            if ts.step_type is array:
                break
            ctr += 1
        scores = list()
        mean = np.mean(ts.reward)
        std = np.std(ts.reward)
        div = np.abs(np.sum(np.gradient(ts.reward)))
        if self.single:
            scores.append(np.mean([mean, std, div]))
        else:
            scores.append(np.round(mean))
            scores.append(np.round(std))
            scores.append(np.round(div))
        tuple(scores)
        if verbose:
            print("\n\033[92mThe individual for this iteration is: ", individual)
            print("The jam length for this individual is: {}".format(ts.reward))
            print('The score for this individual is: {}\033[0m'.format(scores))
        return scores
