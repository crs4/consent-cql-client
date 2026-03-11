from bbmri_fp_etl.models import SampleType

SAMPLE_TYPES = [
    SampleType.WHOLE_BLOOD,
    SampleType.PLASMA,
    SampleType.TISSUE_FROZEN,
    SampleType.SERUM,
    SampleType.TISSUE_FROZEN_OR_FFPE,
    SampleType.TISSUE_FFPE
]




DISEASES = [
    "C10",  # Malignant neoplasm of oropharynx
    "C14",  # Malignant neoplasm of other and ill-defined sites in the lip, oral cavity and pharynx
    "C16",  # Malignant neoplasm of stomach
    "C16",  # Malignant neoplasm of colon
    "C20",  # Malignant neoplasm of rectum
    "C71",  # Malignant neoplasm of brain
    "C32",  # Malignant neoplasm of larynx
]

CCEs = items = [
    "LEGAL_FRAMEWORK",
    "COMMERCIAL_ENTITY",
    "RETURN_TO_PROVIDER",
    "PARTICIPANT_RECONTACT",
    "IMMORT_CELL_LINES",
    "INDUC_PLURIP_STEM_CELLS",
    "ORGANOIDS",
    "DATA_LINKAGE",
    "POSTMORTEM",
    "NUCLEID_ACID_SEQUENCE",
    "ARTIFICIAL_INTELLIGENCE"
]
