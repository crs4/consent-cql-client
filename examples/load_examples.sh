#!/bin/bash
FHIR_ENDPOINT="http://localhost:8089/fhir"
#FHIR_ENDPOINT="http://10.140.141.123:8080/fhir"

blazectl --server $FHIR_ENDPOINT upload ./biobanks
blazectl --server $FHIR_ENDPOINT upload ./collections
blazectl --server $FHIR_ENDPOINT upload ./patients-specimens-conditions
blazectl --server $FHIR_ENDPOINT upload ./consents

