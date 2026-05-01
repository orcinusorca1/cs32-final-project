# CityMatch
import csv

# load da data
#   Open the CSV file
#   For each row, read the city's name and numeric features
#   Store all cities as a list of dictionaries
with open("City_Data.csv", newline="") as f:
   reader = csv.DictReader(f)
   cities = []
   for row in reader:
       cities.append({
           "name": row["City"],
           "temp": float(row["1991-2020 Mean Temp. (°F)"].replace(",", "")),
           "cost": float(row["Cost of Living Index"].replace(",", "")),
           "density": float(row["Population Density (/m^2)"].replace(",", "")),
           "crime": float(row["Total Crime /100K"].replace(",", "")),
           "transit": float(row["Transit Score"].replace(",", "")),
           "walk": float(row["Walkability Score"].replace(",", "")),
           "education": float(row["Education Score"].replace(",", "")),
       })

# normalize the city data (using min-max scaling)
#   For each feature (temp, cost, density, etc.):
#     Find the lowest and highest value across all cities
#     For each city, rescale its value to between 0 and 1
#       where 0 = worst city in dataset, 1 = best city in dataset
#   This lets us fairly compare features that use totally different scales
#   (e.g. temperature in °F vs. a 0–100 walkability index)
#
#   Also save the raw min/max for temp and density separately,
#   because we'll need them later to normalize the user's own inputs
#   using the same scale
for feature in ["temp", "cost", "density", "crime", "transit", "walk", "education"]:
    values = [c[feature] for c in cities]
    lo, hi = min(values), max(values)
    for c in cities:
        c[feature + "_norm"] = (c[feature] - lo) / (hi - lo)

temp_lo, temp_hi = min(c["temp"] for c in cities), max(c["temp"] for c in cities)
density_lo, density_hi = min(c["density"] for c in cities), max(c["density"] for c in cities)


# Density preference map
#   Instead of asking the user to type a raw number like "27,345 people/sq mile",
#   let them pick low/medium/high
#   and map that label to a representative numeric value behind the scenes
DENSITY_MAP = {
   "low":    2_000,
   "medium": 10_000,
   "high":   30_000,
}

# ANSI color codes for bar chart coloring
#   Each feature gets its own color so the breakdown is easy to read at a glance
BAR_COLORS = {
    "Temperature": "\033[38;5;208m",  # orange
    "Density": "\033[38;5;141m",  # purple
    "Affordability": "\033[38;5;82m",   # green
    "Safety": "\033[38;5;196m",  # red
    "Transit":  "\033[38;5;39m",   # blue
    "Walkability": "\033[38;5;226m",  # yellow
    "Education": "\033[38;5;51m",   # cyan
}
RESET = "\033[0m"


# Helper functions for validated input
#   get_rating: keeps asking until the user types a number between 1 and 5
#   get_temp: keeps asking until the user types any valid number
#   Both functions protect the rest of the program from crashing on bad input
def get_rating(prompt):
   while True:
       try:
           val = float(input(prompt))
           if 1 <= val <= 5:
               return val
           print("  Please enter a number between 1 and 5.\n")
       except ValueError:
           print("  Invalid input — please enter a number between 1 and 5.\n")


def get_temp(prompt):
   while True:
       try:
           return float(input(prompt))
       except ValueError:
           print("  Invalid input — please enter a number.\n")


# Collect user preferences
#   Ask the user:
#     - What temperature do they prefer?
#     - How dense do they want the city to be? (low/medium/high)
#     - Do they have kids? (asked HERE alongside other preferences,
#       so we can boost safety/education weights before normalization
#       rather than applying a separate flat bonus afterward)
#     - How much does each feature matter to them, rated 1–5?
print("\n=== CityMatch ===")
print("Answer a few questions to find your ideal city.\n")

print("── Your Preferences ──────────────────────────")
user_temp = get_temp("  Preferred mean temperature (°F): ")

