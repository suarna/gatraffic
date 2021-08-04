import random as rd
from datetime import datetime

import numpy as np
import traci
import csv
from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import gatraffictoolbox
import paramstorage
import sumoconnector
import trafficinteract

initial_time = datetime.now()
init_state, n_phases, np_phases, n_steps, det_ids_list, offset = trafficinteract.getinfo(
    "Nets/SimpleNet/tls.xml",
    "Nets/SimpleNet/net.net.xml",
    "Nets/SimpleNet/additional.add.xml",
    "Nets/SimpleNet/testdemandpedestrian.rou.xml")

# CONSTANT PARAMETERS
CHROMOSOME_LENGTH = np_phases + 1
POPULATION_SIZE = 150
MU = 30
LAMBDA = 50
P_CROSSOVER = 0.8
P_MUTATION = 0.2
MAX_GENERATIONS = 1
HOF_SIZE = 6
RANDOM_SEED = rd.randint(0, 1000)
CONFIG_FILE_ROUTE = "Nets/SimpleNet/test-sumo.sumocfg"
N_EXPERIMENTS = 2
N_STEPS = n_steps
CYCLE = 120
MIN_PH_TIME = 15
MAX_PH_TIME = CYCLE - (MIN_PH_TIME * np_phases)
MIN_OFFS_TIME = 0
MAX_OFFS_TIME = 100
# SEL_AL = True  SPEA2 / False NSGA2
SINGLE = False
SEL_AL1 = False
SEL_AL2 = False
ADAPT = False
INTERSECTION_ID = '101'

# Define seed
rd.seed(RANDOM_SEED)

intensity = paramstorage.get_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml")
# Store a tmp file of demand data file
xml_copy = paramstorage.temp_xml("Nets/SimpleNet/testdemandpedestrian.rou.xml")
print("\033[93mThe flow in vehicles/h is: {}\033[0m".format(intensity))

if SINGLE:
    weights = (-1.0,)
    creator.create("FitnessSingle", base.Fitness, weights=weights)
    creator.create("Individual", list, fitness=creator.FitnessSingle)
else:
    # (divergence, mean, std)
    weights = (-1.0, -1.0, -1.0)
    # Define creator
    # Define minimize strategy
    creator.create("FitnessMulti", base.Fitness, weights=weights)
    # Gen class
    creator.create("Individual", list, fitness=creator.FitnessMulti)


# -----------------------------------------------------------------------------------------

# Define score function
def score(individual, env):
    return sim.get_score(env, individual)


# Define hof similarity function to limit the hof length if genotype is the same
def pareto_eq(ind1, ind2):
    return np.any(ind1.fitness.values == ind2.fitness.values)


# -----------------------------------------------------------------------------------------------------


# Define toolbox & register register operators
toolbox = base.Toolbox()
toolbox.register("Action", rd.randint, MIN_PH_TIME, MAX_PH_TIME)
toolbox.register("individualCreator", tools.initRepeat, creator.Individual, toolbox.Action, CHROMOSOME_LENGTH)
toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

# Define statistics
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("mean", np.mean)
stats.register("max", np.max)
stats.register("min", np.min)
stats.register("std", np.std)

if SINGLE:
    hof = tools.HallOfFame(maxsize=HOF_SIZE)
else:
    # hof = tools.ParetoFront(similar=pareto_eq)
    hof = tools.ParetoFront(similar=pareto_eq)

# Run simulation
sim = trafficinteract.TrafficEnv(CONFIG_FILE_ROUTE, N_STEPS, CHROMOSOME_LENGTH, det_ids_list, SINGLE)
sim.runs()
# Running original environment
ref_env = sim.rune("Reference")
# Running test environment
test_env = sim.rune("Test")

# Upper and lower sequences with limits for genes generation
lower_bound = []
upper_bound = []
# Boundaries for phases
for n in range(0, np_phases):
    lower_bound.append(MIN_PH_TIME)
    upper_bound.append(MAX_PH_TIME)
# Adding the offset limits
lower_bound.append(MIN_OFFS_TIME)
upper_bound.append(MAX_OFFS_TIME)

toolbox.register("evaluate", score, ref_env)

if SEL_AL1:
    toolbox.register("select", tools.selSPEA2)
elif SEL_AL2:
    ref_points = tools.uniform_reference_points(2, np_phases + 1)
    toolbox.register("select", tools.selNSGA3, ref_points=ref_points)
elif SINGLE:
    toolbox.register("select", tools.selBest)
else:
    toolbox.register("select", tools.selNSGA2)
toolbox.register("mate", tools.cxOnePoint)
toolbox.register("mutate", tools.mutUniformInt, low=lower_bound, up=upper_bound, indpb=1.0 / CHROMOSOME_LENGTH)

