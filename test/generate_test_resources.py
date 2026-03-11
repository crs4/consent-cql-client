"""
Script to generate a bunch of FHIR resources to populate a FHIR store, for testing purposes
"""

from typing import Iterable

from bbmri_fp_etl.converter import Converter
from bbmri_fp_etl.destinations.fhir import FHIRDest
from bbmri_fp_etl.models import (
    Biobank,
    Country,
    Contact,
    Telecom,
    TelecomType,
    ContactRole,
    RoleType,
    Collection,
    DataCategory,
    CollectionSampleType,
    CollectionType,
    DiseaseOntologyCode,
    DiseaseOntology,
    Disease,
    Donor,
    SamplingEvent,
    Sample,
    Case,
    Sex, StorageTemperature,
    DiagnosisEvent, EventType, AgeUnit
)

import random
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

from bbmri_fp_etl.serializer import JsonFile
from bbmri_fp_etl.sources import AbstractSource

from test.consent import create_specimens_provision, create_consent_resource
from test.valuesets import DISEASES, SAMPLE_TYPES, CCEs

import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")

class ExampleSource(AbstractSource):
    def __init__(self):
        super().__init__()
        self.specimen_rows = ["donor_id; donor_gender;donor_birth_date;diagnosis_id;diagnosis_age;diagnosis_code;diagnosis_date;"
                      "sample_id;sample_type;sample_collected_date;sample_storage_temperature;cce;cce_choice\n"]
        self.biobank_id = "bbmri-eric:ID:IT_1504858990324590"
        self.collection_id = "bbmri-eric:ID:IT_1504858990324590:collection:1606752281669494"

    def get_biobanks_data(self):
        organizations = []
        biobank = Biobank(
            id="bbmri-eric:ID:IT_1504858990324590",
            acronym="bbmri-eric:ID:IT_1504858990324590",
            name="Biobanca IRE",
            description="Born in 2014 (BBIRE), the Biobank of the IRCCS Regina Elena National Cancer Institute includes tissue and biological fluids of cancer patients. The collections store and distribute frozen tissues, FFPE tissues, blood derivatives, cells and cell lines, biological fluids, nucleic acids and related data.",
            url=["https://www.ifo.it"],
            country=Country("IT"),
            contact=[
                Contact(
                    telecom=[
                        Telecom(value="biobancaire@ifo.it", type=TelecomType.EMAIL)
                    ],
                    role=ContactRole(type=RoleType.RESEARCHER),
                )
            ],
            jurystic_person="Dr. Giovanni Blandino",
        )
        organizations.append(biobank)
        collection = Collection(
            id=self.collection_id,
            acronym="Biobanca Tessuti e Liquidi Biologici IRE",
            name="Biobanca Tessuti e Liquidi Biologici IRE",
            description="BBIRE is a pathology biobank that collects high-quality strategic oncological samples for research and the development of new biomarkers for personalized medicine. It was founded to store and distribute human biological tissues and fluids (such as blood, serum, plasma, PBMCs, etc.) along with their associated data. The aim is to advance basic, clinical, and translational cancer research.",
            url=["https://www.ifo.it"],
            country=Country("IT"),
            contact=[
                Contact(
                    telecom=[
                        Telecom(value="biobancaire@ifo.it", type=TelecomType.EMAIL)
                    ],
                    role=ContactRole(type=RoleType.RESEARCHER),
                )
            ],
            age_low=18,
            age_high=99,
            data_category=[DataCategory(DataCategory.IMAGING_DATA),DataCategory(DataCategory.MEDICAL_RECORDS), DataCategory(DataCategory.BIOLOGICAL_SAMPLES)],
            material_type=[
                CollectionSampleType.TISSUE_FROZEN,
                CollectionSampleType.SERUM,
                CollectionSampleType.PERIPHERAL_BLOOD_CELLS,
                CollectionSampleType.TISSUE_PARAFFIN_EMBEDDED,
                CollectionSampleType.TISSUE_STAINED,
                CollectionSampleType.WHOLE_BLOOD,
                CollectionSampleType.PLASMA,
            ],
            type=[CollectionType.OTHER],
            # disease=c['diagnosis_available'].split(',') if c['diagnosis_available'] else [],
            biobank=biobank,
        )
        organizations.append(collection)
        return organizations

    def _generate_random_sample_disease(self):
        disease_ontology_code = DiseaseOntologyCode(
            code=random.choice(DISEASES), ontology=DiseaseOntology.ICD_10
        )
        disease = Disease(main_code=disease_ontology_code, mapping_codes=[])
        return disease

    def _get_random_date(self, start_year, end_year):
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)

        random_day = random.randint(0, (end - start).days)
        birth_date = (
            pd.to_datetime(start + pd.Timedelta(days=random_day))
            .normalize()  # sets time to 00:00:00
            .to_pydatetime()
        )

        return birth_date



    def _generate_case(self, donor_id):
        donor_birth_date = self._get_random_date(1936, 2008)
        event_date = self._get_random_date(2010, datetime.today().year)
        sampling_event_date = event_date -relativedelta(months=random.randint(1, 12))

        diagnosis_event = DiagnosisEvent(id=f'{donor_id}_event',
                                         date_at_event = event_date,
                                         event_type = EventType.DIAGNOSIS,
                                         disease= self._generate_random_sample_disease(),


        )

        donor = Donor(
            id=f"{donor_id}",
            gender=random.choice([Sex.MALE, Sex.FEMALE]),
            birth_date=donor_birth_date,
            events=[diagnosis_event],
        )
        samples = []
        for i in range(1, random.choice([3, 4, 5, 6])):
            sample_id = f"Sample-{donor_id}-{i}"
            sampling_event = SamplingEvent(
                id=f"SE-{sample_id}",
                date_at_event=sampling_event_date,
            )
            sample = Sample(
                id=sample_id,
                type=random.choice(SAMPLE_TYPES),
                events=[sampling_event],
                content_diagnosis=[self._generate_random_sample_disease()],
                collection=Collection(id="test-biobank-1collection-1"),
                creation_time=sampling_event_date,
                storage_temperature=[StorageTemperature.TEMP_60_TO_85]
            )


            samples.append(sample)
        sample_provisions = []
        for cce in CCEs:
            choice = random.choice(["permit",'deny'])
            sample_consent_provision = create_specimens_provision(
                choice, [s.id for s in samples], cce, "2025-01-24T00:00:00Z"
            )
            sample_provisions.append(sample_consent_provision)

            for s in samples:
                self.specimen_rows.append(
                    f'{donor_id}'
                    + ";"
                    + f'{donor.gender}'
                    + ";"
                    + f'{donor.birth_date}'
                    +";"
                    +f'{diagnosis_event.id}'
                    + ";"
                    +f'{diagnosis_event.age_at_event}'
                    + ";"
                    + f'{diagnosis_event.disease.main_code.code}'
                    + ";"
                    + f'{diagnosis_event.date_at_event}'
                    + ";"
                    + f'{s.id}'
                    + ";"
                    + f'{s.type.name}'
                    + ";"
                    +f'{s.creation_time.isoformat()}'
                    + ";"
                    + f'{s.storage_temperature[0]}'
                    +';'
                    + f'{cce}'
                    + ';'
                    + f'{choice}'
                    + "\n"
                )
        create_consent_resource(
            f"consent-patient-{donor.id}",
            donor.id,
            self.biobank_id,
            "2025-04-24T00:00:00Z",
            sample_provisions,
        )

        return Case(donor=donor, samples=samples)

    def get_cases_data(self) -> Iterable[Case]:
        cases = []
        for i in range(0, 1000):
            logging.debug(f'Generating case:{i}')
            case = self._generate_case(i)
            cases.append(case)
        return cases


if __name__ == "__main__":

    source = ExampleSource()
    fhir_dest_cases = FHIRDest(JsonFile("./fhir_output"))
    fhir_orgs_cases = FHIRDest(JsonFile("./fhir_orgs_output"))
    converter_orgs = Converter(source, fhir_orgs_cases, Converter.ORGANIZATION)
    converter_orgs.run()
    converter_cases = Converter(source, fhir_dest_cases, Converter.CASE)
    converter_cases.run()
    f = open("./input_data/patient_specimens.csv", "w")
    for row in source.specimen_rows:
        f.write(row)
