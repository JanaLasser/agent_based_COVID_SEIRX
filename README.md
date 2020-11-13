# Agent based simulation of the spread of COVID-19 in nursing homes
**Author: Jana Lasser, Complexity Science Hub Vienna (lasser@csh.ac.at)**

A simple simulation to explore the spread of COVID-19 in nursing homes via agent-based modeling (ABM) of residents and employees of nursing homes. The model follows an SEIRX approach, building on the agent based simulation framework [mesa](https://mesa.readthedocs.io/en/master/) in which agents can be susceptible (S), exposed (E), infected (I), removed (R) or quarantined (X). The model offers the possibility to explore the effectiveness of various testing, tracing and quarantine strategies and implements an empirically measured contact network of nursing home residents.  

<img alt="Illustrative figure of infection spread in a nursing home" src="img/fig.png?raw=true" height="500" width="800" align="center">



**This software is under development and intended to respond rapidly to the current situation. Please use it with caution and bear in mind that there might be bugs**

Reference:  

_Lasser, J. (2020). Agent based simulation of the spread of COVID-19 in nursing homes. DOI: 10.5281/zenodo.4106334_

## Simulation design

### Infections
We simulate two types of agents (residents and employees) that live and work in nursing homes. Infections are introduced through employees (or residents, or both) that have a certain probability to become an index case. Residents have an explicitly defined contact network that is defined through their room neighbors, table neighbors at joint meals and residents that live in the same living area of the nursing home. The contact network defines which residents interact with which other residents and different contact venues modulate infection transmission risk (for example infection risk is drastically increased for roommates). We provide several exemplary contact networks (see ```data/```), representing different architectures for long-time care facilities with different numbers of living quarters. Contact networks are stored as a [networkx](https://networkx.org/) graph with edge attributes for different interaction venues. Employees have no explicitly defined contact network and interact with all residents and all other employees in the same living quarter.  
In every step (day) of the simulation, agents interact according to their interaction rules and can transmit the infection. Depending on its infection state, an agent has one of five states: susceptible (S), exposed (E), infected (I), removed (R) or quarantined (X). In addition, agents can develop symptoms.

### Testing
Agents can be testable, depending on the period of time they have already been infected and the test used. Agents can have a pending test result (tested), which will prevent them from getting tested again before the pending result arrives. Tests take a certain amount of time to return results, depending on the chosen time until test result. Tests can return positive or negative results, depending on whether the agent was testable at the time of testing and on the sensitivity/specificity of the chosen test.

### Containment strategies
Next to the transmission of the infection, the nursing home implements containment measures (quarantine) and a testing and tracing strategy to curb the spread of the virus among its residents and employees. Symptomatic cases are immediately quarantined and tested. Once a positive test result is returned, all close contacts (K1 contact persons) of the positive agent are immediately quarantined. The definition of "close contact" is also up for specification. By default, room and table mates of residents are defined as "close contact", whereas employees have no specific close contacts. If "quarters" is defined as additional K1 contact area, all residents residing in the same living quarters as the positive case and all employees working in the same living quarters will also be quarantined.  
If there is a positive test result, the nursing home can launch a "background screen" of its population, testing all its employees and residents. A background screen is followed by a "follow up screen" with a to-be-specified time-delay (should be close to the exposure duration, default=5). Next to population screening that is triggered by positive test results, the nursing home can do "preventive screens" in set intervals. The intervals for these screens can be specified and can be chosen differently for the residents and employees.

### Implementation
* SEIRX model parameters and parameters for the testing strategy are to be passed to the SEIRX model instance at time of creation, if values other than the specified default values should be used.
* The base-class for agents defined in ```agent_SEIRX.py``` implements agent states and counters and functions necessary for simulating contacts between agents and advancing states. 
* There are two agent types: resident and employee, which are implemented in two separate classes which inherit from the agent base-class. These two classes are specified in ```agent_resident.py``` and ```agent_employee.py``` and implement different contact networks and transmission risks, depending on the agent type.
* The testing strategy is contained in a class different from the SEIRX model but is created with parameters passed through the SEIRX constructor. This is to keep parameters and information related to testing and tracing in one place, separate from the infection dynamics model. The testing class is implemented in ```testing_strategy.py```, which also stores information on the sensitivity and specificity of a range of tests (can be easily extended by additional tests).
* The module ```viz.py``` provides some custom visualization utility to plot infection time-lines and agent states on a network

## Assumptions
The assumptions made by the model to simplify the dynamics of infection spread and estimates of relevant parameters of virus spread are detailed in the following.

### Parameters
* **Exposure time** (latent time): The time from transmission to becoming infectious is approximated to be five days ([Linton et al. 2020](https://www.mdpi.com/2077-0383/9/2/538), [Lauer et al. 2020](https://www.acpjournals.org/doi/full/10.7326/M20-0504)).
* **Infectivity duration**: An infected agent is assumed to be infectious for 10 days after becoming infections ([Walsh et al. 2020](https://doi.org/10.1016/j.jinf.2020.06.067)).
* **Time until symptoms** (incubation time): Humans infected with SARS-CoV2 that develop a clinical course of the disease usually develop symptoms only after they become infectious. We assume the length of the time period between becoming infectious and developing symptoms to be two days ([He et al. 2020](https://www.nature.com/articles/s41591-020-0869-5)).
* **Infectiousness**: We assume that infectiousness stays constantly high in the two days before symptoms onset and decreases monotonically after symptoms onset until it reaches zero 8 days after symptoms onset ([He et al. 2020](https://doi.org/10.1038/s41591-020-0869-5), [Walsh et al. 2020](10.1016/j.jinf.2020.06.067)).
* **Symptom probability**: A large proportion of infections with SARS-CoV2 take a subclinical (i.e. asymptomatic) course. We assume that this is true for 40% of infections [(Nikolai et al. 2020)](https://www.sciencedirect.com/science/article/pii/S1201971220307062#bib0100). Nevertheless, a differentiation between residents and personnell might be warranted, with a lower probability to remain asymptomatic for residents, as evidence is mounting that age correlates negatively with the probability to have an asymptomatic course [(McMichael et al. 2020)](https://www.nejm.org/doi/full/10.1056/NEJMoa2005412)
* **Infectiousness of asymptomatic cases**: We assume that the infectiousness of asymptomatic persons is the same as the infectiousness of symptomatic cases ([Nikolai et al. 2020](https://www.sciencedirect.com/science/article/pii/S1201971220307062#bib0100), [Walsh et al. 2020](https://doi.org/10.1016/j.jinf.2020.06.067)). 
* **Transmission risk**: The simulation defines transmission risks between the two groups of agents and within a group of agents. Furthermore, transmission risk is increased for residents that share a room (by a factor of 2) and for residents that eat on the same table (by a factor of 1.5). Transmission risks in the model are calibrated such that the basic reproduction number R_0 approaches 2.5 to 3 (the value currently reported for SARS-Cov2 spread in the literature, see [Li et al. 2020](https://doi.org/10.1056/NEJMoa2001316), [Wu et al. 2020](http://www.sciencedirect.com/science/article/pii/S0140673620302609) ) in a system without interventions.

### Interaction and intervention assumptions
* **Time**: We assume that one model simulation step corresponds to one day. Simulation parameters are chosen accordingly.
* **Tests**: The class ```testing_strategy.py``` implements a variety of different tests, including antigen, PCR and LAMP tests. These tests differ regarding their sensitivity, specificity, the time a test takes until it delivers a result, the time it takes until an infected agent is testable and the time an infected agent stays testable. The test used for testing can be specified at model setup (default is same day PCR test).
* **Quarantine duration**: We assume that agents that were tested positive are isolated (quarantined) for 14 days, according to [recommendations by the WHO](https://www.who.int/publications/i/item/considerations-for-quarantine-of-individuals-in-the-context-of-containment-for-coronavirus-disease-(covid-19)).
* **Index cases**: There are several ways to introduce index cases to the facility: One way is to introduce a single index case through an employee or patient and then simulate the ensuing outbreak in the facility. The second option is to set a probability of an agent to become an index case in each simulation step and choose whether employees, patients or both agent groups can become index cases.
* **Interaction of residents with residents**: We assume that every resident interacts with every other resident that lives in the same living area of the facility every day (simulation step) and has a basic probability to transmit an infection. The probability is increased for closer interactions (living in the same room, eating at the same table).
* **Interaction of employees with residents**: We assume that every employee interacts with every resident every day and has a basic probability to transmit an infection.
* **Interaction of employees with employees**: We assume that every employee interacts with every other employee every day and has a basic probability to transmit an infection.

## Installation (Linux)
1. Clone the repository:  
```git clone https://github.com/JanaLasser/SEIRX_nursing_homes.git```  
2. Create and activate a virtual environment  
```python3 -m venv .my_venv```  
```source .my_venv/bin/activate```  
3. Update pip  
``` pip install --upgrade pip```  
4. Install dependencies  
```pip install -r requirements.txt```  

## Running the simulation
The following requires the activation of the virtual environment you created during installation  
```source .my_venv/bin/activate```

I provide an exemplary [Jupyter Notebook](https://github.com/JanaLasser/SEIRX_nursing_homes/blob/master/example.ipynb) that illustrates how a simulation model is set up and run, how results are visualised and how data from a model run can be collected.  

I also provide the [Jupyter Notebook](https://github.com/JanaLasser/SEIRX_nursing_homes/blob/master/screening_frequency_data_creation.ipynb) used to run the simulations and create the data used in the publication **Agent-based simulations for optimized prevention of the spread of SARS-CoV-2 in nursing homes** as well as the [Jupyter Notebook](https://github.com/JanaLasser/SEIRX_nursing_homes/blob/master/screening_frequency_analysis.ipynb) used to create the heatmaps for the different analysed screnarios from the simulation data.

## Acknowledgements
I would like to thank [Peter Klimek](https://www.csh.ac.at/researcher/peter-klimek/) from Complexity Science Hub Vienna and Thomas Wochele-Thoma from [Caritas Austria](https://www.caritas.at/) for the fruitful discussions that led to the development of this project.

## References
Linton, N. M., Kobayashi, T., Yang, Y., Hayashi, K., Akhmetzhanov, A. R., Jung, S. M., ... & Nishiura, H. (2020). Incubation period and other epidemiological characteristics of 2019 novel coronavirus infections with right truncation: a statistical analysis of publicly available case data. Journal of clinical medicine, 9(2), 538. [DOI: 10.3390/jcm9020538](https://doi.org/10.3390/jcm9020538)  

Lauer, S. A., Grantz, K. H., Bi, Q., Jones, F. K., Zheng, Q., Meredith, H. R., ... & Lessler, J. (2020). The incubation period of coronavirus disease 2019 (COVID-19) from publicly reported confirmed cases: estimation and application. Annals of internal medicine, 172(9), 577-582. [DOI: 10.7326/M20-0504](https://doi.org/10.7326/M20-0504)  

Walsh, K. A., Jordan, K., Clyne, B., Rohde, D., Drummond, L., Byrne, P., ... & O'Neill, M. (2020). SARS-CoV-2 detection, viral load and infectivity over the course of an infection: SARS-CoV-2 detection, viral load and infectivity. Journal of Infection. [DOI: 10.1016/j.jinf.2020.06.067](10.1016/j.jinf.2020.06.067)  

He, X., Lau, E. H., Wu, P., Deng, X., Wang, J., Hao, X., ... & Mo, X. (2020). Temporal dynamics in viral shedding and transmissibility of COVID-19. Nature medicine, 26(5), 672-675. [DOI: 10.1038/s41591-020-0869-5](https://doi.org/10.1038/s41591-020-0869-5)  

Nikolai, L. A., Meyer, C. G., Kremsner, P. G., & Velavan, T. P. (2020). Asymptomatic SARS Coronavirus 2 infection: Invisible yet invincible. International Journal of Infectious Diseases. [DOI: 10.1016/j.ijid.2020.08.076](https://doi.org/10.1016/j.ijid.2020.08.076)  

McMichael, T. M., Currie, D. W., Clark, S., Pogosjans, S., Kay, M., Schwartz, N. G., ... & Ferro, J. (2020). Epidemiology of Covid-19 in a long-term care facility in King County, Washington. New England Journal of Medicine, 382(21), 2005-2011. [DOI: 10.1056/NEJMoa2005412](https://doi.org/10.1056/NEJMoa2005412)  

Li, Q., Guan, X., Wu, P., Wang, X., Zhou, L., Tong, Y., ... & Xing, X. (2020). Early transmission dynamics in Wuhan, China, of novel coronavirus–infected pneumonia. New England Journal of Medicine. [DOI: 10.1056/NEJMoa2001316](https://doi.org/10.1056/NEJMoa2001316)  

Wu, J. T., Leung, K., & Leung, G. M. (2020). Nowcasting and forecasting the potential domestic and international spread of the 2019-nCoV outbreak originating in Wuhan, China: a modelling study. The Lancet, 395(10225), 689-697. [DOI: 10.1016/S0140-6736(20)30260-9](https://doi.org/10.1016/S0140-6736(20)30260-9)  
