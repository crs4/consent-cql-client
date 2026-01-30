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
    Sex,
)

import random
import pandas as pd
from datetime import datetime

from bbmri_fp_etl.serializer import JsonFile
from bbmri_fp_etl.sources import AbstractSource

from test.valuesets import DISEASES, SAMPLE_TYPES


class ExampleSource(AbstractSource):
    def get_biobanks_data(self):
        organizations = []
        biobank = Biobank(
            id="test-bb-1",
            acronym="test-bb-1",
            name="Test Biobank",
            description="Test Biobank",
            url=["http://test-bb-1.com"],
            country=Country("IT"),
            contact=[
                Contact(
                    telecom=[
                        Telecom(value="conctact@contact.it", type=TelecomType.EMAIL)
                    ],
                    role=ContactRole(type=RoleType.RESEARCHER),
                )
            ],
            jurystic_person="Test Person",
        )
        organizations.append(biobank)
        collection = Collection(
            id="test-biobank-1-collection-1",
            acronym="test-biobank-1-collection-1",
            name="Test Collection 1",
            description="Test Collection 1",
            url=["http://test-bb-1.com"],
            country=Country("IT"),
            contact=[
                Contact(
                    telecom=[
                        Telecom(value="conctact@contact.it", type=TelecomType.EMAIL)
                    ],
                    role=ContactRole(type=RoleType.RESEARCHER),
                )
            ],
            age_low=0,
            age_high=99,
            data_category=[DataCategory(DataCategory.OTHER)],
            material_type=[
                CollectionSampleType.WHOLE_BLOOD,
                CollectionSampleType.URINE,
                CollectionSampleType.PLASMA,
                CollectionSampleType.TISSUE_FROZEN,
                CollectionSampleType.DNA,
                CollectionSampleType.SERUM,
                CollectionSampleType.SALIVA,
                CollectionSampleType.OTHER,  # Pathogenic sample type not mapped in our model, using OTHE
                CollectionSampleType.WHOLE_BLOOD,
                CollectionSampleType.URINE,
                CollectionSampleType.PLASMA,
                CollectionSampleType.RNA,
                CollectionSampleType.DNA,
                CollectionSampleType.TISSUE_FROZEN,
                CollectionSampleType.FECES,
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
        return [disease]

    def _get_random_birth_date(self, start_year, end_year):
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
        donor = Donor(
            id=f"{donor_id}",
            gender=random.choice([Sex.MALE, Sex.FEMALE]),
            birth_date=self._get_random_birth_date(1925, 2010),
        )
        samples = []
        for i in range(1, random.choice([2, 3, 4, 5, 6])):
            sample_id = f"Sample_{donor_id}_{i}"
            sampling_event = SamplingEvent(
                id=f"SE-{sample_id}",
                date_at_event=self._get_random_birth_date(2011, 2020),
            )
            sample = Sample(
                id=sample_id,
                type=random.choice(SAMPLE_TYPES),
                events=[sampling_event],
                content_diagnosis=self._generate_random_sample_disease(),
                collection=Collection(id="test-biobank-1collection-1"),
            )
            samples.append(sample)
        return Case(donor=donor, samples=samples)

    def get_cases_data(self) -> Iterable[Case]:
        cases = []
        for i in range(0, 100000):
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
