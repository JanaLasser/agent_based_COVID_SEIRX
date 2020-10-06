import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

colors = {'susceptible':'g',
		  'exposed':'orange', 
		  'infected':'red',
	      'recovered':'gray',
	      'quarantined':'blue',
	      'testable':'k'}


def draw_states(model, step, pos, ax):
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
		weight = G[u][v]['weight']
		ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], \
			color='k', linewidth=weight, zorder=1)

	for n in nodes:
		if quarantine_states[n]:
			ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=50, zorder=2,\
	    	edgecolors='k', linewidths=2)
		else:
			#print('not quarantined')
			ax.scatter(pos[n][0], pos[n][1], color=color_list[n], s=50, zorder=2)

	## draw employees
	employees = [a.unique_id for a in model.schedule.agents if a.type == 'employee']
	employee_states = model.datacollector.get_agent_vars_dataframe()
	employee_states = employee_states.iloc[employee_states.index.isin(employees, level=1)] 

	employee_states['color'] = employee_states['infection_state'].replace(colors)
	color_list = employee_states.loc[step].sort_index()['color']

	quarantine_states = employee_states.loc[step].sort_index()['quarantine_state']

	N_employee = model.num_employees
	ncol = 10
	x_start = np.asarray([a[0] for a in pos.values()]).max()
	x_step = 0.2
	y_start = np.asarray([a[1] for a in pos.values()]).max()
	y_stop = np.asarray([a[1] for a in pos.values()]).min()
	y_step = (y_start - y_stop)/ncol

	for i, e in enumerate(employees):
		xpos = x_start + (int(i/ncol) + 1) * x_step
		ypos = y_start - i%ncol * y_step
		if quarantine_states[e]:
			ax.scatter(xpos, ypos, color=color_list[e], edgecolors='k', linewidths=2)
		else:
			ax.scatter(xpos, ypos, color=color_list[e])

	ax.text(x_start, y_stop - 0.2, 'employees')
	ax.text(-0.2, y_stop - 0.2, 'patients')


	ax.set_frame_on(False)
	ax.set_xticks([])
	ax.set_yticks([])

def draw_infection_timeline(model, agent_type, ax):
	pop_numbers = model.datacollector.get_model_vars_dataframe()
	if agent_type == 'patient':
		N = model.num_patients
	elif agent_type == 'employee':
		N = model.num_employees
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
	ax.plot(pop_numbers['R_{}'.format(agent_type)]/N, \
		 label='R', color=colors['recovered'])
	ax.plot(pop_numbers['X_{}'.format(agent_type)]/N, \
		 label='X', color=colors['quarantined'])
	ax.plot(pop_numbers['T_{}'.format(agent_type)]/N, '--',\
		 label='testable', color=colors['testable'])
	ax.legend()
	ax.set_xlabel('steps')
	ax.set_ylabel('pdf')
	ax.set_ylim(-0.05, 1.05)
	ax.set_title('{} (N={})'.format(agent_type, N))
