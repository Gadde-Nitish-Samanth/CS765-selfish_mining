# bitcoin-simulation

Libraries used:
python 3.8.10
numpy 1.17.4
simpy 4.0.1 (pip install simpy)

In the folder named code:
1.models.py contains the classes used to model the nodes,transactions,connection between two nodes,blocks
2.networkgen.py returns the adjacency matrix corresponding to the network
3.simulation.py runs the simulation of blockchain using models.py and networkgen.py

how to run the simulation:

go inside the folder code and run the following command in the terminal

python3 simulation.py

and set the simulation parameters asked where 
n = number of nodes
z = percent of slow nodes
T_tx = mean interarrival time of transactions
percent_high_cpu = percent of nodes with high cpu
B_Tx = mean interarrival time of blocks# CS765-selfish_mining
