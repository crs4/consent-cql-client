import base64
import json
import secrets
import uuid
import requests
import pprint

from datetime import datetime
from cql.models import Library, Population, Measure, EvaluationMeasure
from aiohttp import web
from enum import Enum

import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")


class Granularity(Enum):
    RESOURCES = "RESOURCES"
    COUNT = "COUNT"


FHIR_CODE_SYSTEMS = {
    "FastingStatus": "http://terminology.hl7.org/CodeSystem/v2-0916",
    "SampleMaterialType": "https://fhir.bbmri.de/CodeSystem/SampleMaterialType",
    "icd10": "http://hl7.org/fhir/sid/icd-10",
    "icd10gm": "http://fhir.de/CodeSystem/dimdi/icd-10-gm",
    "loinc": "http://loinc.org",
    "ordo": "http://www.orpha.net/ORDO/",
    "uberon": "http://purl.obolibrary.org/obo/uberon.owl",
    "StorageTemperature": "https://fhir.bbmri.de/CodeSystem/StorageTemperature",
}


FHIR_BASE_URL = "http://localhost:8089/fhir"
FHIR_SPECIMEN_RESOURCE_URL = f"{FHIR_BASE_URL}/Specimen"
FHIR_PATIENT_RESOURCE_URL = f"{FHIR_BASE_URL}/Patient"
FHIR_ORGANIZATION_RESOURCE_URL = f"{FHIR_BASE_URL}/Organization"
FHIR_REQUEST_HEADER = {"Content-type": "application/fhir+json"}
MAX_RESULTS = 11000
FHIR_LIBRARY_VERSION = "0.1.1"
FHIR_MEASURE_YEAR_VERSION = "0.1.1"
FHIR_MEASURE_EVALUATION_YEAR_START = "1900"
FHIR_MEASURE_EVALUATION_YEAR_END = "2100"
CQL_QUERY_CONTEXT = "Specimen"  # This can be Specimen or  Patient
CQL_QUERY_GRANULARITY = Granularity.COUNT  # it can be count or resources
CCEs = ["RETURN_OF_RESULTS"]  # Common Condition Elements codes


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


def create_cql_patients_query(context: str, CCEs: list):
    return (
        "library Retrieve\n"
        + "using FHIR version '4.0.0'\n"
        + "include FHIRHelpers version '4.0.0'\n\n"
        + "\n".join(
            [
                f"codesystem {key}: '{value}'"
                for (key, value) in FHIR_CODE_SYSTEMS.items()
            ]
        )
        + "\n\ncontext Patient"
        + "\n\ndefine Patient:\n singleton from ([Patient])"
        + "\n\ndefine InInitialPopulation:\n"
        + "  {constraints}\n"
        + "define Gender:\n"
        + "  Patient.gender \n"
        + "define AgeClass:\n"
        + "  (AgeInYears() div 10) * 10"
    )


def create_cql_specimens_query():
    return (
        "library Retrieve\n"
        + "using FHIR version '4.0.0'\n"
        + "include FHIRHelpers version '4.0.0'\n\n"
        + "\n".join(
            [
                f"codesystem {key}: '{value}'"
                for (key, value) in FHIR_CODE_SYSTEMS.items()
            ]
        )
        + "\n\ncontext Specimen"
        + "\n\ndefine Patient:\n singleton from ([Patient])"
        + "\n\ndefine InInitialPopulation:\n"
        + """
                      (exists(from Specimen.extension E where E.url = 'https://fhir.bbmri.de/StructureDefinition/SampleDiagnosis' and
                      (icd10.id in E.value.coding.system and 'G20' in E.value.coding.code))) and 
                      (exists from [Patient] P where (P.gender = 'male')) and 
                      (exists(from [Specimen] S where S.type.coding contains Code 'blood-serum' from SampleMaterialType))
                      """
    )


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
        subject=CQL_QUERY_CONTEXT,
        library_url=url,
        id=generate_id(),
    )


def create_evaluation_measure(report_type):
    return EvaluationMeasure(
        period_start=FHIR_MEASURE_EVALUATION_YEAR_START,
        period_end=FHIR_MEASURE_EVALUATION_YEAR_END,
        report_type=report_type,
    )


def perform_cql_query(cql_query: str, granularity: Granularity):
    logging.debug(cql_query)
    base64_cql = encode(cql_query)
    logging.debug("Creating Library")
    library_url = generate_uuid()
    library = create_library(base64_cql, library_url)
    logging.debug("POST Library")
    l = perform_fhir_api_request("POST", f"{FHIR_BASE_URL}/Library", library)
    logging.debug("Library created")
    populations = [
        Population(expression="InInitialPopulation", code="initial-population")
    ]
    measure = create_measure(populations, library_url)
    logging.debug("Creating Measure")
    logging.debug(measure.get_resource())
    created_measure = perform_fhir_api_request(
        "POST", f"{FHIR_BASE_URL}/Measure", measure
    )
    logging.debug("Measure created")
    measure_id = created_measure["id"]
    report_type = EvaluationMeasure.SUBJECT_LIST
    evaluation_measure = create_evaluation_measure(report_type)
    logging.debug("Evaluating Measure")
    logging.debug(evaluation_measure.get_resource())
    evaluation_measure_results = perform_fhir_api_request(
        "POST",
        f"{FHIR_BASE_URL}/Measure/{measure_id}/$evaluate-measure",
        json=evaluation_measure,
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
        "GET", f"{FHIR_BASE_URL}/{CQL_QUERY_CONTEXT}", params=params
    )
    logging.debug(fhir_entries)
    return fhir_entries


def main():
    query = create_cql_specimens_query()
    qry_result = perform_cql_query(query, CQL_QUERY_GRANULARITY)
    num = (
        qry_result
        if CQL_QUERY_GRANULARITY == Granularity.COUNT
        else len(qry_result["entry"])
    )
    logging.info(
        f"Found {num} {CQL_QUERY_CONTEXT}(s) according to the correspondent parameters."
    )
    if CQL_QUERY_GRANULARITY == Granularity.RESOURCES:
        logging.info("RESOURCES:")
        logging.info(json.dumps(qry_result, indent=2, sort_keys=True))
    else:
        logging.info("No resources to show, as the granularity is COUNT")


if __name__ == "__main__":
    main()
