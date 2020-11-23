import numpy as np
import pandas as pd
import networkx as nx

def test_infection(a):
    if a.infectious or a.recovered or a.exposed:
        return 1
    else:
        return 0
    
def count_infected(model, agent_type):
    infected_agents = np.asarray([test_infection(a) for a in model.schedule.agents \
                         if a.type == agent_type]).sum()
    
    return infected_agents
    
def calculate_R0(model):
    transmissions = [a.transmissions for a in model.schedule.agents]
    infected = [test_infection(a) for a in model.schedule.agents]
    IDs = [a.ID for a in model.schedule.agents]
    types = [a.type for a in model.schedule.agents]
    df = pd.DataFrame({'ID':IDs,
                       'type':types,
                       'was_infected':infected,
                       'transmissions':transmissions})
    df = df[df['was_infected'] == 1]
    overall_R0 = df['transmissions'].mean()
    resident_R0 = df[df['type'] == 'resident']['transmissions'].mean()
    employee_R0 = df[df['type'] == 'employee']['transmissions'].mean()
    
    return (overall_R0, resident_R0, employee_R0)

def calculate_finite_size_R0(model):
    df = pd.DataFrame(columns=['ID', 'agent_type', 't', 'target'])
    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target in a.transmission_targets.keys():
                df = df.append({'ID':a.ID, 'agent_type':a.type,
                    't':a.transmission_targets[target], 'target':target},
                            ignore_index=True)
                
    # find first transmission(s)
    # NOTE: while it is very unlikely that two first transmissions occurred
    # in the same timestep, we have to account for the possibility nevertheless
    first_transmitters = df[df['t'] == df['t'].min()]['ID'].values
    N_transmissions = []
    for ft in first_transmitters:
        N_transmissions.append(len(df[df['ID'] == ft]))
        
    return np.mean(N_transmissions), df

def get_transmission_network(model):
    transmissions = []
    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target in a.transmission_targets.keys():
                transmissions.append((a.ID, target))
                
    G = nx.Graph()
    G.add_edges_from(transmissions)
                
    return G

def get_statistics(df, col):
    return {
        '{}_mean'.format(col):df[col].mean(),
        '{}_median'.format(col):df[col].median(),
        '{}_0.025'.format(col):df[col].quantile(0.025),
        '{}_0.75'.format(col):df[col].quantile(0.75),
        '{}_0.25'.format(col):df[col].quantile(0.25),
        '{}_0.975'.format(col):df[col].quantile(0.975),
        '{}_std'.format(col):df[col].std(),
    }