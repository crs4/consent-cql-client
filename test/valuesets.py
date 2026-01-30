from bbmri_fp_etl.models import SampleType

SAMPLE_TYPES = [
    SampleType.WHOLE_BLOOD,
    SampleType.URINE,
    SampleType.PLASMA,
    SampleType.TISSUE_FROZEN,
    SampleType.DNA,
    SampleType.SERUM,
    SampleType.SALIVA,
    SampleType.OTHER,  # Pathogenic sample type not mapped in our model, using OTHE
    SampleType.WHOLE_BLOOD,
    SampleType.URINE,
    SampleType.PLASMA,
    SampleType.RNA,
    SampleType.DNA,
    SampleType.TISSUE_FROZEN,
    SampleType.FECES,
]


DISEASES = [
    "I10",  # Essential (primary) hypertension
    "I21.9",  # Acute myocardial infarction, unspecified
    "I25.10",  # Atherosclerotic heart disease of native coronary artery
    "I50.9",  # Heart failure, unspecified
    "I48.91",  # Atrial fibrillation, unspecified
    "E11.9",  # Type 2 diabetes mellitus without complications
    "E10.9",  # Type 1 diabetes mellitus without complications
    "E78.5",  # Hyperlipidemia, unspecified
    "E03.9",  # Hypothyroidism, unspecified
    "E66.9",  # Obesity, unspecified
    "J45.909",  # Asthma, unspecified, uncomplicated
    "J44.9",  # Chronic obstructive pulmonary disease, unspecified
    "J18.9",  # Pneumonia, unspecified organism
    "J06.9",  # Acute upper respiratory infection, unspecified
    "J20.9",  # Acute bronchitis, unspecified
    "U07.1",  # COVID-19
    "B34.9",  # Viral infection, unspecified
    "A09",  # Infectious gastroenteritis and colitis, unspecified
    "N39.0",  # Urinary tract infection, site not specified
    "B20",  # Human immunodeficiency virus [HIV] disease
    "G43.909",  # Migraine, unspecified, not intractable
    "G40.909",  # Epilepsy, unspecified, not intractable
    "G35",  # Multiple sclerosis
    "G20",  # Parkinson’s disease
    "I63.9",  # Cerebral infarction, unspecified
    "F32.9",  # Major depressive disorder, single episode, unspecified
    "F33.9",  # Major depressive disorder, recurrent, unspecified
    "F41.9",  # Anxiety disorder, unspecified
    "F10.20",  # Alcohol dependence, uncomplicated
    "F20.9",  # Schizophrenia, unspecified
    "M54.5",  # Low back pain
    "M17.9",  # Osteoarthritis of knee, unspecified
    "M79.1",  # Myalgia
    "M25.50",  # Joint pain, unspecified joint
    "M81.0",  # Age-related osteoporosis without fracture
    "K21.9",  # Gastro-esophageal reflux disease without esophagitis
    "K52.9",  # Noninfective gastroenteritis and colitis, unspecified
    "K76.0",  # Fatty (change of) liver, not elsewhere classified
    "K80.20",  # Calculus of gallbladder without cholecystitis
    "K29.70",  # Gastritis, unspecified, without bleeding
    "N18.9",  # Chronic kidney disease, unspecified
    "N17.9",  # Acute kidney failure, unspecified
    "N40.0",  # Benign prostatic hyperplasia without symptoms
    "R32",  # Urinary incontinence, unspecified
    "C34.90",  # Malignant neoplasm of lung, unspecified
    "C50.919",  # Malignant neoplasm of breast, unspecified
    "C18.9",  # Malignant neoplasm of colon, unspecified
    "C61",  # Malignant neoplasm of prostate
    "C71.9",  # Malignant neoplasm of brain, unspecified
    "R53.83",  # Other fatigue
]

CCEs = [
    "REGULATORY_JURISDICTION",
    "COMMERCIAL_USE",
    "RETURN_OF_RESULTS",
    "CONTACT_TO_PARTICIPATE",
    "GENERATION_OF_BIOLOGICAL_PRODUCTS",
    "RETURN_OF_INCIDENTAL_FINDINGS",
    "DATA_LINKAGE",
    "DATA_SAMPLE_POST_MORTEM_REUSE",
]
