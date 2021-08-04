# GATRAFFIC

**gatraffic** Is a Genetic Algorithm Traffic Agent for decentralized traffic management, the current implementation is used for testing purposes

## Using the program:
There are two ways to testing the code, downloading directly the code from https://github.com/suarna/gatraffic.git 
or using a docker image downloaded from https://hub.docker.com/repository/docker/suarna/gatraffic

### Running directly with the code:

 -Clone the repository:

   `git clone https://github.com/suarna/gatraffic.git`

 -Install sumo simulator from your repository if it is available for your OS,
 for example for Ubuntu Linux:
 
	sudo apt-get install sumo sumo-tools
	
-Or download from http://sumo.dlr.de/docs/Downloads.php and follow the instructions for your OS:

-Set the environment variable $SUMO_HOME (if not yet) pointing to the sumo folder:

  `$SUMO_HOME=/usr/share/sumo`

-The best way to satisfy the dependencies is creating a virtual environment into the project main folder, we need to 
satisfy some dependencies:

`sudo apt-get install python3.8`

`sudo apt-get install python3-pip`

`sudo pip3.8 install virtualenv`

-Finally we can create the environment:

`virtualenv -r /usr/bin/python3.8 venv`
 
-Enable Python Virtual Environment using the following command:
  
`source venv/bin/activate`

-Install the required python packages using pip into the main :

`pip3.8 install -r requirements.txt`

-Execute the code:

`python3.8 gatraffic.py`
or
`python3.8 test-gatraffic.py`

-When finished experiments write `deactivate` in the prompt to leave the python virtual environment
  
### Running with docker image:

-Install docker for your distribution from:

https://hub.docker.com/search?q=&type=edition&offering=community  

and follow installation instructions.

-Download the image from the docker HUB repository:

`sudo docker pull suarna/gatraffic:latest`

-Run the image with the following command:

`sudo docker run -it --name gataffic suarna/gatraffic:latest`

-If everything works fine, a prompt, something similar to this should appear:

`root@b0d1305bac4b:/app#`

-Running the code executing the command:

`python3.8 gatraffic.py`
or
`python3.8 test-gatraffic.py`

-Once the experiments are finished you can leave the container using 
`Ctrl+p followed by Ctrl+q` combination, in this case the container remains active, 
if you type `exit` the container will stop.

-If you want to restart the image type and attach the prompt:

`sudo docker container start gataffic && docker attach gataffic`

## Editing execution parameters:

-The parameters are changed editing the gatraffic.py and test-gatraffic.py files:

### PARAMETERS GATRAFFIC.PY

CHROMOSOME_LENGTH = np_phases + 1  
POPULATION_SIZE = 150  
MU = 30  
LAMBDA = 50  
P_CROSSOVER = 0.8  
P_MUTATION = 0.2  
MAX_GENERATIONS = 2  
HOF_SIZE = 6
RANDOM_SEED = rd.randint(0, 1000)
CONFIG_FILE_ROUTE = "Nets/SimpleNet/sumo.sumocfg"  
N_STEPS = n_steps  
CYCLE = 120  
MIN_PH_TIME = 15  
MAX_PH_TIME = CYCLE-(MIN_PH_TIME*np_phases)  
MIN_OFFS_TIME = 0  
MAX_OFFS_TIME = 100  
INTERSECTION_ID = '101'  `

### PARAMETERS TEST-GATRAFFIC.PY

CHROMOSOME_LENGTH = np_phases + 1  
POPULATION_SIZE = 150  
MU = 30  
LAMBDA = 50  
P_CROSSOVER = 0.8  
P_MUTATION = 0.2  
MAX_GENERATIONS = 3  
HOF_SIZE = 6  
RANDOM_SEED = rd.randint(0, 1000)  
CONFIG_FILE_ROUTE = "Nets/SimpleNet/test-sumo.sumocfg"  
N_EXPERIMENTS = 5  
N_STEPS = n_steps  
CYCLE = 120  
MIN_PH_TIME = 15  
MAX_PH_TIME = CYCLE-(MIN_PH_TIME*np_phases)  
MIN_OFFS_TIME = 0  
MAX_OFFS_TIME = 100  
SINGLE = False  
SEL_AL1 = False  
SEL_AL2 = False  
ADAPT = False  
INTERSECTION_ID = '101' 
NORM = 200  

-The parameters SINGLE, AL_1 and AL_2 when set to True are used to compute with other selection algorithms, SPEA2 and 
selNSGA3, selecting SINGLE we select the best individual.

### OTHER PARAMETERS 

-Other parameter is related with verbosity of the output, we can change it in 
trafficinteract.py in the line 98 setting the value verbosity True or False

-We must also set some simulation parameters, we can edit the `demandpedestrian.rou.xml`
changing the flow probabilities and begin end simulation parameters, the same apply for 
`testdemandpedestrian.rou.xml`.

_**It is important that the simulation duration takes the same begin and en values 
for all the flows_
