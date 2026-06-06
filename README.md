#  Infectious Disease Spread Simulator

An Agent-Based Simulation for Infectious Disease Spread, built on the research paper: **"An Infectious Disease Spread Simulation Based on Large Language Model Decision Making"**.

##  Live Deployments

- **Interactive Streamlit Dashboard:** [View Simulation Results](https://infectious-disease-spread-simulator-7wcalmebfennsr5mrxmlaf.streamlit.app/)
- **Project Frontend:** [View Project Page](https://gyan1201.github.io/Infectious-Disease-Spread-Simulator/)
- **Build Tutorial:** [View Tutorial](https://gyan1201.github.io/Infectious-Disease-Spread-Simulator/tutorial-webpage/)

##  About the Project

This project simulates the spread of infectious diseases using Large Language Models (LLMs) to model human decision-making behavior. It combines a robust **Java/MASON** simulation backend with a modern **Python/Streamlit** visualization dashboard.

### Features
- Agent-Based Modeling using the MASON framework.
- SEIR disease models enhanced by LLM-driven agent interactions.
- Dynamic choropleth mapping for localized simulation tracking (e.g., Atlanta, San Francisco).

##  Local Development

### 1. Java Backend Simulator
To run the underlying simulation, you need Java 17 and Maven:
```bash
cd disease-simulator-LLM_agent
mvn clean compile assembly:single
java -Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory \
     -Dlog.rootDirectory=logs \
     -Dfile.prefix=gui-run \
     -Dsimulation.test=bias \
     -jar target/vanilla-0.1-jar-with-dependencies.jar \
     -configuration examples/atlanta.properties \
     -bias.config examples/bias.llm.properties \
     -bias.single.config examples/bias.single.properties \
     -until 25920
```

### 2. Streamlit Dashboard
The Streamlit app visualizes the simulation logs. You can run it locally with Python:
```bash
cd disease-simulator-LLM_agent
pip install -r ../requirements.txt
streamlit run gui/app.py
```
