# The CIPHER Platform

**Cyberattack Impacts, Patient Harms & Emergency Response (CIPHER)** is an interactive platform for modelling clinical risks from healthcare cyberattacks.

Check out the demo here: [https://thecipherplatform.github.io/](https://thecipherplatform.github.io/)

## About
The <b>CIPHER project</b> was built to safeguard patient care during healthcare cyberattacks, by improving the way we model <b>C</b>yberattack <b>I</b>mpacts, <b>P</b>atient <b>H</b>arms and <b>E</b>mergency <b>R</b>esponse (CIPHER). On this page you'll find the key databases and resources that underpin the project, and the skeleton code for creating cyber-risk quantification models from these datasets. The project was created as part of the <a href="https://cyberhealth.ucsd.edu/research/current-projects/index.html">H3RP Programme</a> at UC San Diego</b> and published open-source under the CCB license so that academics globally can download these datasets and resources to create models that are tailored to their local hospital context and patient population. We welcome healthcare practitoners to examine the safety incidents likely to occur during IT downtime in their hospital, and encourage specialists to look at the risks specific to their populations which can be done by filtering the datasets by clinical domain. 

[More details]

The full codebase with advanced functinality (filters, maps, clinical impact modelling) is available here: www.thecipherplatform.com

## Quick Start

You don't need to install anything - just open the site above.

Alternatively, if you want to run the demo locally:

''' bash
1. git clone https://github.com/thecipherplatform/thecipherplatform.github.io
2. cd thecipherplatform.github.io
3. python -m http.server.8080
4. open http://localhost.8080 in your browser

## Repo Layout
data / Version 1 of csv Dataset
build/ Python builder script
index.html Static landing page served by Github Pages
README.md Project documentation

## Data
data/v1_cipher_data.csv is the version 1 release of the CIPHER dataset, which contains the combined academic and online data collected as part of our research project investigating patient-level harms from healthcare cyberattacks. Full details of the methodology for obtaining the dataset are provided in the associated published academic papers.

## Authors
Dr Isabel Straw - Project Lead
Developed as part of the HR3P Programme at UC San Diego

## License
Licensed under Apache 2.0 License
You are free to use, modify and distribute the project with attribution

