
# ✅ Metrics where 0 is a valid and meaningful value (e.g., "Absent", "Not Detected")
zero_is_valid = {
    "Casts",
    "Bile Pigments",
    "Urobilinogen",
    "Acetone",
    "Crystals",
    "R.B.Cs",
    "Pus cells",
    "Epithelial cells",
    "Hypercalcemia",
    "Hypocalcemia",
    "Vitamin B12",
    "Serum methylmalonic acid",
    "Homocysteine",
    "Active B12 (Holotranscobalamin)"
}
# ✅ Metrics where negative values *could* make sense (e.g., delta scores, some derivatives)
negatives_allowed = {
    # Currently none in your health dataset, but keep for extensibility
}

# 🔒 Optional: List of critical metrics you always want to keep, even if 0 or null (for override)
always_keep = {
    # "Hemoglobin (Hb)",
    # "WBC",
}