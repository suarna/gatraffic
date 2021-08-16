import random as rd
from datetime import datetime
import matplotlib.pyplot as plot
import copy

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
from parameters import *

initial_time = datetime.now()
init_state, n_phases, np_phases, n_steps, det_ids_list, offset = trafficinteract.getinfo(
    "Nets/SimpleNet/tls.xml",
    "Nets/SimpleNet/net.net.xml",
    "Nets/SimpleNet/additional.add.xml",
    "Nets/SimpleNet/testdemandpedestrian.rou.xml")


# LOAD HYPER-PARAMETERS FROM FILE
hyper_params = params('@param_test.txt')
print("Loaded parameters are: {}".format(hyper_params))
for key, val in hyper_params.items():
    exec(key + '=val')

# DECLARE MORE PARAMETERS
CHROMOSOME_LENGTH = np_phases + 1
MAX_PH_TIME = CYCLE - (MIN_PH_TIME * np_phases)

# Define seed
rd.seed(rd.randint(0, 1000))

intensity = paramstorage.get_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml")
# Store a tmp copy of demand and tls data files
xml_copy_demand = paramstorage.temp_xml("Nets/SimpleNet/testdemandpedestrian.rou.xml")
xml_copy_tls = paramstorage.temp_xml("Nets/SimpleNet/tls.xml")
print("\033[93mThe flow in vehicles/h is: {}\033[0m".format(intensity))

if SINGLE:
    weights = (-1.0,)
    creator.create("FitnessSingle", base.Fitness, weights=weights)
    creator.create("Individual", list, fitness=creator.FitnessSingle)
else:
    # (mean, std, divergence)
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
fit_list = list()
sim = trafficinteract.TrafficEnv(CONFIG_FILE_ROUTE, n_steps, CHROMOSOME_LENGTH, det_ids_list, SINGLE, fit_list)
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
intensity_list = [intensity]


def main():
    try:
        for i in range(0, N_EXPERIMENTS):
            print("-----------------------------------------------------------------------------")
            print("EXPERIMENT NUMBER {} INITIATED".format(i + 1))
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
            # Get a copy of the best hof item
            best = copy.deepcopy(hof.items[0])
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
                    # Update fitness value of hof item
                    hof.items[_].fitness.values = result
                    test_result.append(hof.items[_])
                    print("The test score for individual {} adapted from {} is : {}".format(plan, hof.items[_], result))

                else:
                    result = sim.get_score(hof.items[_], test_env)
                    # Update fitness value of hof item
                    hof.items[_].fitness.values = result
                    test_result.append(hof.items[_])
                    print("The test fitness score for individual {} is : {}".format(hof.items[_], result))

            # Get volume to capacity values
            v2c = []
            new_intensity = paramstorage.get_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml")
            for _ in range(len(hof)):
                if i == 0:
                    v2c.append(np.mean(sim.v2c(hof.items[_], intensity)))
                else:
                    v2c.append(np.mean(sim.v2c(hof.items[_], new_intensity)))
            min_idx = np.argmin(v2c)
            v2c_list.append([hof.items[min_idx], v2c[min_idx]])

            # Select non dominated from the test set
            best_test = tools.selNSGA2(test_result, 1)
            best_test_list.append(hof.items[hof.items.index(best_test[0])])

            # Set best test offset value in the traffic light logic
            paramstorage.set_offset("Nets/SimpleNet/tls.xml", best_test[len(best_test) - 1])

            # Tuning prob flow adding or subtracting a (random(-bound,bound))
            paramstorage.set_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml", BOUND)
            if i != 0:
                intensity_list.append(paramstorage.get_flow("Nets/SimpleNet/testdemandpedestrian.rou.xml"))
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

        print("Evolution:")
        for lb in lb_list:
            print(lb)
        lb_dict = lb_list[0][0]
        keys = lb_dict.keys()
        lb_url = 'data/logbook_' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.csv'
        with open(lb_url, 'w', newline='') as f:
            dw = csv.DictWriter(f, keys)
            dw.writeheader()
            for l in lb_list:
                dw.writerows(l)

        best_csv = []
        print("Best individual per experiment:")
        idx = 0
        for best in best_list:
            print("Experiment: {} # Best: {} # Fitness value: {}".
                  format(idx+1, best, best.fitness.values))
            best_csv.append([idx+1, intensity_list[idx], best, best.fitness.values])
            idx += 1
        with open('data/best_' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Experiment", "Intensity", "Best Plan", "Best Fitness"])
            writer.writerows(best_csv)

        best_test_csv = []
        print("Best test individual per experiment:")
        idx = 0
        for best_test in best_test_list:
            print("Experiment: {} # Best test: {} # Fitness test value: {}".
                  format(idx+1, best_test, best_test.fitness.values))
            best_test_csv.append([idx+1, intensity_list[idx], best_test, best_test.fitness.values])
            idx += 1
        with open('data/best_test_' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Experiment", "Intensity", "Best Test Plan", "Best Fitness"])
            writer.writerows(best_test_csv)

        v2c_csv = []
        print("Best mean value of volume two capacity ratio:")
        idx = 0
        for v2c in v2c_list:
            print("Experiment: {} # Individual: {} # Best volume to capacity: {}".
                  format(idx+1, v2c[0], v2c[1]))
            v2c_csv.append([idx+1, v2c[0], v2c[1]])
            idx += 1
        with open('data/v2c_' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Experiment", "Individual", "V2C Ratio"])
            writer.writerows(v2c_csv)

        # Plotting
        data = np.genfromtxt(lb_url, delimiter=",", names=["gen", "nevals", "mean"])
        x = np.arange(0, len(data["gen"]), 1)
        plot.figure(0)
        plot.plot(x, data["mean"], color='blue')
        plot.xlabel("Generations")
        plot.ylabel("Mean of Fitness")
        plot.savefig('Nets/SimpleNet/plots/test-' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.png')

        plot.figure(1)
        plot.xlabel("Individuals tested")
        plot.ylabel("MA50 of jam length values")
        for lane in range(0, len(det_ids_list)):
            # Compute the moving average per 50 plans
            jam_ma = gatraffictoolbox.ma(list(zip(*fit_list))[lane], 50)
            plot.plot(np.arange(0, len(jam_ma), 1), jam_ma, color="C{}".format(lane))
        plot.savefig('Nets/SimpleNet/plots/jam_test-' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.png')

        print("\nThe initial time was: {}".format(initial_time))
        print("The final time is: {}".format(datetime.now()))
    finally:
        # Restore original xml demand and tls data files
        with open("Nets/SimpleNet/testdemandpedestrian.rou.xml", 'w') as original:
            tmp = open(xml_copy_demand.name, 'r')
            original.write(str(tmp.read()))
        with open("Nets/SimpleNet/tls.xml", 'w') as original:
            tmp = open(xml_copy_tls.name, 'r')
            original.write(str(tmp.read()))


if __name__ == "__main__":
    main()
