# CS32 Final Project

Our overarching program is a house search platform/location generator (similar to something like Zillow) based on your personality/preferences.

## Description

### Motivation
This is an algorithm designed to help users identify U.S. cities that best align with their lifestyle preferences. Inspired by other platforms like Zillow, this project focuses on the earliest and often most difficult step of the housing search process, which is choosing the right location/finding a starting place to search for specific housing. Users will input their preferences, such as climate, cost of living, population density, job opportunities, and safety, and the program analyzes these inputs to generate personalized city recommendations from a curated dataset of major U.S. cities. The algorithm combines everything into a centralized and streamlined platform so indecisive people don't have to search for each preference individually.

### Tech Framework
The code will ask the user to input based on a set scale of preferences and then feed the details all together into the algorithm.

Because different factors are measured on different scales, the program will first normalize all data to ensure fair comparisons, and then apply a weighted scoring system for more customized results. The program ranks all cities based on their computed scores and returns the top matches.

The goal is also to provide a brief explanation of its results so users understand why certain cities were selected and where trade-offs occur to help them refine their own further searches.

### Tools & Requirements
- **Language:** Python 3
- **Libraries:** Built-in csv module (no external packages required)
- **Environment:** Runs in any terminal or IDE (VS Code, PyCharm, etc.)
- **Data File:** `City_Data.csv` must be in the same directory as the Python file

### How to Run
1. Make sure `City_Data.csv` is in the project folder
2. Run the program: `python citymatch.py`
3. Follow the prompts in the terminal to input your preferences

### Algorithm Overview (High-Level Design)

**Inputs:**
- Preferred temperature
- Preferred population density (low/medium/high)
- Whether the user has children
- Importance ratings (1-5) for:
  - Temperature
  - Density
  - Affordability
  - Safety
  - Transit
  - Walkability
  - Education

**Process:**
- Load city data from CSV into dictionaries
- Normalize all features using min-max scaling
- Normalize user inputs to match dataset scale
- Adjust weights (boost safety and education if user has children)
- Compute a weighted score for each city
- Rank all cities from best to worst

**Outputs:**
- Top 3 recommended cities  
- Score breakdown showing how each factor contributed
- A bonus “you might also like” city based on the user’s top priority

Dataset manually compiled from publicly available city statistics.

## Use of Generative AI

We used generative AI tools in the following ways:
- To verify that our min-max normalization logic was implemented correctly
- To help generate color codes for the terminal bar visualization

All algorithm design and implementation were written by our team.

## Other Information

### Group Members

* Sarah Sun
* Kimberly Widjaja
* Dang Lin