while True:
   density_choice = input("  Preferred population density (low / medium / high): ").strip().lower()
   if density_choice in DENSITY_MAP:
       user_density = DENSITY_MAP[density_choice]
       break
   print("  Please enter low, medium, or high.\n")

# New addition!! Kids question is now part of preferences
# We ask it before the ratings so we can automatically nudge safety
# and education weights upward before the user even sees them. the
# adjustment is incorporated into the weighting system rather than added as
# a separate bonus on top of the final score.
has_kids = input("  Do you have children? (yes/no): ").strip().lower() == "yes"

print("\n── What matters most to you? (rate each 1–5) ──")
temp_w = get_rating("  Temperature match:          ")
density_w = get_rating("  Population density match:   ")
afford_w = get_rating("  Affordability:              ")
safety_w = get_rating("  Safety:                     ")
transit_w = get_rating("  Public transit access:      ")
walk_w = get_rating("  Walkability:                ")
education_w = get_rating("  Education quality:          ")
print("───────────────────────────────────────────────\n")

# Kids weight boost
#   If the user has kids, increase safety and education weights by 1.5x
#   BEFORE normalization. This means the boost is proportional to how
#   much the user already cares. if they rated safety a 5, the boost
#   is larger than if they rated it a 1. It also gets absorbed into the
#   normalization step so the total still sums to 1.
if has_kids:
    safety_w  *= 1.5
    education_w *= 1.5

# Normalize user inputs
#   The user typed raw values (e.g. 72°F, "medium" density)
#   We rescale them to [0,1] using the same min/max from the city dataset
#   so they're directly comparable to the normalized city values
#
#   Then clamp, so if the user's value falls outside the dataset range,
#   clip it to 0 or 1 so nothing breaks
#
#   Also normalize the importance weights the user gave (1–5 ratings)
#   by dividing each by the total, so all weights together sum to exactly 1
#   This prevents a user who rates everything 5 from getting a
#   different result than one who rates everything 1
user_temp_norm = (user_temp - temp_lo) / (temp_hi - temp_lo)
user_density_norm = (user_density - density_lo) / (density_hi - density_lo)
user_temp_norm = max(0.0, min(1.0, user_temp_norm))
user_density_norm = max(0.0, min(1.0, user_density_norm))

total_w = temp_w + density_w + afford_w + safety_w + transit_w + walk_w + education_w
temp_w /= total_w
density_w /= total_w
afford_w /= total_w
safety_w /= total_w
transit_w /= total_w
walk_w /= total_w
education_w /= total_w

# Find which feature the user weighted most heavily (after normalization)
# Used later to pick a meaningful "you might also like" recommendation
weight_map = {
    "temp": temp_w,
    "cost": afford_w,
    "density": density_w,
    "crime": safety_w,
    "transit": transit_w,
    "walk": walk_w,
    "education": education_w,
}
top_feature = max(weight_map, key=weight_map.get)


# Scoring function
#   Given one city, calculate how well it matches the user's preferences
#
#   For "match" features (temp, density):
#     Score = 1 - distance from user's preference
#     Perfect match → 1.0, opposite end of scale → 0.0
#
#   For "lower is better" features (cost, crime):
#     Score = 1 - normalized value
#     Cheapest/safest city → 1.0, most expensive/dangerous → 0.0
#
#   For "higher is better" features (transit, walkability, education):
#     Score = normalized value directly
#     Best city → 1.0, worst → 0.0
#
#   Multiply each score by its normalized weight, then sum everything up
#   Return the total score and a breakdown so we can show the user why
def score_city(c):
   temp_match = 1 - abs(c["temp_norm"] - user_temp_norm)
   density_match = 1 - abs(c["density_norm"] - user_density_norm)
   cost_score = 1 - c["cost_norm"]
   safety_score = 1 - c["crime_norm"]
   transit_score = c["transit_norm"]
   walk_score = c["walk_norm"]
   education_score = c["education_norm"]

   breakdown = {
       "Temperature": round(temp_w  * temp_match, 3),
       "Density": round(density_w  * density_match, 3),
       "Affordability": round(afford_w * cost_score, 3),
       "Safety": round(safety_w * safety_score, 3),
       "Transit": round(transit_w * transit_score, 3),
       "Walkability": round(walk_w  * walk_score, 3),
       "Education": round(education_w * education_score, 3),
   }

   total = sum(breakdown.values())
   return total, breakdown


