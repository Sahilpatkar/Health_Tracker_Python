CREATE TABLE IF NOT EXISTS cardio_stage_ranges (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    factor_name   VARCHAR(64),
    stage_label   VARCHAR(64),
    stage_number  INT, -- For sorting: Stage 1 = 1, etc.
    min_value     DECIMAL(5,2),
    max_value     DECIMAL(5,2)
);

-- Fasting Blood Glucose
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('plasma_glucose_fasting', 'Early Insulin Resistance', 1, 90.00, 100.00),
('plasma_glucose_fasting', 'Pre-Diabetes & Lipid Imbalance', 2, 100.00, 125.00),
('plasma_glucose_fasting', 'Metabolic Syndrome', 3, 125.00, 140.00),
('plasma_glucose_fasting', 'Diabetes & High Cardiovascular Risk', 4, 140.00, 180.00),
('plasma_glucose_fasting', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 180.00, 9999.99);

-- HbA1c
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('HbA1c', 'Early Insulin Resistance', 1, 5.50, 5.70),
('HbA1c', 'Pre-Diabetes & Lipid Imbalance', 2, 5.70, 6.40),
('HbA1c', 'Metabolic Syndrome', 3, 6.40, 7.50),
('HbA1c', 'Diabetes & High Cardiovascular Risk', 4, 7.50, 9.00),
('HbA1c', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 9.00, 20.00);

-- Fasting Insulin
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Insulin Fasting', 'Early Insulin Resistance', 1, 5.00, 10.00),
('Insulin Fasting', 'Pre-Diabetes & Lipid Imbalance', 2, 10.00, 20.00),
('Insulin Fasting', 'Metabolic Syndrome', 3, 20.00, 40.00),
('Insulin Fasting', 'Diabetes & High Cardiovascular Risk', 4, 40.00, 60.00),
('Insulin Fasting', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 60.00, 200.00);

-- LDL Cholesterol
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('LDL Cholesterol', 'Early Insulin Resistance', 1, 100.00, 130.00),
('LDL Cholesterol', 'Pre-Diabetes & Lipid Imbalance', 2, 130.00, 160.00),
('LDL Cholesterol', 'Metabolic Syndrome', 3, 160.00, 190.00),
('LDL Cholesterol', 'Diabetes & High Cardiovascular Risk', 4, 190.00, 220.00),
('LDL Cholesterol', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 220.00, 400.00);

-- HDL Cholesterol (reversed scale: higher = better)
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('HDL Cholesterol', 'Early Insulin Resistance', 1, 50.00, 999.99),
('HDL Cholesterol', 'Pre-Diabetes & Lipid Imbalance', 2, 40.00, 50.00),
('HDL Cholesterol', 'Metabolic Syndrome', 3, 30.00, 40.00),
('HDL Cholesterol', 'Diabetes & High Cardiovascular Risk', 4, 25.00, 30.00),
('HDL Cholesterol', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 0.00, 25.00);

-- VLDL
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('VLDL Cholesterol', 'Early Insulin Resistance', 1, 5.00, 20.00),
('VLDL Cholesterol', 'Pre-Diabetes & Lipid Imbalance', 2, 20.00, 30.00),
('VLDL Cholesterol', 'Metabolic Syndrome', 3, 30.00, 40.00),
('VLDL Cholesterol', 'Diabetes & High Cardiovascular Risk', 4, 40.00, 50.00),
('VLDL Cholesterol', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 50.00, 999.99);

-- Triglycerides
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Triglycerides', 'Early Insulin Resistance', 1, 100.00, 150.00),
('Triglycerides', 'Pre-Diabetes & Lipid Imbalance', 2, 150.00, 200.00),
('Triglycerides', 'Metabolic Syndrome', 3, 200.00, 300.00),
('Triglycerides', 'Diabetes & High Cardiovascular Risk', 4, 300.00, 400.00),
('Triglycerides', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 400.00, 1000.00);

-- Carb Intake
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Carb Intake', 'Early Insulin Resistance', 1, 250.00, 300.00),
('Carb Intake', 'Pre-Diabetes & Lipid Imbalance', 2, 150.00, 200.00),
('Carb Intake', 'Metabolic Syndrome', 3, 100.00, 150.00),
('Carb Intake', 'Diabetes & High Cardiovascular Risk', 4, 50.00, 100.00),
('Carb Intake', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 0.00, 50.00);

-- Protein Intake (per kg body weight)
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Protein Intake', 'Early Insulin Resistance', 1, 0.60, 0.80),
('Protein Intake', 'Pre-Diabetes & Lipid Imbalance', 2, 0.80, 1.00),
('Protein Intake', 'Metabolic Syndrome', 3, 1.00, 1.20),
('Protein Intake', 'Diabetes & High Cardiovascular Risk', 4, 1.20, 1.50),
('Protein Intake', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 1.50, 2.00);

-- Fat Intake
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Fat Intake', 'Early Insulin Resistance', 1, 80.00, 999.99),
('Fat Intake', 'Pre-Diabetes & Lipid Imbalance', 2, 60.00, 80.00),
('Fat Intake', 'Metabolic Syndrome', 3, 50.00, 70.00),
('Fat Intake', 'Diabetes & High Cardiovascular Risk', 4, 40.00, 60.00),
('Fat Intake', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 40.00, 50.00);

-- Sleep
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Sleep', 'Early Insulin Resistance', 1, 6.00, 7.00),
('Sleep', 'Pre-Diabetes & Lipid Imbalance', 2, 6.00, 7.00),
('Sleep', 'Metabolic Syndrome', 3, 6.50, 7.50),
('Sleep', 'Diabetes & High Cardiovascular Risk', 4, 7.00, 8.00),
('Sleep', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 7.50, 8.50);

-- Calories Burned
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Calories Burned', 'Early Insulin Resistance', 1, 1500.00, 2000.00),
('Calories Burned', 'Pre-Diabetes & Lipid Imbalance', 2, 1500.00, 1800.00),
('Calories Burned', 'Metabolic Syndrome', 3, 1400.00, 1700.00),
('Calories Burned', 'Diabetes & High Cardiovascular Risk', 4, 1300.00, 1600.00),
('Calories Burned', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 1200.00, 1500.00);

-- Exercise
INSERT INTO cardio_stage_ranges (factor_name, stage_label, stage_number, min_value, max_value)
VALUES
('Exercise', 'Early Insulin Resistance', 1, 0.00, 30.00),
('Exercise', 'Pre-Diabetes & Lipid Imbalance', 2, 30.00, 40.00),
('Exercise', 'Metabolic Syndrome', 3, 40.00, 60.00),
('Exercise', 'Diabetes & High Cardiovascular Risk', 4, 60.00, 120.00),
('Exercise', 'Critical Organ Risk (Heart Attack/Stroke)', 5, 60.00, 180.00);

