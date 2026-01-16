# Demonstrator for the BBMRI.it Pilot project

This project is a demonstrator of the usage of the profiled FHIR BBMRI.it consent 
resource. It provides a series of sample resources, including Consent, that can 
be loaded into a FHIR server and then queried via CQL. 

## Provided resources 
The following examples of resources are provided in the `examples/` folder:

 - Person 
 - Organization (for Biobanks and Collections)
 - Condition
 - Specimen
 - Consent 

## Requirements
 - Install and run the [Samply FHIR server](https://github.com/samply/blaze) 
   (via docker compose)
 - Install the [blazectl command line tool](https://github.com/samply/blazectl) and 
   set the related blazectl command in the path 
 - Python 3.x
 - Python packages: requests

## Installation and run 

First, load the fhir resources, launcing the .sh script; 
```bash
./load_examples.sh
```
Then, run the cql query, launching the python script:
```bash
python3 run_cql_query.py
```

You can modufy the variables in the script:
 - CCEs: can be edited by adding or removing one or more conditions of use 
 - CQL_QUERY_CONTEXT: if set to Patient, then the query provides the count or the 
   detail of the Patients whose samples satisfy the CCEs; if set to Specimen, then the 
   query provides the count or the detail of the Specimens that satisfy the CCEs.
 - CQL_QUERY_GRANULARITY: can be set to RESOURCE or COUNT, depending on whether you want 
   the detail of the resources or just their count.

## Acknowledgments
This work has been partially funded by the following sources: 

 - the “Total Patient Management” (ToPMa) project (grant by the Sardinian Regional Authority, grant number RC_CRP_077). Intervento finanziato con risorse FSC 2014-2020 - Patto per lo Sviluppo della Regione Sardegna;
 - the “Processing, Analysis, Exploration, and Sharing of Big and/or Complex Data” (XDATA) project (grant by the Sardinian Regional Authority).