# Creating population
population = toolbox.populationCreator(n=POPULATION_SIZE)

v2c_list = []
lb_list = []
best_list = []
best_test_list = []


def main():
    for i in range(0, N_EXPERIMENTS):
        print("-----------------------------------------------------------------------------")
        print("EXPERIMENT NUMBER {} INITIATED".format(i+1))
        print("-----------------------------------------------------------------------------")
        if i != 0:
            # Update HOF fitness for new environment conditions
            for _ in range(len(hof)):
                result = sim.get_score(hof.items[_], ref_env)
                hof.items[_].fitness.values = result
                if hof.items[_] in pop:
                    pop[pop.index(hof.items[_])].fitness.values = result
        pop, lb = algorithms.eaMuPlusLambda(population,
                                            toolbox,
                                            MU,
                                            LAMBDA,
                                            P_CROSSOVER,
                                            P_MUTATION,
                                            MAX_GENERATIONS,
                                            stats,
                                            hof,
                                            True)

        lb_list.append(lb)
        best = hof.items[0]
        best_list.append(best)
        print("\n\033[0;31;40mHOF content is: ", hof)
        print("Best Plan = {}\033[0m".format(best))

        # Apply plan to test env and read result
        test_result = []
        for _ in range(len(hof)):
            if ADAPT:
                # Adapt to cycle
                plan = gatraffictoolbox.adapt(hof.items[_], CYCLE, MIN_PH_TIME, MAX_PH_TIME)
                result = sim.get_score(plan, test_env)
                print("The test score for individual {} adapted from {} is : {}".format(plan, hof.items[_], result))

            else:
                result = sim.get_score(hof.items[_], test_env)
                hof.items[_].fitness.values = result
                test_result.append(hof.items[_])
                print("The test fitness score for individual {} is : {}".format(hof.items[_], result))

        # Get volume to capacity values
        v2c = []
        new_intensity = paramstorage.get_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml")
        for _ in range(len(hof)):
            v2c.append(np.mean(sim.v2c(hof.items[_], new_intensity)))
        min_idx = np.argmin(v2c)
        v2c_list.append([hof.items[min_idx], v2c[min_idx]])

        # Select non dominated from the test set
        best_test = tools.selNSGA2(test_result, 1)
        best_test_list.append(hof.items[hof.items.index(best_test[0])])

        # Set best test offset value in the traffic light logic
        paramstorage.set_offset("Nets/SimpleNet/tls.xml", best_test[len(best_test) - 1])

        paramstorage.set_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml")
        print("\033[93mThe new flow is: {}\033[0m".format(paramstorage.get_flow(
            "Nets/SimpleNet/testdemandpedestrian.rou.xml")))

        print("-----------------------------------------------------------------------------")
        print("EXPERIMENT FINISHED")
        print("-----------------------------------------------------------------------------")

    # Close environments
    traci.switch("Test")
    sumoconnector.close()
    traci.switch("Reference")
    sumoconnector.close()
    traci.switch("default")
    sumoconnector.close()

    # Restore original xml demand data file
    with open("Nets/SimpleNet/testdemandpedestrian.rou.xml", 'w') as original:
        tmp = open(xml_copy.name, 'r')
        original.write(str(tmp.read()))

    print("Evolution:")
    for lb in lb_list:
        print(lb)
    lb_dict = lb_list[0][0]
    keys = lb_dict.keys()
    with open('people.csv', 'w', newline='') as f:
        dw = csv.DictWriter(f, list(keys[0]))
        dw.writeheader()
        dw.writerows(lb_list)

    best_csv = []
    print("Best individual per experiment:")
    for best in best_list:
        print("Experiment: {} # Best: {} # Fitness value: {}".
              format(best_list.index(best), best, best.fitness.values))
        best_csv.append([best_list.index(best), best, best.fitness.values])
    with open('data/best.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(best_csv)

    best_test_csv = []
    print("Best test individual per experiment:")
    for best_test in best_test_list:
        print("Experiment: {} # Best test: {} # Fitness test value: {}".
              format(best_test_list.index(best_test), best_test, best_test.fitness.values))
        best_test_csv.append([best_test_list.index(best_test), best_test, best_test.fitness.values])
    with open('data/best_test.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(best_test_csv)

    v2c_csv = []
    print("Best mean value of volume two capacity ratio:")
    for v2c in v2c_list:
        print("Experiment: {} # Individual: {} # Best volume to capacity: {}".format(v2c_list.index(v2c), v2c[0], v2c[1]))
        v2c_csv.append([v2c_list.index(v2c), v2c[0], v2c[1]])
    with open('data/v2c.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(v2c_csv)

    print("\nThe initial time was: {}".format(initial_time))
    print("The final time is: {}".format(datetime.now()))


if __name__ == "__main__":
    main()
