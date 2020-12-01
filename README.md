# Agent based simulation of the spread of COVID-19 in confined spaces
**Author: Jana Lasser, Complexity Science Hub Vienna (lasser@csh.ac.at)**

A simple simulation to explore the spread of COVID-19 in confined spaces such as nursing homes or schools via agent-based modeling (ABM) of agents living and working in such spaces. The model follows an SEIRX approach, building on the agent based simulation framework [mesa](https://mesa.readthedocs.io/en/master/) in which agents can be susceptible (S), exposed (E), infected (I), removed (R) or quarantined (X). The model offers the possibility to explore the effectiveness of various testing, tracing and quarantine strategies and operates on explicitly defined contact networks between agents.  

<img alt="Illustrative figure of infection spread in a nursing home" src="img/fig.png?raw=true" height="500" width="800" align="center">



**This software is under development and intended to respond rapidly to the current situation. Please use it with caution and bear in mind that there might be bugs**

Reference:  

_Lasser, J. (2020). Agent based simulation of the spread of COVID-19 in nursing homes. [DOI](https://doi.org/10.5281/zenodo.4275533): 10.5281/zenodo.4275533_

## Simulation design

### Infections
Simulations can have several types of agents, for example residents & employees in nursing homes, or teachers, students and family members in schools. Infections are introduced through agents that have a certain probability to become an index case. The contact network defines which agents interact with which other agents and different contact venues modulate infection transmission risk between "close" and "very far". Contact networks are stored as a [networkx](https://networkx.org/) graph with edge attributes for different interaction venues. In every step (day) of the simulation, agents interact according to the contact network and can transmit the infection. Depending on its infection state, an agent has one of four states: susceptible (S), exposed (E), infected (I) or removed (R). In addition, agents can be quarantined (X) and develop symptoms when they are infected.

Transmissions occur at random. These random events are scaled by the ```transmission_risk``` of the transmitting agent, which can be specified for each agent group separately, to account for example for agent age or cautionary behaviour, such as mask-wearing. Transmission is also modulated by the ```reception_risk``` of the receiving agent, which again can be specified for each agent group separately to account for age and cautionary behaviour. These parameters need to be chosen or calibrated to reflect real-world infection dynamics.

### Containment strategies
Next to the transmission of the infection, containment measures (quarantine) and a testing and tracing strategy can be implemented to curb the spread of the virus. If ```testing='diagnostic'```, symptomatic cases are immediately quarantined and tested. Once a positive test result is returned, all close contacts (K1 contact persons) of the positive agent are immediately quarantined. The definition of "close contact" has to be specified through the contact intensity (edge attributes) of the contact network. For example, if "close contact" is chosen to include agents that have "close" and "intermediate" contact, according to the contact network, all agents which are connected to a positively tested agent via links that have the attribute "close" or "intermediate" will be quarantined upon arrival of the test result. Quarantined agents will stay in quarantine for ```quarantine_duration``` days if ```liberating_testing=False``` (default). If ```liberating_testing = True```, quarantined agents will be released from quarantine if they return a negative test result.

If ```testing='background'```, in addition to testing of single symptomatic agents, if there is a positive test result, a "background screen" of the population will be launched. In the nursing home scenario, all residents and employees are tested in such a background screen. In the school scenario, all teachers and students (but not family members) are tested in such a background screen. If a ```follow_up_testing```-interval is specified, each background screen is followed by a "follow up screen" with the specified time-delay, testing the same agent groups as in the background screen.

Next to population screening that is triggered by positive test results, if ```testing='preventive'```, preventive screens will be performed independently of diagnostic testing and background/follow-up screens. These preventive screens are performed in given intervals, which are to be specified for each agent group using the parameter ```screening_interval```.

### Testing
Agents can be testable, depending on the period of time they have already been infected – which determines the viral load – and the test used. Agents can have a pending test result (tested), which will prevent them from getting tested again before the pending result arrives. Tests take a certain amount of time to return results, depending on the chosen testing technology. Tests can return positive or negative results, depending on whether the agent was testable at the time of testing (had enough virus load) and on the sensitivity/specificity of the chosen test. Test technologies for preventive screening and diagnostic testing (diagnostic tests, background screens and follow-up screens) can be specified separately. A test technology always specifies the test's sensitivity, specificity and test result turnover time.

### Implementation
* SEIRX model parameters and parameters for the testing strategy are to be passed to the SEIRX model instance at time of creation, if values other than the specified default values should be used. Every scenario (so far: nursing homes and schools) implements its own model class which inherits from ```model_SEIRX.py```, where the main infection dynamics and testing/tracing are implemented. The scenario-specific models only specify scenario-specific data collection functions and (if needed) a custom step function.
* Similarly to the model, agents have a base-class defined in ```agent_SEIRX.py```, which implements agent states and counters and functions necessary for simulating contacts between agents and advancing states. Different agent types needed in the scenarios inherit from this base class and might implement additional functionality.
* Currently there are five agent types: resident and employee (nursing home scenario) and teacher, student and family member (school scenario). These agent types are implemented in separate classes which inherit from the agent base-class. 
* The testing strategy is contained in ```testing_strategy.py```, a class different from the SEIRX base model but is created with parameters passed through the SEIRX constructor. This is to keep parameters and information related to testing and tracing in one place, separate from the infection dynamics model. The testing class also stores information on the sensitivity, specificity and turnover time of a range of tests and can be easily extended to include additional testing technologies.
* The module ```analysis_functions.py``` provides a range of functions to analyse data from model runs.
* The module ```viz.py``` provides some custom visualization utility to plot infection time-lines and agent states on a network, given a model instance.

## Applications
### Nursing homes
Nursing homes implement agents types ```resident``` and ```employee```, as well as the ```model_nursing_home``` (all located in the ```nursing_home``` sub-folder).  
The contact networks for nursing homes are specified through resident relations in the homes (room neighbors, table neighbors at joint meals, other shared areas). Employees interact with all other employees and all residents in the same living quarter (```unit```) of the nursing home every day. We provide several exemplary contact networks (see ```data/nursing_homes```), representing different architectures of nursing homes with different numbers of living quarters. These contact networks are abstractions of empirically determined interaction relations in Austrian nursing homes. By default, resident roommates are defined as "close contact" and are quarantined if a resident sharing the same room is tested positive, whereas employees have no specific close contacts. 

### Schools
Schools implement agent types ```teachers```, ```students``` and ```family_members``` of students, as well as the ```model_school``` (all located in the ```school``` sub-folder).  

The contact networks for schools are generated to reflect common structures in Austrian schools in a [jupyter notebook](https://github.com/JanaLasser/agent_based_COVID_SEIRX/blob/dev/school/construct_school_network.ipynb) provided in this repository. Schools are defined by the number of classes they have, the number of students per class, the number of floors these classes are distributed over, and the school type which determines the age structure of the students in the school. A school will have a number of teachers that corresponds to twice the number of classes (which corresponds to approximately the class/teacher ratio in Austrian schools). Every student will have a number of family members drawn from a distribution of household sizes corresponding to Austrian house holds.

In addition to specifying the agent type, nodes also have node attributes that introduce additional parameters into the transmission dynamics: students are part of a ```class``` (```unit```), which largely defines their contact network. Classes are assigned to ```floors``` and have "neighbouring classes" that are situated on the same floor. A small number of random contacts between neighbouring classes are added to the student interaction network, next to the interactions within each class. Teachers have a schedule that specifies the classes they interact with.  

Students within the same class have ```intermediate``` contacts to each other (complete graph). Teachers teaching students in a class have ```intermediate``` contacts to all students in the class. Teachers also have ```intermediate``` contacts to all other teachers (complete graph among teachers), since they regularly meet in the faculty room. Some students have ```far``` contacts to students from other classes, reflecting friendships and passing contacts in hallways to members of other classes. Students also have ```close``` contacts to members of their household. There are no contacts between teachers and family members.  

Students also have an ```age``` that modulates both their ```transmission risk``` and their ```reception risk```. 

## Assumptions
The assumptions made by the model to simplify the dynamics of infection spread and estimates of relevant parameters of virus spread are detailed in the following.

### Parameters
* **Exposure time** (latent time): The time from transmission to becoming infectious is approximated to be $5\pm 1.9$ days ([Ferreti et al. 2020](https://doi.org/10.1126/science.abb6936), [Linton et al. 2020](https://www.mdpi.com/2077-0383/9/2/538), [Lauer et al. 2020](https://www.acpjournals.org/doi/full/10.7326/M20-0504)). Adjust this parameter through the ```exposure_duration``` variable by supplying either a mean duration or the mean and standard deviation of a Weibull distribution.

* **Infectivity duration**: An infected agent is assumed to be infectious for 10.91 $\pm$ 3.95 days after becoming infections ([Walsh et al. 2020](https://doi.org/10.1016/j.jinf.2020.06.067), [You et al. 2020](https://www.sciencedirect.com/science/article/abs/pii/S1438463920302133?via%3Dihub)). Adjust this parameter through the ```infection_duration``` variable by supplying either a mean duration or the mean and standard deviation of a Weibull distribution.

* **Time until symptoms** (incubation time): Humans infected with SARS-CoV2 that develop a clinical course of the disease usually develop symptoms only after they become infectious. We assume the length of the time period between transmission and developing symptoms to be $6.4\pm 0.8$ days ([He et al. 2020](https://www.nature.com/articles/s41591-020-0869-5), [Backer et al. 2020](https://doi.org/10.2807/1560-7917.ES.2020.25.5.2000062)). Adjust this parameter through the ```time_until_symptoms``` variable by supplying either a mean duration or the mean and standard deviation of a Weibull distribution.

* **Infectiousness**: We assume that infectiousness stays constantly high in the two days before symptoms onset and decreases monotonically after symptoms onset until it reaches zero 8 days after symptoms onset ([He et al. 2020](https://doi.org/10.1038/s41591-020-0869-5), [Walsh et al. 2020](10.1016/j.jinf.2020.06.067)).

* **Symptom probability**: A large proportion of infections with SARS-CoV2 take a subclinical (i.e. asymptomatic) course. We assume that this is true for 40% of infections [(Nikolai et al. 2020)](https://www.sciencedirect.com/science/article/pii/S1201971220307062#bib0100). Nevertheless, a differentiation between residents and personnell might be warranted, with a lower probability to remain asymptomatic for residents, as evidence is mounting that age correlates negatively with the probability to have an asymptomatic course [(McMichael et al. 2020)](https://www.nejm.org/doi/full/10.1056/NEJMoa2005412). Adjust this parameter through the ```symptom_probability``` variable of each agent group.

* **Infectiousness of asymptomatic cases**: We assume that the infectiousness of asymptomatic persons is the same as the infectiousness of symptomatic cases ([Nikolai et al. 2020](https://www.sciencedirect.com/science/article/pii/S1201971220307062#bib0100), [Walsh et al. 2020](https://doi.org/10.1016/j.jinf.2020.06.067)). Adjust this parameter through the ```subclinical_modifier``` variable.

* **Transmission risk**: For every agent group, a base transmission risk ```transmission_risk``` has to be specified. Transmission risk for a transmission between agents is modulated by the closeness of their contact. The modulation can be specified through the ```infection_risk_contact_type_weights``` – a dictionary, that specifies weights for ```very_far```, ```far```, ```intermediate``` and ```close``` contacts. Transmission risks are also modulated by agent age (if it is specified), to account for lower lung volumes of children [NEEDS A REFERENCE], and by masks (see "mask effectiveness" below). As a note of caution: evidence for the reduced contraction of SARS-CoV-2 in children is still very scarce and the assumptions here are very speculative. Transmission risks in the nursing home model are calibrated such that the outbreak characteristics match the observed empirical data of outbreaks in Austrian nursing homes. In these simulations without interventions, the basic reproduction number R_0 approaches 2.5 to 3 if the index case is introduced through an employee (the value currently reported for SARS-Cov2 spread in the literature, see [Li et al. 2020](https://doi.org/10.1056/NEJMoa2001316), [Wu et al. 2020](http://www.sciencedirect.com/science/article/pii/S0140673620302609) ). If the index case is introduced through a resident, the basic reproduction number lies between 4 and 5, which reflects the confined living conditions and close contacts between residents in nursing homes.

* **Reception risk**: For every agent group, a base reception risk ```reception_risk``` has to be specified. The reception risk is modulated by agent age (if specified), to account for the lower number of receptors responsible for contracting SARS-CoV-2 in children ([Sharif-Askari et al. 2020](https://dx.doi.org/10.1016%2Fj.omtm.2020.05.013)). As a note of caution: evidence for the reduced contraction of SARS-CoV-2 in children is still very scarce and the assumptions here are very speculative.
* **Mask effectiveness**: If agents wear masks, we reduce their transmission risk by 50% and their reception risk by 30%, which are conservative estimates based on the study by [Pan et al. 2020](https://doi.org/10.1101/2020.11.18.20233353).

### Interaction and intervention assumptions
* **Time**: We assume that one model simulation step corresponds to one day. Simulation parameters are chosen accordingly.
* **Tests**: The class ```testing_strategy.py``` implements a variety of different tests, including antigen, PCR and LAMP tests. These tests differ regarding their sensitivity, specificity, the time a test takes until it delivers a result, the time it takes until an infected agent is testable and the time an infected agent stays testable. The test used for diagnostic and preventive testing can be specified at model setup (default is one day turnover PCR test).
* **Quarantine duration**: We assume that agents that were tested positive are isolated (quarantined) for 14 days, according to [recommendations by the WHO](https://www.who.int/publications/i/item/considerations-for-quarantine-of-individuals-in-the-context-of-containment-for-coronavirus-disease-(covid-19)). This time can be changed by supplying the parameter ```quarantine_duration``` to the simulation.
* **Index cases**: There are several ways to introduce index cases to a facility: One way is to introduce a single index case through an agent (specify the agent group through the ```index_case``` parameter) and then simulate the ensuing outbreak in the facility. The second option is to set a probability of an agent to become an index case in each simulation step and choose whether employees, patients or both agent groups can become index cases. To use this option, specify ```index_case='continuous'``` and set the ```index_probability``` parameter to a non-zero risk for the desired agent groups.

## Installation (Linux)
Note: this is currently not working because the dependencies are buggy. This simulation uses the standard scientific python stack (python 3.7, numpy, pandas, matplotlib) plus networkx and mesa. If these libraries are installed, the simulation should work out of the box.

1. Clone the repository:  
```git clone https://github.com/JanaLasser/agent_based_COVID_SEIRX.git```  
Note: if you want to clone the development branch, use  
```git clone --branch dev https://github.com/JanaLasser/agent_based_COVID_SEIRX.git``` 
2. Navigate to the repository
```cd agent_based_COVID_SEIRX```
3. Create and activate a virtual environment. Make sure you use a Python version >= 3.8
```virtualenv -p=/usr/bin/python3.8 .my_venv```  
```source .my_venv/bin/activate```  
4. Update pip  
``` pip install --upgrade pip```  
5. Install dependencies  
```pip install -r requirements.txt```  

## Running the simulation
The following requires the activation of the virtual environment you created during installation  
```source .my_venv/bin/activate```

I provide exemplary Jupyter Notebooks for [nursing homes](https://github.com/JanaLasser/agent_based_COVID_SEIRX/blob/dev/nursing_home/example_nursing_home.ipynb) and [schools](https://github.com/JanaLasser/agent_based_COVID_SEIRX/blob/dev/school/example_school.ipynb) that illustrate how a simulation model is set up and run for these two applications, how results are visualised and how data from a model run can be collected. Run the example notebook from the terminal:  
```jupyter-notebook nursing_home/example_nursing_home.ipynb```  
or  

```jupyter-notebook school/example_school.ipynb```

I also provide the [Jupyter Notebook](https://github.com/JanaLasser/agent_based_COVID_SEIRX/blob/dev/nursing_home/screening_frequency_data_creation.ipynb) used to run the simulations and create the data used in the publication **Agent-based simulations for optimized prevention of the spread of SARS-CoV-2 in nursing homes** as well as the [Jupyter Notebook](https://github.com/JanaLasser/agent_based_COVID_SEIRX/blob/master/nursing_home/screening_frequency_analysis.ipynb) used to create the heatmaps for the different analysed screnarios from the simulation data. Run these notebooks from the terminal using:

```jupyter-notebook nursing_home/screening_frequency_data_creation.ipynb```  
and  
```jupyter-notebook nursing_home/screening_frequency_analysis.ipynb```  


## Acknowledgements
I would like to thank [Peter Klimek](https://www.csh.ac.at/researcher/peter-klimek/) from Complexity Science Hub Vienna and Thomas Wochele-Thoma from [Caritas Austria](https://www.caritas.at/) for the fruitful discussions that led to the development of this project.

## References
Ferretti, Luca, et al. "Quantifying SARS-CoV-2 transmission suggests epidemic control with digital contact tracing." Science 368.6491 (2020). [DOI: 10.1126/science.abb6936](https://doi.org/10.1126/science.abb6936)

Linton, N. M., Kobayashi, T., Yang, Y., Hayashi, K., Akhmetzhanov, A. R., Jung, S. M., ... & Nishiura, H. (2020). Incubation period and other epidemiological characteristics of 2019 novel coronavirus infections with right truncation: a statistical analysis of publicly available case data. Journal of clinical medicine, 9(2), 538. [DOI: 10.3390/jcm9020538](https://doi.org/10.3390/jcm9020538)  

Lauer, S. A., Grantz, K. H., Bi, Q., Jones, F. K., Zheng, Q., Meredith, H. R., ... & Lessler, J. (2020). The incubation period of coronavirus disease 2019 (COVID-19) from publicly reported confirmed cases: estimation and application. Annals of internal medicine, 172(9), 577-582. [DOI: 10.7326/M20-0504](https://doi.org/10.7326/M20-0504)  

Walsh, K. A., Jordan, K., Clyne, B., Rohde, D., Drummond, L., Byrne, P., ... & O'Neill, M. (2020). SARS-CoV-2 detection, viral load and infectivity over the course of an infection: SARS-CoV-2 detection, viral load and infectivity. Journal of Infection. [DOI: 10.1016/j.jinf.2020.06.067](10.1016/j.jinf.2020.06.067)  

You, C., Deng, Y., Hu, W., Sun, J., Lin, Q., Zhou, F., ... & Zhou, X. H. (2020). Estimation of the time-varying reproduction number of COVID-19 outbreak in China. International Journal of Hygiene and Environmental Health, 113555. [DOI: 10.1016/j.ijheh.2020.113555](https://doi.org/10.1016/j.ijheh.2020.113555)

Backer Jantien A, Klinkenberg Don, Wallinga Jacco. Incubation period of 2019 novel coronavirus (2019-nCoV) infections among travellers from Wuhan, China, 20–28 January 2020. Euro Surveill. 2020;25(5):pii=2000062. [DOI: 10.2807/1560-7917.ES.2020.25.5.2000062](https://doi.org/10.2807/1560-7917.ES.2020.25.5.2000062)

He, X., Lau, E. H., Wu, P., Deng, X., Wang, J., Hao, X., ... & Mo, X. (2020). Temporal dynamics in viral shedding and transmissibility of COVID-19. Nature medicine, 26(5), 672-675. [DOI: 10.1038/s41591-020-0869-5](https://doi.org/10.1038/s41591-020-0869-5)  

Nikolai, L. A., Meyer, C. G., Kremsner, P. G., & Velavan, T. P. (2020). Asymptomatic SARS Coronavirus 2 infection: Invisible yet invincible. International Journal of Infectious Diseases. [DOI: 10.1016/j.ijid.2020.08.076](https://doi.org/10.1016/j.ijid.2020.08.076)  

McMichael, T. M., Currie, D. W., Clark, S., Pogosjans, S., Kay, M., Schwartz, N. G., ... & Ferro, J. (2020). Epidemiology of Covid-19 in a long-term care facility in King County, Washington. New England Journal of Medicine, 382(21), 2005-2011. [DOI: 10.1056/NEJMoa2005412](https://doi.org/10.1056/NEJMoa2005412)  

Li, Q., Guan, X., Wu, P., Wang, X., Zhou, L., Tong, Y., ... & Xing, X. (2020). Early transmission dynamics in Wuhan, China, of novel coronavirus–infected pneumonia. New England Journal of Medicine. [DOI: 10.1056/NEJMoa2001316](https://doi.org/10.1056/NEJMoa2001316)  

Wu, J. T., Leung, K., & Leung, G. M. (2020). Nowcasting and forecasting the potential domestic and international spread of the 2019-nCoV outbreak originating in Wuhan, China: a modelling study. The Lancet, 395(10225), 689-697. [DOI: 10.1016/S0140-6736(20)30260-9](https://doi.org/10.1016/S0140-6736(20)30260-9)  

Pan, J., Harb, C., Leng, W., & Marr, L. C. (2020). Inward and outward effectiveness of cloth masks, a surgical mask, and a face shield. medRxiv. [DOI: 10.1101/2020.11.18.20233353](https://doi.org/10.1101/2020.11.18.20233353)

Sharif-Askari, N. S., Sharif-Askari, F. S., Alabed, M., Temsah, M. H., Al Heialy, S., Hamid, Q., & Halwani, R. (2020). Airways Expression of SARS-CoV-2 Receptor, ACE2, and TMPRSS2 Is Lower in Children Than Adults and Increases with Smoking and COPD. Mol Ther Methods Clin Dev, 18, 1-6. [DOI: 10.1016%2Fj.omtm.2020.05.013](https://dx.doi.org/10.1016%2Fj.omtm.2020.05.013)
