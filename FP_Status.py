# FP Status
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
           "name":      row["City"],
           "temp":      float(row["1991-2020 Mean Temp. (°F)"].replace(",", "")),
           "cost":      float(row["Cost of Living Index"].replace(",", "")),
           "density":   float(row["Population Density (/m^2)"].replace(",", "")),
           "crime":     float(row["Total Crime /100K"].replace(",", "")),
           "transit":   float(row["Transit Score"].replace(",", "")),
           "walk":      float(row["Walkability Score"].replace(",", "")),
           "education": float(row["Education Score"].replace(",", "")),
       })

# normalize the city data  (using min-max scaling)
#   For each feature (temp, cost, density, etc.):
#     Find the lowest and highest value across all cities
#     For each city, rescale its value to sit between 0 and 1
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

temp_lo,    temp_hi    = min(c["temp"]    for c in cities), max(c["temp"]    for c in cities)
density_lo, density_hi = min(c["density"] for c in cities), max(c["density"] for c in cities)


# Density preference map **NEWWWW
#   Instead of asking the user to type a raw number like "27,345 people/sq mile",
#   let them pick low / medium / high
#   and map that label to a representative numeric value behind the scenes

DENSITY_MAP = {
   "low":    2_000,
   "medium": 10_000,
   "high":   30_000,
}

# Using helper functions instead
#   get_rating: keeps asking until the user types a number between 1 and 5
#   get_temp:   keeps asking until the user types any valid number
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


# asking user preferences through all the specific questions
#   Ask the user:
#     - What temperature do they prefer?
#     - How dense do they want the city to be? (low/medium/high)
#     - How much does each feature matter to them, rated 1–5?
#     - Do they have kids? (used later for a bonus score adjustment)

print("\n=== City Recommender ===")
print("Answer a few questions to find your ideal city.\n")

print("── Your Preferences ──────────────────────────")
user_temp = get_temp("  Preferred mean temperature (°F): ")

while True:
   density_choice = input("  Preferred population density (low / medium / high): ").strip().lower()
   if density_choice in DENSITY_MAP:
       user_density = DENSITY_MAP[density_choice]
       break
   print("  Please enter low, medium, or high.\n")

print("\n── What matters most to you? (rate each 1-5) ──")
temp_w      = get_rating("  Temperature match:          ")
density_w   = get_rating("  Population density match:   ")
afford_w    = get_rating("  Affordability:              ")
safety_w    = get_rating("  Safety:                     ")
transit_w   = get_rating("  Public transit access:      ")
walk_w      = get_rating("  Walkability:                ")
education_w = get_rating("  Education quality:          ")

print("\n── A little more about you ────────────────────")
has_kids = input("  Do you have children? (yes/no): ").strip().lower() == "yes"
print("───────────────────────────────────────────────\n")

# normalizing input values
#   The user typed raw values (e.g. 72°F, "medium" density)
#   We rescale them to [0,1] using the same min/max from the city dataset
#   so they're directly comparable to the normalized city values
#
#   Then clamp: if the user's value falls outside the dataset range,
#   clip it to 0 or 1 so nothing breaks
#
#   Also normalize the importance weights the user gave (1–5 ratings)
#   by dividing each by the total — so all weights together sum to exactly 1
#   This prevents a user who rates everything 5 from getting a
#   different result than one who rates everything 1

user_temp_norm    = (user_temp    - temp_lo)    / (temp_hi    - temp_lo)
user_density_norm = (user_density - density_lo) / (density_hi - density_lo)
user_temp_norm    = max(0.0, min(1.0, user_temp_norm))
user_density_norm = max(0.0, min(1.0, user_density_norm))

total_w     = temp_w + density_w + afford_w + safety_w + transit_w + walk_w + education_w
temp_w      /= total_w
density_w   /= total_w
afford_w    /= total_w
safety_w    /= total_w
transit_w   /= total_w
walk_w      /= total_w
education_w /= total_w

# Calculating matches with user preferences
#   Given one city, calculate how well it matches the user's preferences
#
#   For "match" features (temp, density):
#     Score = 1 - distance from user's preference
#     Perfect match -> 1.0, opposite end of scale -> 0.0
#
#   For "lower is better" features (cost, crime):
#     Score = 1 - normalized value
#     Cheapest/safest city -> 1.0, most expensive/dangerous -> 0.0
#
#   For "higher is better" features (transit, walkability):
#     Score = normalized value directly
#     Best city -> 1.0, worst -> 0.0
#
#   NEW*** Kids bonus: if the user has children, add a small extra boost
#     based on safety and education scores (5% of each)
#
#   Multiply each score by its normalized weight, then sum everything up
#   Return the total score AND a breakdown so we can show the user why

