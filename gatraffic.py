import random as rd
from datetime import datetime

import matplotlib.pyplot as plot
import numpy as np
import traci
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from matplotlib.font_manager import FontProperties

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
    "Nets/SimpleNet/demandpedestrian.rou.xml")


# LOAD HYPER-PARAMETERS FROM FILE
hyper_params = params('@param.txt')
print("Loaded parameters are: {}".format(hyper_params))
for key, val in hyper_params.items():
    exec(key + '=val')

# DECLARE MORE PARAMETERS
CHROMOSOME_LENGTH = np_phases + 1
MAX_PH_TIME = CYCLE-(MIN_PH_TIME*np_phases)

# Define seed
rd.seed(rd.randint(0, 1000))

intensity = paramstorage.get_flow("Nets/SimpleNet/demandpedestrian.rou.xml")
print("The flow vehicles/h are: {}".format(intensity))

# (mean, std)
weights = (-1.0, -1.0, -1.0)


# Define creator
# Define minimize strategy
creator.create("FitnessMulti", base.Fitness, weights=weights)


# Gen class
creator.create("Individual", list, fitness=creator.FitnessMulti)

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


# Define hall of fame object
def pareto_eq(ind1, ind2):
    return np.any(ind1.fitness.values == ind2.fitness.values)


hof = tools.ParetoFront(similar=pareto_eq)

# Run simulation
fit_list = list()
sim = trafficinteract.TrafficEnv(CONFIG_FILE_ROUTE, n_steps, CHROMOSOME_LENGTH, det_ids_list, False, fit_list)
sim.runs()
# Running original environment
ref_env = sim.rune("Reference")
# Running test environment
test_env = sim.rune("Test")

# Creating population
population = toolbox.populationCreator(n=POPULATION_SIZE)


def score(individual, env):
    return sim.get_score(env, individual)


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
toolbox.register("select", tools.selNSGA2)
# toolbox.register("select", tools.selSPEA2)
toolbox.register("mate", tools.cxOnePoint)
toolbox.register("mutate", tools.mutUniformInt, low=lower_bound, up=upper_bound, indpb=1.0 / CHROMOSOME_LENGTH)


def main():

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
    # print best solution:
    best = hof.items[0]
    print("\nBest Plan = ", best)
    print("Best Fitness = ", best.fitness.values)
    # Set best offset value
    paramstorage.set_offset("Nets/SimpleNet/tls.xml", best[len(best) - 1])

    # Plotting
    print(lb)
    print(hof)
    mean_fit, max_fit, min_fit, std_fit = lb.select('mean', 'max', 'min', 'std')
    plot.figure(0)
    plot.plot(mean_fit, color='blue')
    plot.xlabel("Generations")
    plot.ylabel("Fitness Values")
    plot.savefig('Nets/SimpleNet/plots/plot-' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.png')
    plot.figure(1)
    plot.xlabel("Individuals tested")
    plot.ylabel("MA50 of jam length values")

    font_p = FontProperties()
    font_p.set_size('xx-small')
    plt = []
    legends = []
    for lane in range(0, len(det_ids_list)):
        # Compute the moving average per 50 plans
        jam_ma = gatraffictoolbox.ma(list(zip(*fit_list))[lane], 50)
        plt += plot.plot(np.arange(0, len(jam_ma), 1), jam_ma, color="C{}".format(lane), label='Lane {}'.format(lane))
        legends.append('Lane {}'.format(lane+1))
    plot.legend(plt[:len(plt)], legends, bbox_to_anchor=(1.12, 1), loc='upper right',
                frameon=False, title='Lanes', prop=font_p)
    plot.savefig('Nets/SimpleNet/plots/jam-' + datetime.now().strftime('%m_%d_%Y-%H:%M:%S') + '.png')

    # Store best solution for the traffic intensity
    try:
        file = open('data/'+INTERSECTION_ID+'.xml')
    except IOError:
        print("We couldn't open the file")
        paramstorage.create_xml_file('data/'+INTERSECTION_ID + ".xml")
    finally:
        file = open('data/'+INTERSECTION_ID + '.xml')
        paramstorage.add_plan('data/'+INTERSECTION_ID + '.xml', INTERSECTION_ID + "-" + str(datetime.now()),
                              intensity, best, offset)
        file.close()

    sumoconnector.close()
    traci.switch("Test")
    sumoconnector.close()
    traci.switch("default")
    sumoconnector.close()

    v2c = []
    for _ in range(len(hof)):
        v2c.append(sim.v2c(hof.items[_], intensity))
    print('The Volume to Capacity Ratio for the hof plans is: {}\033[0m'.format(v2c))
    print("According to Volume to Capacity Ratio the best plan is: ", hof.items[np.argmin(v2c)])
    print("\nThe initial time was: {}".format(initial_time))
    print("The final time is: {}".format(datetime.now()))


if __name__ == "__main__":
    main()
