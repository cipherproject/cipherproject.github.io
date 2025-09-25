# The CIPHER Platform

**Cyberattack Impacts, Patient Harms & Emergency Response (CIPHER)** is an interactive platform for modelling clinical risks from healthcare cyberattacks.

Check out the demo version of the platform here: [https://cipherproject.github.io/](https://cipherproject.github.io/)

## About
The <b>CIPHER project</b> was built to safeguard patient care during healthcare cyberattacks, by improving the way we model <b>C</b>yberattack <b>I</b>mpacts, <b>P</b>atient <b>H</b>arms and <b>E</b>mergency <b>R</b>esponse (CIPHER). 

On this page you'll find the key databases and resources that underpin the project, and the skeleton code for creating cyber-risk quantification models from these datasets. The project was created as part of the <a href="https://cyberhealth.ucsd.edu/research/current-projects/index.html">H3RP Programme</a> at UC San Diego</b> and is available for academics globally to download our curated datasets and resources to create models that are tailored to their local hospital context. We welcome healthcare practitoners to examine the safety incidents likely to occur during IT downtime in their hospital, and encourage specialists to look at the risks specific to their populations which can be done by filtering the datasets by clinical domain. 

The full models with advanced functionality (filters, maps, NLP search) is available here: www.thecipherplatform.com

## Quick Start

No need to install anything - just open the demo site above.

Alternatively, if you want to run the demo locally:

''' bash
1. git clone https://github.com/cipherproject/thecipherplatform.github.io
2. cd thecipherplatform.github.io
3. python -m http.server.8080
4. open http://localhost.8080 in your browser

## Repo Layout
1. data / Version 1 of csv Dataset
2. build/ Python builder script
3. index.html Static landing page served by Github Pages
4. README.md Project documentation

## Data
<b>data/v1_cipher_data.csv</b> is the version 1 release of the CIPHER dataset, which contains the combined academic and online data collected as part of our research project investigating patient-level harms from healthcare cyberattacks. Full details of the methodology for obtaining the dataset are provided in the associated published academic papers.

## Authors
Dr Isabel Straw

Developed as part of the HR3P Programme at UC San Diego

## License
Licensed under Apache 2.0 License
You are free to use, modify and distribute the project with attribution

