POPULATION_SIZE = None
MU = None
LAMBDA = None
P_CROSSOVER = None
P_MUTATION = None
MAX_GENERATIONS = None
HOF_SIZE = None
CONFIG_FILE_ROUTE = None
N_EXPERIMENTS = None
CYCLE = None
MIN_PH_TIME = None
MIN_OFFS_TIME = None
MAX_OFFS_TIME = None
SINGLE = None
SEL_AL1 = None
SEL_AL2 = None
ADAPT = None
BOUND = None
INTERSECTION_ID = None


def params(file: str):
    with open(file, 'r') as params_file:
        parameters = params_file.readlines()
    parameters = map(lambda param: param.split('='), parameters)
    hyper_params = dict()
    for hyper, value in parameters:
        value = value.strip()
        if value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        elif value == 'True':
            value = bool(True)
        elif value == 'False':
            value = bool(False)
        else:
            value = str(value)
        hyper_params.setdefault(hyper, value)
    return hyper_params