# Rank all cities
#   Run score_city() on every city in the dataset
#   Sort the results highest score first
scores = [(score_city(c), c) for c in cities]
scores.sort(key=lambda x: x[0][0], reverse=True)

top_3_names = {scores[i][1]["name"] for i in range(min(3, len(scores)))}

# "You might also like" is tied to what the user actually values most
#   Instead of always surfacing the safest city, we find the city outside
#   the top 3 that scores best on whichever feature the user weighted highest.
#   This makes the bonus recommendation feel relevant to the specific user
#   rather than defaulting to a safety recommendation everyone gets the same.
#
#   For "lower is better" features (cost, crime), we pick the city with the
#   lowest raw value. For all others, we pick the city with the highest.
lower_is_better = {"cost", "crime"}

if top_feature in lower_is_better:
    bonus_city = min(
        [c for c in cities if c["name"] not in top_3_names],
        key=lambda c: c[top_feature]
    )
else:
    bonus_city = max(
        [c for c in cities if c["name"] not in top_3_names],
        key=lambda c: c[top_feature]
    )

# Human-readable label for the bonus city blurb
FEATURE_LABELS = {
    "temp": ("average temperature", lambda c: f"{c['temp']}°F"),
    "cost": ("cost of living",lambda c: f"index {c['cost']}"),
    "density":("population density", lambda c: f"{c['density']:,.0f}/sq mi"),
    "crime": ("safety", lambda c: f"{c['crime']:.0f} crimes/100K"),
    "transit": ("transit score", lambda c: str(c['transit'])),
    "walk": ("walkability",lambda c: str(c['walk'])),
    "education":("education score",lambda c: str(c['education'])),
}


# Display function
#   Print the top 3 cities, skipping any the user has already rejected
#   For each city show:
#     - Overall score
#     - Key stats (temp, cost, crime, transit, walk, education)
#     - A colored bar chart breakdown of how much each feature contributed
#   Then show the "you might also like" bonus city, labeled with
#   the specific feature it excels at (the user's top-weighted feature)
def display_results(scores, rejected=None):
   print("\n=== Top 3 CityMatch Recommendations ===\n")

   shown = 0
   for (total, breakdown), c in scores:
       if rejected and c["name"] in rejected:
           continue
       if shown == 3:
           break

       temp_diff = abs(c["temp"] - user_temp)
       print(f" {shown + 1}. {c['name']}  (score: {total:.3f})")
       print(f" Avg temp {c['temp']}°F  (you wanted {user_temp}°F, diff={temp_diff:.1f}°)")
       print(f" Cost index {c['cost']}  |  Crime/100K {c['crime']:.0f}")
       print(f" Transit score {c['transit']}  |  Walk score {c['walk']}  |  Education score {c['education']:.0f}")
       print(f" Score breakdown:")
       for feature, contribution in breakdown.items():
           if contribution > 0:
               color = BAR_COLORS.get(feature, "")
               bar = "█" * int(contribution * 100)
               print(f" {feature:<15} {contribution:.3f}  {color}{bar}{RESET}")
       print()
       shown += 1

   # Bonus recommendation - labeled so the user understands why it's shown
   if not rejected or bonus_city["name"] not in rejected:
       s, _ = score_city(bonus_city)
       label, value_fn = FEATURE_LABELS[top_feature]
       print("── You might also like ────────────────────────")
       print(f" {bonus_city['name']}  (score: {s:.3f})")
       print(f" Recommended because you prioritized {label}: {value_fn(bonus_city)}")
       print(f" Cost index {bonus_city['cost']}  |  Avg temp {bonus_city['temp']}°F\n")

# Show the results

display_results(scores)
print("Good luck with your move!\n")
