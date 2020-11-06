import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import networkx as nx
import numpy as np

colors = {'susceptible':'g',
		  'exposed':'orange', 
		  'infectious':'red',
	      'recovered':'gray',
	      'quarantined':'blue',
	      'testable':'k'}

def get_pos(G, model):
	quarters = list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes]))
	num_residents = len([a for a in model.schedule.agents if \
		(a.type == 'resident' and a.quarter == 'Q1')])

	fixed = ['p{}'.format(i * num_residents + 1) for i in range(len(quarters))]

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

def draw_states(model, step, pos, pat_ax, emp_ax, leg_ax):
	quarters = list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes]))
	quarters.sort()

	## draw residents
	residents = [a.unique_id for a in model.schedule.agents if a.type == 'resident']

	resident_states = model.datacollector.get_agent_vars_dataframe()
	resident_states = resident_states.iloc[resident_states.index.isin(residents, level=1)] 

	resident_states['color'] = resident_states['infection_state'].replace(colors)
	color_list = resident_states.loc[step].sort_index()['color']

	quarantine_states = resident_states.loc[step].sort_index()['quarantine_state']

	G = model.G
	nodes = list(G.nodes)
	nodes.sort()

	x_max = np.asarray([a[0] for a in pos.values()]).max()
	x_min = np.asarray([a[0] for a in pos.values()]).min()
	x_extent = x_max + np.abs(x_min)

	y_min = np.asarray([a[1] for a in pos.values()]).min()
	y_max = np.asarray([a[1] for a in pos.values()]).max()
	y_step = (y_max + np.abs(y_min)) / 10

	pat_ax.set_ylim(y_min - y_step/2, y_max + y_step) 
	pat_ax.text(x_max - x_extent / 2 - 0.1, y_max + y_step / 2, 'residents', fontsize=14)
	
	for u, v in list(G.edges):
		weight = G[u][v]['weight']**2 / 5
		try:
			pat_ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], \
			color='k', linewidth=weight, zorder=1)
		except KeyError:
			print('warning: edge ({}, {}) not found in position map'.format(u, v))

	resident_handles = {}
	for n in nodes:
		if quarantine_states[n]:
			handle = pat_ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=150, zorder=2,
			edgecolors='k', linewidth=3)
			resident_handles.update({n:handle})
		else:
			handle = pat_ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=150, zorder=2)
			resident_handles.update({n:handle})




	## draw employees
	employees = [a.unique_id for a in model.schedule.agents if a.type == 'employee']
	employee_states = model.datacollector.get_agent_vars_dataframe()
	employee_states = employee_states.iloc[employee_states.index.isin(employees, level=1)] 

	employee_states['color'] = employee_states['infection_state'].replace(colors)
	color_list = employee_states.loc[step].sort_index()['color']
	quarantine_states = employee_states.loc[step].sort_index()['quarantine_state']
	N_employee = model.employees_per_quarter

	employee_handles = {}

	emp_ax.set_xlim(-0.5, len(quarters) - 1 + 0.5)
	emp_ax.set_ylim(-1, N_employee)
	emp_ax.text(0 - 0.25,  N_employee - 0.45, 'employees', fontsize=14)

	for j, quarter in enumerate(quarters):
	    employees = [a.unique_id for a in model.schedule.agents if \
	        (a.type == 'employee' and a.quarter == quarter)]

	    #emp_ax.text(j - 0.065, -0.8, quarter, fontsize=14)

	    for i, e in enumerate(employees):
	        ypos = i
	        if quarantine_states[e]:
	            handle = emp_ax.scatter(j, i, color=color_list[e], \
	            	s=100, edgecolors='k', linewidth=3)
	            employee_handles.update({e:handle})
	        else:
	            handle = emp_ax.scatter(j, i, color=color_list[e], s=150)
	            employee_handles.update({e:handle})


	for ax in [pat_ax, emp_ax, leg_ax]:
		ax.set_xticks([])
		ax.set_yticks([])
		ax.set_frame_on(False)

	handles, labels = pat_ax.get_legend_handles_labels()
	S_handle = plt.Line2D((0,1),(0,0), color=colors['susceptible'],
		 marker='o', linestyle='', markersize=15)
	E_handle = plt.Line2D((0,1),(0,0), color=colors['exposed'],
		 marker='o', linestyle='', markersize=15)
	I_handle = plt.Line2D((0,1),(0,0), color=colors['infectious'],
		 marker='o', linestyle='', markersize=15)
	R_handle = plt.Line2D((0,1),(0,0), color=colors['recovered'],
		 marker='o', linestyle='', markersize=15)
	X_handle = plt.Line2D((0,1),(0,0), color='k',marker='o', 
		linestyle='', markersize=15, mfc='none', mew=3)
	#Create legend from custom artist/label lists
	legend = leg_ax.legend([S_handle, E_handle, I_handle, R_handle, X_handle],
	          ['susceptible', 'exposed', 'infected', 'recovered', 'quarantined'],
	           fontsize=14, loc=2)

	step_text_handle = leg_ax.text(0.32, 0.7, 'day {}'.format(step), fontsize=14)

	return legend, employee_handles, resident_handles, step_text_handle

