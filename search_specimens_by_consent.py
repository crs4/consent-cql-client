import base64
import secrets
import uuid
from datetime import datetime

import requests

from cql.models import Library, Population, Measure, EvaluationMeasure

from aiohttp import web

fhir_base_url = "http://localhost:8089/fhir"
fhir_specimen_url = f"{fhir_base_url}/Specimen"
fhir_patient_url = f"{fhir_base_url}/Patient"
fhir_organization_url = f"{fhir_base_url}/Organization"
fhir_json_header = {"Content-type": "application/fhir+json"}
max_items = 11000
library_version = "0.1.1"
measure_version = "0.1.1"
evaluation_year_start = "1900"
evaluation_year_end = "2100"


def encode(string):
    return base64.b64encode(string.encode("ascii"))


def generate_uuid():
    return "urn:uuid:{uuid}".format(uuid=uuid.uuid1())


def generate_creation_timestamp():
    return f"{datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f%z')[:-3]}Z"


def generate_id():
    return secrets.token_hex(8)


def _perform_request(method, url, json=None, params=None):
    try:
        res = requests.request(
            method,
            url,
            json=json.get_resource() if json is not None else None,
            params=params if params is not None else None,
            headers=fhir_json_header,
        )
    except requests.exceptions.ConnectionError:
        raise web.HTTPInternalServerError(reason="Error contacting data service")

    print("Performing request to %s" % url)
    if res.status_code not in (200, 201):
        print("Error performing the request. Returned code %s" % res.status_code)
        raise Exception(res.json())
    return res.json()


# specimens_query_by_consent = "library Retrieve\n" + \
#                       "using FHIR version '4.0.0'\n" + \
#                       "include FHIRHelpers version '4.0.0'\n\n" + \
#                       "\n".join([f"codesystem {key}: '{value}'" for (key, value) in FHIR_CODE_SYSTEMS.items()]) + \
#                       "\n\ncontext Specimen" + \
#                       "\n\ndefine Patient:\n singleton from ([Patient])" + \
#                       "\n\ndefine InInitialPopulation:\n" + \
#                       "exists(from [Specimen] S where exists (from S.extension E where E.value.identifier.value = '{self.collection_id}')"
# "exists(from [Patient] P where P.gender = 'female') "
#                       "exists(from [Consent] C where exists(flatten(C.provision.provision) P where exists(P.data D where D.reference.reference = 'Specimen/' + S.id))) "

# "exists(from [Specimen] S where S.type.coding contains Code 'blood-serum' from SampleMaterialType)"


# specimens_query_by_consent = """
# library ConsentQuery version '1.0.0'
#
# using FHIR version '4.0.1'
#
# context Patient
#
# define InInitialPopulation:
#   exists([Consent])
# """

specimens_query_by_consent = """
library ConsentSpecimenQuery version '1.0.0'

using FHIR version '4.0.0'

include FHIRHelpers version '4.0.0'

context Unfiltered




// Find all Consent resources where provision.provision.data references a Specimen and matches a specific provision.code
define ConsentWithSpecimenReferences:
  [Consent] C
    where exists (
      C.provision P
        where exists (
          P.provision Q
            where Q.code.coding.system = 'https://fhir.bbmri.de/CodeSystem/common-condition-elements-cs'
            and Q.code.coding.code = 'BIOBANKING'
            and exists (
              Q.data D
            )
    )
    )

// Extract the Specimen IDs referenced in the provisions of the Consent resources
  define SpecimenIdsReferencedInConsent:
  flatten(
    [Consent] C
          return flatten (
            C.provision.provision Q
              return flatten (
                Q.data D
                where Q.code.coding.system = 'https://fhir.bbmri.de/CodeSystem/common-condition-elements-cs'
                and Q.code.coding.code = 'COMMERCIAL_USE'
                  return Split(D.reference.reference, '/')[1]
              )
        
      )
      )
   
define testSpecimens:
     List<String>{'urn-test-spec-AABJdynbLg'}


// Now switch to the Specimen context and retrieve those Specimens
context Specimen

define InInitialPopulation:
  exists (from [Specimen] S
    where S.id in SpecimenIdsReferencedInConsent)

"""


base64_cql = encode(specimens_query_by_consent)
library_url = generate_uuid()
print("Creating Library")
print(specimens_query_by_consent)
library = Library(
    version_id=library_version,
    last_updated=generate_creation_timestamp(),
    data=base64_cql.decode("ascii"),
    id=generate_id(),
    url=library_url,
)
l = _perform_request("POST", f"{fhir_base_url}/Library", library)
print("Library created")
populations = [Population(expression="InInitialPopulation", code="initial-population")]
measure = Measure(
    stratifiers=[],
    populations=populations,
    version_id=measure_version,
    last_updated=generate_creation_timestamp(),
    subject="Specimen",
    library_url=library_url,
    id=generate_id(),
)

print("Creating Measure")
print(measure.get_resource())
created_measure = _perform_request("POST", f"{fhir_base_url}/Measure", measure)
print("Measure created")
measure_id = created_measure["id"]
report_type = EvaluationMeasure.SUBJECT_LIST
evaluation_measure = EvaluationMeasure(
    period_start=evaluation_year_start,
    period_end=evaluation_year_end,
    report_type=report_type,
)
print("Evaluating Measure")
print(evaluation_measure.get_resource())
evaluation_measure_results = _perform_request(
    "POST",
    f"{fhir_base_url}/Measure/{measure_id}/$evaluate-measure",
    json=evaluation_measure,
)
print("Measure evaluated")
print(evaluation_measure_results)

num = evaluation_measure_results["group"][0]["population"][0]["count"]
list_id = evaluation_measure_results["group"][0]["population"][0]["subjectResults"][
    "reference"
][5:]
# get results from the measures list; at the moment it gets overall results
params = {"_list": list_id, "_count": max_items}
fhir_entries = _perform_request("GET", f"{fhir_base_url}/Specimen", params=params)
print(fhir_entries)
