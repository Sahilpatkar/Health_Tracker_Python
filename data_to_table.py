import json
from typing import List, Dict, Any





parameters = [
    "Hemoglobin (Hb)",
    "Total Leucocytes (WBC) count",
    "Platelet count",
    "Red blood cell (RBC) count",
    "PCV (Packed Cell Volume)",
    "MCV (Mean Corpuscular Volume)",
    "MCH (Mean Corpuscular Hb)",
    "MCHC (Mean Corpuscular Hb Conc.)",
    "RDW (RBC distribution width)",
    "MPV (Mean Platelet Volume)",
    "Neutrophils",
    "Absolute Neutrophils",
    "Eosinophils",
    "Absolute Eosinophils",
    "Basophils",
    "Absolute Basophils",
    "Lymphocytes",
    "Absolute Lymphocytes",
    "Monocytes",
    "Absolute Monocytes",
    "Cholesterol (Total)",
    "Triglycerides",
    "HDL Cholesterol",
    "VLDL Cholesterol",
    "LDL Cholesterol",
    "Cholesterol/HDL Ratio",
    "LDL/HDL Ratio",
    "Apolipoprotein A1",
    "Apolipoprotein B",
    "ApoB/A1 Ratio",
    "Bilirubin-Total",
    "Bilirubin-Conjugated",
    "Bilirubin-Unconjugated",
    "SGOT (AST)",
    "SGPT (ALT)",
    "Alkaline Phosphatase",
    "Protein (Total)",
    "Albumin",
    "Globulin",
    "Plasma Glucose Fasting",
    "Urea",
    "BUN (Blood Urea Nitrogen)",
    "Creatinine",
    "25-OH Vitamin D",
    "Vitamin B12",
    "Insulin Fasting",
    "Free T3",
    "Free T4",
    "TSH (Ultrasensitive)",
    "Estimated Average Glucose (eAG)",
    "PSA",
    "hs-CRP",
    "Calcium",
    "ESR (Erythrocyte Sedimentation Rate)",
    "pH",
    "Protein",
    "Glucose",
    "Acetone",
    "Bile Pigments",
    "Urobilinogen",
    "RBCs",
    "Pus cells",
    "Epithelial cells",
    "Casts",
    "Crystals",
    "Quantity Examined",
    "Appearance",
    "Colour"
]

def skim_required_parameters(data:json) -> list[dict[str | Any, dict[str, str | None] | Any] | list[str]]:
    # for i in data["params"].keys():
    #     if i not in parameters:
    #         print(i)
    result_json = {}
    missing:list[str] = []
    for i in parameters:
        if i in data["params"].keys():
            result_json[i] = data["params"][i]
        else:
            result_json[i] = {'value': None, 'unit': 'NA'}
            missing.append(i)


    return [result_json, missing]

if __name__ == "__main__":
    out_path = "/Users/spatkar/PycharmProjects/Health_Tracker_Python/HealthReport/shashank/raw_report/report_SHASHANK ANANT PATKAR_2022-05-28T15:24:00.json"
    with open(out_path, "r") as f:
        datajson = json.load(f)
    print(skim_required_parameters(datajson)[1])

