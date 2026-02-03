import base64
import json
import secrets
import uuid
import requests
from datetime import datetime

from datetime import datetime
from cql.models import Library, Population, Measure, EvaluationMeasure
from aiohttp import web
from enum import Enum


import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")


class Granularity(Enum):
    RESOURCES = "RESOURCES"
    COUNT = "COUNT"


FHIR_BASE_URL = "http://localhost:8089/fhir"
FHIR_SPECIMEN_RESOURCE_URL = f"{FHIR_BASE_URL}/Specimen"
FHIR_PATIENT_RESOURCE_URL = f"{FHIR_BASE_URL}/Patient"
FHIR_ORGANIZATION_RESOURCE_URL = f"{FHIR_BASE_URL}/Organization"
FHIR_REQUEST_HEADER = {"Content-type": "application/fhir+json"}
MAX_RESULTS = 11000
FHIR_LIBRARY_VERSION = "0.1.2"
FHIR_LIBRARY_WITH_CONSENT_URL = "http://bbmri.it/fhir/Library/CountSpecimensWithConsentLibraryNew1"
FHIR_MEASURE_WITH_CONSENT_URL = "http://bbmri.it/fhir/Library/CountSpecimensWithConsentMeasure"
FHIR_MEASURE_YEAR_VERSION = "0.1.1"
FHIR_MEASURE_EVALUATION_YEAR_START = "1900"
FHIR_MEASURE_EVALUATION_YEAR_END = "2100"
CQL_QUERY_GRANULARITY = Granularity.COUNT  # it can be count or resources
CCEs = ["CONTACT_TO_PARTICIPATE"]  # Common Condition Elements codes

def encode(string):
    return base64.b64encode(string.encode("ascii"))


def generate_uuid():
    return "urn:uuid:{uuid}".format(uuid=uuid.uuid1())


def generate_creation_timestamp():
    return f"{datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f%z')[:-3]}Z"


def generate_id():
    return secrets.token_hex(8)


def perform_fhir_api_request(method, url, json=None, params=None):
    try:
        res = requests.request(
            method,
            url,
            json=json.get_resource() if json is not None else None,
            params=params if params is not None else None,
            headers=FHIR_REQUEST_HEADER,
        )
    except requests.exceptions.ConnectionError:
        raise web.HTTPInternalServerError(reason="Error contacting data service")

    logging.debug("Performing request to %s" % url)
    if res.status_code not in (200, 201):
        logging.debug(
            "Error performing the request. Returned code %s" % res.status_code
        )
        raise Exception(res.json())
    return res.json()

def create_cql_query(include_consent):

    query_header = f"""
    library ConsentSpecimenQuery version '1.0.0'
    using FHIR version '4.0.0'
    include FHIRHelpers version '4.0.0'
    codesystem SampleMaterialType:  'https://fhir.bbmri.de/CodeSystem/SampleMaterialType'
    codesystem icd10: 'http://hl7.org/fhir/sid/icd-10'
    
    parameter "CCEChoice" String
    parameter "CCECode" String
    parameter "DiagnosisCode" String
    parameter "SampleType" String
    parameter "PatientGender" String
    
    define Patient:\n singleton from ([Patient])
    
    context {'Unfiltered' if include_consent else 'Specimen'}
    
    """

    search_consents_function = f"""
        define SpecimenIdsReferencedInConsent:
        flatten (
            [Consent] C
            return flatten (
                C.provision.provision Q
                return flatten (
                    Q.data D 
                    where Q.type = "CCEChoice" and 
                    Q.code.coding.code = "CCECode"
                    return Split(D.reference.reference, '/')[1]
                    )
                )
        )
        
    """

    specimens_search_function = f"""
        define FilteredSpecimens:
        (exists(from Specimen.extension E where E.url = 'https://fhir.bbmri.de/StructureDefinition/SampleDiagnosis' and
                      (icd10.id in E.value.coding.system and "DiagnosisCode" in E.value.coding.code))) and 
                      (exists from [Patient] P where (P.gender = "PatientGender")) and 
                      (exists(from [Specimen] S where S.type.coding contains Code 'SampleType' from "SampleMaterialType"))
                      
    """


    query = query_header
    initial_population = "define InInitialPopulation:\n"
    consent_block =  """
    
    exists (
            from [Specimen] S
            where S.id in SpecimenIdsReferencedInConsent )
    """

    if include_consent:
        query += search_consents_function
        query += "context Specimen\n\n"
        query+= specimens_search_function
        query += initial_population
        query+= 'FilteredSpecimens and \n'
        query += consent_block

    else:
        query += specimens_search_function
        query += initial_population
        query += 'FilteredSpecimens'

    return query

def create_library(base64_cql_query, url):
    return Library(
        version_id=FHIR_LIBRARY_VERSION,
        last_updated=generate_creation_timestamp(),
        data=base64_cql_query.decode("ascii"),
        id=generate_id(),
        url=url,
    )


