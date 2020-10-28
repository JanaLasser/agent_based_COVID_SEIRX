import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import networkx as nx
import numpy as np

colors = {'susceptible':'g',
		  'exposed':'orange', 
		  'infected':'red',
	      'recovered':'gray',
	      'quarantined':'blue',
	      'testable':'k'}

def get_pos(G, model):
	quarters = list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes]))
	num_patients = len([a for a in model.schedule.agents if \
		(a.type == 'patient' and a.quarter == 'Q1')])

	fixed = ['p{}'.format(i * num_patients + 1) for i in range(len(quarters))]

	if len(quarters) == 4:
		coords = [[-3, -3], [-3, 3], [3, 3], [3, -3]]

	elif len(quarters) == 3:
		coords = [[0, -3], [-3, 3], [3, 3]]

	elif len(quarters) == 2:
		coords = [[-3, 0], [3, 0]]
	else:
		coords = [[0, 0]]
	
	fixed_pos = {f:c for f, c in zip(fixed, coords)}

	pos = nx.drawing.layout.spring_layout(G, k=1.5, dim=2, weight='weight',
		fixed=fixed, pos=fixed_pos, scale=1, iterations=100)

	return pos

def draw_states(model, step, pos, ax):
	quarters = list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes]))
	quarters.sort()

	## draw patients
	patients = [a.unique_id for a in model.schedule.agents if a.type == 'patient']

	patient_states = model.datacollector.get_agent_vars_dataframe()
	patient_states = patient_states.iloc[patient_states.index.isin(patients, level=1)] 

	patient_states['color'] = patient_states['infection_state'].replace(colors)
	color_list = patient_states.loc[step].sort_index()['color']

	quarantine_states = patient_states.loc[step].sort_index()['quarantine_state']

	G = model.G
	nodes = list(G.nodes)
	nodes.sort()
	
	for u, v in list(G.edges):
		weight = G[u][v]['weight']**4 / 20
		try:
			ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], \
			color='k', linewidth=weight, zorder=1)
		except KeyError:
			print('warning: edge ({}, {}) not found in position map'.format(u, v))

	for n in nodes:
		if quarantine_states[n]:
			ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=50, zorder=2,\
	    	edgecolors='k', linewidths=2)
		else:
			ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=50, zorder=2)


	## draw employees
	employees = [a.unique_id for a in model.schedule.agents if a.type == 'employee']
	employee_states = model.datacollector.get_agent_vars_dataframe()
	employee_states = employee_states.iloc[employee_states.index.isin(employees, level=1)] 

	employee_states['color'] = employee_states['infection_state'].replace(colors)
	color_list = employee_states.loc[step].sort_index()['color']

	quarantine_states = employee_states.loc[step].sort_index()['quarantine_state']

	N_employee = model.employees_per_quarter

	x_min = np.asarray([a[0] for a in pos.values()]).min()
	x_max = np.asarray([a[0] for a in pos.values()]).max()
	y_min = np.asarray([a[1] for a in pos.values()]).min()
	y_max = np.asarray([a[1] for a in pos.values()]).max()

	x_step = x_max / 10
	x_start = x_max + 2* x_step
	y_step = (y_max - y_min) / N_employee

	if len(quarters) == 4:
	    text_pos = [[x_min, y_min],[x_min, y_max],[x_max, y_max],[x_max, y_min]]

	elif len(quarters) == 3:
	    text_pos = [[0, y_min],[x_min, y_max],[x_max, y_max]]

	elif len(quarters) == 2:
	    text_pos = [[x_min, 0],[x_max, 0]]
	else:
	    text_pos = [[0, y_max]]

	for quarter, tpos in zip(quarters, text_pos):
		ax.text(tpos[0], tpos[1], quarter)

	for j, quarter in enumerate(quarters):
	    xpos = x_start + j * x_step
	    employees = [a.unique_id for a in model.schedule.agents if \
	        (a.type == 'employee' and a.quarter == quarter)]

	    ax.text(xpos - x_step / 3, y_min - y_step / 8, quarter)

	    for i, e in enumerate(employees):
	        ypos = y_max - i % N_employee * y_step
	        if quarantine_states[e]:
	            ax.scatter(xpos, ypos, color=color_list[e], edgecolors='k', linewidths=2)
	        else:
	            ax.scatter(xpos, ypos, color=color_list[e])

	ax.text(x_start - x_step / 4, y_max + y_step, 'employees')
	ax.text(-0.2, y_max + y_step, 'patients')


	ax.set_frame_on(False)
	ax.set_xticks([])
	ax.set_yticks([])

	handles, labels = ax.get_legend_handles_labels()
	S_handle = plt.Line2D((0,1),(0,0), color=colors['susceptible'],
		 marker='o', linestyle='', markersize=8)
	E_handle = plt.Line2D((0,1),(0,0), color=colors['exposed'],
		 marker='o', linestyle='', markersize=8)
	I_handle = plt.Line2D((0,1),(0,0), color=colors['infected'],
		 marker='o', linestyle='', markersize=8)
	R_handle = plt.Line2D((0,1),(0,0), color=colors['recovered'],
		 marker='o', linestyle='', markersize=8)
	X_handle = plt.Line2D((0,1),(0,0), color='k',marker='o', 
		linestyle='', markersize=8, mfc='none', mew=2)
	#Create legend from custom artist/label lists
	legend = ax.legend([S_handle, E_handle, I_handle, R_handle, X_handle],
	          ['susceptible', 'exposed', 'infected', 'recovered', 'quarantined'],
	           fontsize=10, bbox_to_anchor=[1, 1, 0.25, 0])
	return legend

