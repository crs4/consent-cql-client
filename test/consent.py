import uuid
import json
def create_specimens_provision(provision_type, specimen_ids, cce_code, timestamp):
  specimen_reference_block = [
    {
      "reference": {
        "reference": f'Specimen/{s}',
        "display": f'Specimen/{s}',
      },
      "meaning": "instance"
    }
    for s in specimen_ids
  ]
  return {
              "type": f'{provision_type}',
              "data": specimen_reference_block,
              "code": [
                {
                  "coding": [
                    {
                      "system": "https://fhir.bbmri.de/CodeSystem/common-condition-elements-cs",
                      "code": f'{cce_code}'
                    }
                  ]
                }
              ],
              "period": {
                "start": f'{timestamp}'
              }
            }


def create_consent_resource(consent_id, patient_id, collection_id, main_provision_timestamp,specimen_provisions):
    consent_template = {
      "entry": [
        {
          "fullUrl": f'{uuid.uuid4()}',
          "request": {
            "method": "PUT",
            "url": f'Consent/consent-urn-test-part-{consent_id}'
          },
          "resource": {
            "id": f'consent-urn-test-part-{consent_id}',
            "resourceType": "Consent",
            "identifier": [{"value": f'Consent/consent-urn-test-part-{consent_id}'}],
            "meta": {
              "profile": [
                "https://fhir.bbmri.de/StructureDefinition/Consent"
              ]
            },
            "status": "active",
            "scope": {
              "coding": [
                {
                  "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                  "code": "research",
                  "display": "Research"
                }
              ]
            },
            "category": [
              {
                "coding": [
                  {
                    "system": "https://loinc.org/",
                    "code": "59284-0",
                    "display": "Patient consent"
                  }
                ]
              }
            ],
            "patient": {
              "reference": f'Patient/{patient_id}'
            },
            "organization":[ {
              "reference": f'Organization/{collection_id}'
            }],
            "dateTime": "2025-04-24T00:00:00Z",
            "policyRule": {
              "coding": [
                {
                  "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                  "code": "_ActConsentDirective"
                }
              ]
            },
            "provision": {
              "class": [
                {
                  "system": "http://hl7.org/fhir/resource-types",
                  "code": "Specimen",
                  "display": "Specimen"
                }
              ],          "period": {
                "start": f'{main_provision_timestamp}',
              },
              "provision": [p for p in specimen_provisions]
            }
          }
        }
      ],
      "type": "transaction",
      "resourceType": "Bundle"
    }
    f = open(f'./fhir_consents_output/consent_patient_{patient_id}.json', 'w')
    json.dump(consent_template, f, indent=2)


def main():
  p = create_specimens_provision('permit', ['Sample-0-1', 'Sample-0-2'], "RETURN_OF_RESULTS", "2025-04-24T00:00:00Z")
  create_consent_resource('consent-0', '0', 'test-biobank-1-collection-1', "2025-04-24T00:00:00Z", [p])


if __name__ == "__main__":
  main()