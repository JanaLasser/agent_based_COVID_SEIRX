import matplotlib.pyplot as plt
import networkx as nx

colors = {'susceptible':'g',
		  'exposed':'orange', 
		  'infected':'red',
	      'recovered':'gray'}

def draw_states(model, step, ax):
	patient_states = pop_numbers = model.datacollector.get_agent_vars_dataframe()
	patient_states['color'] = patient_states['state'].replace(colors)
	color_list = patient_states.loc[step].sort_index()['color']

	G = model.G
	pos = nx.drawing.layout.spring_layout(G, dim=2, weight='weight')
	nodes = list(G.nodes)
	nodes.sort()
	
	for u, v in list(G.edges):
		weight = G[u][v]['weight']
		ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], \
			color='k', linewidth=weight, zorder=1)

	for n in nodes:
	    ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=50, zorder=2)

	ax.set_frame_on(False)
	ax.set_xticks([])
	ax.set_yticks([])

def draw_infection_timeline(model, ax):
	pop_numbers = model.datacollector.get_model_vars_dataframe()
	pop_numbers['S'] = model.num_agents - pop_numbers.E - pop_numbers.I - pop_numbers.R

	ax.plot(pop_numbers.S, label='S', color=colors['susceptible'])
	ax.plot(pop_numbers.E, label='E', color=colors['exposed'])
	ax.plot(pop_numbers.I, label='I', color=colors['infected'])
	ax.plot(pop_numbers.R, label='R', color=colors['recovered'])
	ax.legend()
