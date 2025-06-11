import pybamm

# Get a list of all available parameter sets
all_parameters = pybamm.ParameterValues.values

# Print the list to see them all
print(all_parameters)

print("--- Finding LFP Parameter Sets ---")
lfp_sets = [p for p in all_parameters if "LFP" in p]
for lfp in lfp_sets:
    print(lfp)

print("\n--- Finding LG Parameter Sets ---")
lg_sets = [p for p in all_parameters if "LG" in p]
for lg in lg_sets:
    print(lg)