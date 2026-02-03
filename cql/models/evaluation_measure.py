from cql.models import FHIRResource


class EvaluationMeasure(FHIRResource):
    SUBJECT_LIST = "subject-list"
    POPULATION = "population"

    def __init__(self, period_start, period_end, report_type, cce_choice,cce_code,diagnosis_code,sample_type, patient_gender):
        assert report_type in (self.SUBJECT_LIST, self.POPULATION)
        self.period_start = period_start
        self.period_end = period_end
        self.report_type = report_type
        self.cce_choice = cce_choice
        self.cce_code = cce_code
        self.diagnosis_code = diagnosis_code
        self.sample_type = sample_type
        self.patient_gender = patient_gender

        super(EvaluationMeasure, self).__init__(
            {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "periodStart", "valueDate": self.period_start},
                    {"name": "periodEnd", "valueDate": self.period_end},
                    {"name": "reportType", "valueCode": self.report_type},
                    {"name": "CCEChoice", "valueString": self.cce_choice},
                    {"name": "CCECode", "valueString": self.cce_code},
                    {"name": "DiagnosisCode", "valueString": self.diagnosis_code},
                    {"name": "SampleType", "valueString": self.sample_type},
                    {"name": "PatientGender", "valueString": self.patient_gender},
                ],
            }
        )