def create_measure(populations, url):
    return Measure(
        stratifiers=[],
        populations=populations,
        version_id=FHIR_MEASURE_YEAR_VERSION,
        last_updated=generate_creation_timestamp(),
        subject='Specimen',
        library_url=url,
        id=generate_id(),
    )


def create_evaluation_measure(report_type,cce_choice,cce_code,diagnosis_code,sample_type, patient_gender):
    return EvaluationMeasure(
        period_start=FHIR_MEASURE_EVALUATION_YEAR_START,
        period_end=FHIR_MEASURE_EVALUATION_YEAR_END,
        report_type=report_type,
        cce_choice=cce_choice,
        cce_code=cce_code,
        diagnosis_code=diagnosis_code,
        sample_type=sample_type,
        patient_gender=patient_gender
    )


def post_library(cql_query, library_url):
    base64_cql = encode(cql_query)
    logging.debug("Creating Library")
    library = create_library(base64_cql, library_url)
    logging.debug("POST Library")
    #if the library with the same url exists, it is not recreated
    library = perform_fhir_api_request("POST", f"{FHIR_BASE_URL}/Library?{library_url}", library)
    return library['id']


def post_measure(library_url, measure_url):
    populations = [
        Population(expression="InInitialPopulation", code="initial-population")
    ]
    measure = create_measure(populations, library_url)
    logging.debug("Creating Measure")
    logging.debug(measure.get_resource())
    #if the measure with the same url exists, it is not recreated
    created_measure = perform_fhir_api_request(
        "POST", f"{FHIR_BASE_URL}/Measure?{measure_url}", measure
    )
    return created_measure['id']


def evaluate_measure(measure_id, granularity, cce_choice, cce_code, diagnosis_code, sample_type, patient_gender):
    report_type = EvaluationMeasure.SUBJECT_LIST
    evaluation_measure = create_evaluation_measure(report_type,cce_choice,cce_code,diagnosis_code,sample_type, patient_gender)
    logging.debug("Evaluating Measure")
    logging.debug(evaluation_measure.get_resource())
    evaluation_measure_results = perform_fhir_api_request(
        "POST",
        f"{FHIR_BASE_URL}/Measure/{measure_id}/$evaluate-measure",
        json=evaluation_measure
    )
    logging.debug("Measure evaluated")
    logging.debug(evaluation_measure_results)

    num = evaluation_measure_results["group"][0]["population"][0]["count"]
    if granularity == Granularity.COUNT:
        return num
    list_id = evaluation_measure_results["group"][0]["population"][0]["subjectResults"][
        "reference"
    ][5:]
    params = {"_list": list_id, "_count": MAX_RESULTS}
    fhir_entries = perform_fhir_api_request(
        "GET", f"{FHIR_BASE_URL}/Specimen", params=params
    )
    logging.debug(fhir_entries)
    return fhir_entries


def main():
    cql_query = create_cql_query(True)
    logging.debug(cql_query)
    #get library
    # Check if library exists
    res = requests.get(f"{FHIR_BASE_URL}/Library", params={"url": FHIR_LIBRARY_WITH_CONSENT_URL})
    if res.json().get("total", 0) > 0:
        library_id = res.json()["entry"][0]["resource"]["id"]
        logging.info(f'Library already present with id {library_id}')
    else:
        # create new library
        library_id = post_library(cql_query, FHIR_LIBRARY_WITH_CONSENT_URL)
        logging.info(f'Created Library with id {library_id}')

    library_id = 'DHBEGDYNCGZKKBOY'
    measure_id = 'DHBEGGZTOTAHCV4I'

    # Check if a measure already exists for the library
    # url = f"{FHIR_BASE_URL}/Measure?url={FHIR_LIBRARY_WITH_CONSENT_URL}"
    # res = requests.get(f"{FHIR_BASE_URL}/Measure?library={FHIR_LIBRARY_WITH_CONSENT_URL}")
    # res_json = res.json()
    # measure_entries = res.json().get("entry", [])
    #
    # if measure_entries:
    #     measure_id = measure_entries[0]["resource"]["id"]
    #     logging.info(f'Measure already present with id {measure_id}')
    #
    # else:
    #     measure_id = post_measure(FHIR_LIBRARY_WITH_CONSENT_URL,FHIR_MEASURE_WITH_CONSENT_URL)
    #     logging.info(f'Created Measure with id {measure_id}')


    start = datetime.now()
    qry_result = evaluate_measure(measure_id,Granularity.COUNT,'CONTACT_TO_PARTICIPATE', 'permit', 'G20','blood-serum', 'male')
    num = (
        qry_result
        if CQL_QUERY_GRANULARITY == Granularity.COUNT
        else len(qry_result["entry"])
    )
    logging.info(
        f"Found {num} Specimen(s) according to the correspondent parameters."
    )
    if CQL_QUERY_GRANULARITY == Granularity.RESOURCES:
        logging.info("RESOURCES:")
        logging.info(json.dumps(qry_result, indent=2, sort_keys=True))
    else:
        logging.info("No resources to show, as the granularity is COUNT")
    end = datetime.now()
    logging.info(f'Overall execution time: {(end - start).seconds} seconds')


if __name__ == "__main__":
    main()
