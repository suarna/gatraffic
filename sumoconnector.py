import os
import sys

import traci


def start(sumo_file: str, label: str = "default"):
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("you must declare environment variable 'SUMO_HOME'")
    sumo_binary = "/usr/bin/sumo"
    sumo_cmd = [sumo_binary, "--random", "-c", sumo_file]
    traci.start(sumo_cmd, label=label)
    return True


def advance(n_steps: int = 0):
    traci.simulationStep(n_steps)
    return True


def close():
    traci.close()
    return True


class Listener(traci.StepListener):

    def step(self, t):
        # print("Listener called with parameter %s." % t)
        return True