def draw_infection_timeline(model, agent_type, ax):
	pop_numbers = model.datacollector.get_model_vars_dataframe()
	if agent_type == 'patient':
		N = model.num_patients
	elif agent_type == 'employee':
		N = model.employees_per_quarter
		N_quarters = len(list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes])))
		N *= N_quarters
	else:
		print('unknown agent type!')

	pop_numbers['S_{}'.format(agent_type)] = N - pop_numbers['E_{}'.format(agent_type)]\
											   - pop_numbers['I_{}'.format(agent_type)]\
											   - pop_numbers['R_{}'.format(agent_type)]

	ax.plot(pop_numbers['S_{}'.format(agent_type)]/N,\
		 label='S', color=colors['susceptible'])
	ax.plot(pop_numbers['E_{}'.format(agent_type)]/N,\
		 label='E', color=colors['exposed'])
	ax.plot(pop_numbers['I_{}'.format(agent_type)]/N, \
		 label='I', color=colors['infected'])
	ax.plot(pop_numbers['I_symptomatic_{}'.format(agent_type)]/N, \
		 label='I symptomatic', color=colors['infected'], alpha=0.3)
	ax.plot(pop_numbers['R_{}'.format(agent_type)]/N, \
		 label='R', color=colors['recovered'])
	ax.plot(pop_numbers['X_{}'.format(agent_type)]/N, \
		 label='X', color=colors['quarantined'])
	ax.plot(pop_numbers['T_{}'.format(agent_type)]/N, '--',\
		 label='testable', color=colors['testable'])

	# draw screen lines
	for i, screen in enumerate(pop_numbers['screen_patients']):
		if screen:
			ax.plot([i, i], [0, 1], '--', color='green', alpha=0.3)
	for i, screen in enumerate(pop_numbers['screen_employees']):
		if screen:
			ax.plot([i, i], [0, 1], '--', color='red', alpha=0.3)


	# legend with custom artist for the screening lines
	handles, labels = ax.get_legend_handles_labels()
	patient_screen_handle = plt.Line2D((0,1),(0,0), color='green',
		 linestyle='--', alpha=0.3)
	employee_screen_handle = plt.Line2D((0,1),(0,0), color='red',
		 linestyle='--', alpha=0.3)

	#Create legend from custom artist/label lists
	ax.legend([handle for i,handle in enumerate(handles)] + \
			[patient_screen_handle, employee_screen_handle],
	          [label for i,label in enumerate(labels)] + \
	          ['patient screen', 'employee screen'], ncol=2, loc=9, fontsize=8)

	ax.set_xlabel('steps')
	ax.set_ylabel('probability density')
	ax.set_ylim(-0.05, 1.05)
	ax.xaxis.set_major_locator(MultipleLocator(20))
	ax.xaxis.set_minor_locator(MultipleLocator(5))
	ax.set_title('{} (N={})'.format(agent_type, N))