def score_city(c):
   temp_match      = 1 - abs(c["temp_norm"]    - user_temp_norm)
   density_match   = 1 - abs(c["density_norm"] - user_density_norm)
   cost_score      = 1 - c["cost_norm"]
   safety_score    = 1 - c["crime_norm"]
   transit_score   = c["transit_norm"]
   walk_score      = c["walk_norm"]
   education_score = 1 - c["education_norm"]

   kids_bonus = 0.0
   if has_kids:
       kids_bonus = 0.05 * (safety_score + education_score)

   breakdown = {
       "Temperature":  round(temp_w      * temp_match,      3),
       "Density":      round(density_w   * density_match,   3),
       "Affordability":round(afford_w    * cost_score,      3),
       "Safety":       round(safety_w    * safety_score,    3),
       "Transit":      round(transit_w   * transit_score,   3),
       "Walkability":  round(walk_w      * walk_score,      3),
       "Education":    round(education_w * education_score, 3),
       "Kids bonus":   round(kids_bonus,                    3),
   }

   total = sum(breakdown.values())
   return total, breakdown

# Using the scores, rank cities for the user
#   Run score_city() on every city in the dataset
#   Sort the results highest score first
#
#   Also find a "you might also like" city:
#     Take the safest city (lowest crime) that didn't already make the top 3
#     to surface as a bonus recommendation

scores = [(score_city(c), c) for c in cities]
scores.sort(key=lambda x: x[0][0], reverse=True)

top_3_names = {scores[i][1]["name"] for i in range(min(3, len(scores)))}
safest_city = min(
   [c for c in cities if c["name"] not in top_3_names],
   key=lambda c: c["crime"]
)


# Terminal showing the results
#   Print the top 3 cities, skipping any the user has already rejected
#   For each city show:
#     - Overall score
#     - Key stats (temp, cost, crime, transit, walk, education)
#     - A bar chart breakdown of how much each feature contributed to the score
#   Then show the "you might also like" safest city as a bonus

def display_results(scores, rejected=None):
   print("\n=== Top 3 City Recommendations ===\n")

   shown = 0
   for (total, breakdown), c in scores:
       if rejected and c["name"] in rejected:
           continue
       if shown == 3:
           break

       temp_diff = abs(c["temp"] - user_temp)
       print(f"  {shown + 1}. {c['name']}  (score: {total:.3f})")
       print(f"     Avg temp {c['temp']}°F  (you wanted {user_temp}°F, diff={temp_diff:.1f}°)")
       print(f"     Cost index {c['cost']}  |  Crime/100K {c['crime']:.0f}")
       print(f"     Transit score {c['transit']}  |  Walk score {c['walk']}  |  Education rank {c['education']:.0f}")
       print(f"     Score breakdown:")
       for feature, contribution in breakdown.items():
           if contribution > 0:
               bar = "█" * int(contribution * 100)
               print(f"       {feature:<15} {contribution:.3f}  {bar}")
       print()
       shown += 1

   if not rejected or safest_city["name"] not in rejected:
       s, b = score_city(safest_city)
       print("── You might also like ────────────────────────")
       print(f"  {safest_city['name']}  (score: {s:.3f})")
       print(f"  Lowest crime rate in the dataset: {safest_city['crime']:.0f}/100K")
       print(f"  Cost index {safest_city['cost']}  |  Avg temp {safest_city['temp']}°F\n")


# The main loop which uses all helper functions
#   Show the results
#   Ask if the user wants to reject a city and see the next best option
#   If yes: add that city to the rejected set and redisplay, skipping it
#   If no:  print a goodbye message and exit

rejected = set()

while True:
   display_results(scores, rejected=rejected)

   again = input("Would you like to reject a recommendation and see the next city? (yes/no): ").strip().lower()
   if again != "yes":
       print("\nGood luck with your move!\n")
       break

   reject_name = input("Enter the exact city name to reject: ").strip()
   if reject_name in [c["name"] for c in cities]:
       rejected.add(reject_name)
       print(f"\n  '{reject_name}' removed. Re-ranking...\n")
   else:
       print("  City name not recognized, try again.\n")
