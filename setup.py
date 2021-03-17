from setuptools import find_packages, setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name='scseirx',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    version='1.2.0',
    description='A simulation tool to explore the spread of COVID-19 in small communities such as nursing homes or schools via agent-based modeling (ABM) and the impact of prevention measures. The model follows an SEIRX approach, building on the agent based simulation framework mesa in which agents can be susceptible (S), exposed (E), infected (I), removed (R) or quarantined (X) and is based on explicitly defined and dynamic contact networks between agents. The model offers the possibility to explore the effectiveness of various testing, tracing and quarantine strategies and other interventions such as ventilation and mask-wearing.',
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/JanaLasser/agent_based_COVID_SEIRX",
    author='Jana Lasser',
    author_email='lasser@csh.ac.at',
    license='MIT',
    classifiers=[
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8"],
    install_requires=[
        'numpy>=1.19.2',
        'scipy>=1.6.1',
        'matplotlib==3.3.4',
        'networkx>=2.5',
        'mesa>=0.8.8.1',
        'pandas>=1.2.3'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==6.2.2'],
    test_suite='tests',
    include_package_data=True
)