def draw_infection_timeline(model, agent_type, ax):
	linewidth = 3
	pop_numbers = model.datacollector.get_model_vars_dataframe()
	if agent_type == 'resident':
		N = model.num_residents
	elif agent_type == 'employee':
		N = model.employees_per_quarter
		N_quarters = len(list(set([model.G.nodes[ID]['quarter'] for ID in model.G.nodes])))
		N *= N_quarters
	else:
		print('unknown agent type!')

	pop_numbers['S_{}'.format(agent_type)] = N - pop_numbers['E_{}'.format(agent_type)]\
											   - pop_numbers['I_{}'.format(agent_type)]\
											   - pop_numbers['R_{}'.format(agent_type)]

	ax.plot(pop_numbers['S_{}'.format(agent_type)]/N * 100,\
		 label='S', color=colors['susceptible'], linewidth=linewidth, zorder=1)

	ax.plot(pop_numbers['E_{}'.format(agent_type)]/N* 100,\
		 label='E', color=colors['exposed'], linewidth=linewidth, zorder=1)

	ax.plot(pop_numbers['I_{}'.format(agent_type)]/N* 100, \
		 label='$I_2$', color=colors['infectious'],
		  linewidth=linewidth, zorder=1)

	ax.plot(pop_numbers['I_{}'.format(agent_type)]/N* 100, \
		 label='$I_2$', color=colors['infectious'], alpha=0.3,
		  linewidth=linewidth, zorder=1)

	ax.plot(pop_numbers['R_{}'.format(agent_type)]/N* 100, \
		 label='R', color=colors['recovered'], linewidth=linewidth, zorder=1)

	ax.plot(pop_numbers['X_{}'.format(agent_type)]/N* 100, \
		 label='X', color=colors['quarantined'], linewidth=linewidth, zorder=1)

	# draw screen lines
	for i, screen in enumerate(pop_numbers['screen_residents']):
		if screen:
			ax.plot([i, i], [0, 100], color='FireBrick', alpha=0.3,
			 linewidth=7, zorder=2)
	for i, screen in enumerate(pop_numbers['screen_employees']):
		if screen:
			ax.plot([i, i], [0, 100], color='DarkBlue', alpha=0.3, linewidth=2,
				zorder=2)


	# legend with custom artist for the screening lines
	handles, labels = ax.get_legend_handles_labels()
	resident_screen_handle = plt.Line2D((0,1),(0,0), color='FireBrick'
		, alpha=0.3, linewidth=7)
	employee_screen_handle = plt.Line2D((0,1),(0,0), color='DarkBlue',
		 linewidth=2, alpha=0.3)

	#Create legend from custom artist/label lists
	ax.legend([handle for i,handle in enumerate(handles)] + \
			[resident_screen_handle, employee_screen_handle],
	          [label for i,label in enumerate(labels)] + \
	          ['resident screen', 'employee screen'], ncol=2, loc=6, 
	          fontsize=14, bbox_to_anchor=[0, 0.55])

	ax.set_xlabel('steps', fontsize=20)
	ax.set_ylabel('% of population', fontsize=20)
	ax.set_ylim(-1, 100)
	ax.set_xlim(0, 60)
	ax.xaxis.set_major_locator(MultipleLocator(10))
	ax.xaxis.set_minor_locator(MultipleLocator(1))
	ax.tick_params(axis='both', which='major', labelsize=14)

	ax.set_title('{}s (N={})'.format(agent_type, N), fontsize=20)
