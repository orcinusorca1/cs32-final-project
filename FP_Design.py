#FP Design Draft Code

import csv

##### dataset yay
# Open the CSV file for reading
with open("Five_Major_Cities.csv", newline="") as f:

    # Create a reader that maps each row to a dictionary using the header row as keys
    reader = csv.DictReader(f)

    # Build a list of cities; each city is a dict with cleaned numeric values
    cities = []
    for row in reader:
        # Append one dict per city, stripping commas and converting strings to floats- this gives them two decimal values to further narrow scope
        cities.append({
            "name":    row["City"],
            "temp":    float(row["1991-2020 Mean Temp. (°F)"].replace(",", "")),
            "cost":    float(row["Cost of Living Index"].replace(",", "")),
            "density": float(row["Population Density (/m^2)"].replace(",", "")),
            "crime":   float(row["Total Crime /100K"].replace(",", "")),
        })

####### evil normalise
# For each feature, find the min and max across all cities so we can scale to [0, 1]
for feature in ["temp", "cost", "density", "crime"]:
    # Pull out every city's raw value for this feature into a temporary list
    values = [c[feature] for c in cities]

    # Record the smallest and largest values
    lo, hi = min(values), max(values)

    # For each city, replace the raw value with its normalized version
    for c in cities:
        # Formula: (value - min) / (max - min)  →  result is between 0 and 1
        c[feature + "_norm"] = (c[feature] - lo) / (hi - lo)

# Save the min/max for temp and density so we can normalize user input the same way
temp_lo,    temp_hi    = min(c["temp"]    for c in cities), max(c["temp"]    for c in cities)
density_lo, density_hi = min(c["density"] for c in cities), max(c["density"] for c in cities)

###### user inpurr
print("\n=== City Recommender ===\n")

# Ask the user for their preferred average temperature in °F
user_temp    = float(input("Preferred mean temperature (°F): "))

# Ask the user for their preferred population density (people per sq mile)
user_density = float(input("Preferred population density (per sq mile) (For reference, high population density is around 30,000 and low can be around 2000): "))

# Ask how much affordability matters on a 1–5 scale
afford_w     = float(input("How important is affordability? (1–5): "))

# Ask how much safety matters on a 1–5 scale
safety_w     = float(input("How important is safety?       (1–5): "))

#### user input data normalise
# Apply the same min/max scaling used on the city data so inputs are comparable
user_temp_norm    = (user_temp    - temp_lo)    / (temp_hi    - temp_lo)
user_density_norm = (user_density - density_lo) / (density_hi - density_lo)

# Narrow scope of normalized values to [0, 1] in case the user enters something outside the dataset range
user_temp_norm    = max(0.0, min(1.0, user_temp_norm))
user_density_norm = max(0.0, min(1.0, user_density_norm))

###### score the cities yippeee yipee
scores = []  # Will hold (score, city_dict) tuples

for c in cities:
    # Temperature match: 1 means perfect match, 0 means opposite end of the scale
    temp_match    = 1 - abs(c["temp_norm"]    - user_temp_norm)

    # Density match: same logic as temperature
    density_match = 1 - abs(c["density_norm"] - user_density_norm)

    # Cost score: lower normalized cost → higher score (cheaper is better)
    cost_score    = 1 - c["cost_norm"]

    # Safety score: lower normalized crime → higher score (safer is better)
    safety_score  = 1 - c["crime_norm"]

    # Total score: sum the four components; affordability and safety are weighted by user preference
    total = temp_match + density_match + (afford_w * cost_score) + (safety_w * safety_score)

    # Store the result alongside the city dict
    scores.append((total, c))

##### ranking cities
# Sort the list by score, highest first (reverse=True)
scores.sort(key=lambda x: x[0], reverse=True)

#### outputting city yay
print("\n=== Top 3 City Recommendations ===\n")

# Loop over the top 3 entries in the ranked list
for rank, (score, c) in enumerate(scores[:3], start=1):
    # Print rank, city name, and rounded score
    print(f"{rank}. {c['name']}  (score: {score:.2f})")

    # Print a one-line explanation highlighting the city's two best traits
    temp_diff = abs(c["temp"] - user_temp)
    print(f"   Avg temp {c['temp']}°F (you wanted {user_temp}°F, diff={temp_diff:.1f}°), "
          f"Cost index {c['cost']}, Crime/100K {c['crime']:.0f}\n")
