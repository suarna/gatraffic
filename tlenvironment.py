
from abc import ABC

import numpy as np
import traci
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step

import sumoconnector


# Class defining the traffic lights environment
def start_sim(sumocfg: str):
    sumoconnector.start(sumocfg)
    # Adding a listener to the simulation
    listener = sumoconnector.Listener()
    traci.addStepListener(listener)
    return True, listener


class SimulationEnv(py_environment.PyEnvironment, ABC):

    def __init__(self, label, n_phases, n_steps, config_file_route: str, det_ids, fit_list: None):
        super().__init__()
        # Label of the selected environment
        self.label = label
        # Define the actions specs
        self._action_spec = array_spec.BoundedArraySpec(
            (n_phases,), np.int8, minimum=15, maximum=30, name='action')
        # Define the observation specs
        self._observation_spec = array_spec.BoundedArraySpec(
            (n_phases,), dtype=np.float32, minimum=15, maximum=35, name='observation')
        # Get the number of lane area detector from simulation
        self.det_ids = det_ids
        # Reward specs
        self._reward_spec = array_spec.ArraySpec(
            (n_phases,), dtype=np.float32, name='reward')
        # Define state
        self._state = np.array(np.repeat(0, n_phases), dtype=np.float32)
        # Assign values to variables
        self.reward = ()
        self.n_steps = n_steps
        self.jam = np.ndarray((len(self.det_ids),), dtype=np.float32)
        self.cycle = 0
        self.config_file_route = config_file_route
        self.fit_list = fit_list

    def __call__(self):
        sumoconnector.start(self.config_file_route, label=self.label)
        # Adding a listener to the simulation
        listener = sumoconnector.Listener()
        traci.addStepListener(listener)
        return True, listener

    def close(self):
        sumoconnector.close()

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def reward_spec(self):
        return self._reward_spec

    def time_step_spec(self):
        return time_step.time_step_spec(self.observation_spec(), self.reward_spec())

    def _reset(self):
        self._state.fill(0)
        return time_step.restart(self._state, reward_spec=self.reward_spec())

    def _step(self, action):
        traci.switch(self.label)
        sumoconnector.advance()
        tls_logic = traci.trafficlight.getCompleteRedYellowGreenDefinition('intersection')[0]
        if traci.simulation.getTime() == 1:
            self.jam.fill(0)
            self.cycle = 0
            for n in range(self._state.size):
                self._state[n] = action[n]
            i = 0
            # Setting initial simulation step
            for n in range(len(tls_logic.getPhases())):
                if tls_logic.getPhases()[n].duration > 3.0:
                    tls_logic.getPhases()[n].__setattr__('duration', self._state[i])
                    traci.trafficlight.setProgramLogic('intersection', tls_logic)
                    self.cycle += tls_logic.getPhases()[n].duration
                    i += 1
                else:
                    self.cycle += tls_logic.getPhases()[n].duration
        for n in range(traci.lanearea.getIDCount()):
            self.jam[n] += traci.lanearea.getJamLengthMeters(self.det_ids.__getitem__(n))
        if traci.simulation.getTime() == self.n_steps:
            traci.load(['--random', '-c', self.config_file_route])
            self.reward = self.jam / self.n_steps
            print("\n\033[96m---------------------------------------------------------------------------"
                  "-----------Simulation Round Finished")
            self.fit_list.append(self.reward)
            return time_step.termination(np.array(self._state), reward=self.reward)
        else:
            return time_step.transition(np.array(self._state), reward=0)
