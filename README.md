Here’s a draft README for your project: 

(Yes, I left this in here as a joke)

Foreword: Most of this is AI generated, and not checked for acuracy. I just kinda shat this code out using ChatGPT in a day - so, this project isn't very serious.

---

# Starfield Planet Data Scraper

## Part 1: Scrape

This script is designed to extract detailed planet data from [Inara.cz](https://inara.cz/starfield/) for the game *Starfield*. It scrapes information such as system names, planet attributes, available resources, and biome types, storing this data in a JSON format for further processing.

### Requirements

Ensure the following Python packages are installed:
- `requests`
- `beautifulsoup4`

You can install them via:
```bash
pip install requests beautifulsoup4
```

### Usage

1. Place resource dictionaries in `data/inorganic.csv` and `data/organic.csv`.
2. Run the script to scrape data for star systems.

The script will:
- Extract each star system’s data, with fields such as planet names, gravity, and resources.
- Convert certain symbols or subscript numerals for improved readability.
- Clean up specific attributes like `biomes` and `planetary_habitation` based on predefined dictionaries and patterns.

### Output

The data is saved to `data/1_scraped_systems_data.json`, formatted as:

```json
[
    {
        "system_name": "System X",
        "planets": [
            {
                "planet": "Planet A",
                "gravity": "1.0g",
                "resources": {
                    "inorganic": ["Iron", "Nickel"],
                    "organic": ["Carbon"],
                    "other": []
                },
                "biomes": ["Tropical"]
            }
        ]
    }
]
```

---

## Part 2: Clean Data

This script standardizes and classifies the scraped planet data, enhancing consistency and readability. It organizes attributes like planet types, atmospheric properties, and day lengths.

### Functionality

- **Planet Type Classification**: Classifies planets as either `Gas` or `Terrestrial` based on their type description.
- **Atmosphere Standardization**: Normalizes atmospheric descriptions to maintain consistent density, type, and properties (e.g., "Extreme" or "Standard").
- **Day Length Conversion**: Converts day lengths from days to hours where needed for uniformity.

### Usage

1. Ensure the output file from Part 1, `data/1_scraped_systems_data.json`, is present.
2. Run the script to process and clean up the data.

### Output

The cleaned data is saved to `data/2_clean_systems_data.json` in this format:

```json
[
    {
        "system_name": "System X",
        "planets": [
            {
                "planet": "Planet A",
                "planet_type": ["Terrestrial", "Desert"],
                "atmosphere": {
                    "density": "Thin",
                    "type": "Oxygen-rich",
                    "property": null
                },
                "resources": {
                    "inorganic": ["Iron", "Nickel"],
                    "organic": ["Carbon"],
                    "other": []
                },
                "day_length": "48 hours"
            }
        ]
    }
]
```

Each entry now includes standardized and classified data, ready for further analysis or visualization.

---

## Part 3: Scoring Planets

This script scores each planet and system based on the availability and rarity of resources, as well as habitability and biome diversity.

### Scoring Logic

The scoring is calculated in three stages:

1. **Resource Group Counting**:
   - **Function**: `count_resource_groups(input_list, resource_groups)`
   - **Purpose**: To categorize and count resources based on predefined resource groups.
   - **Process**: 
     - Resources are matched to group definitions in `inorganic_groups.json`.
     - Each resource is assigned a group label (e.g., `Chlorine-Xenon`), and a count is maintained for each group found on a planet.
   - **Output**: A dictionary of resource groups with counts, which is later used to calculate the inorganic resource score.

2. **Resource Scoring by Rarity**:
   - **Function**: `score_resources(resource_list, resource_dict)`
   - **Purpose**: To assign scores based on resource rarity.
   - **Scoring Scale**:
     - `Common`: 1 point
     - `Uncommon`: 2 points
     - `Rare`: 4 points
     - `Exotic`: 8 points
     - `Unique`: 16 points
   - **Process**:
     - Each resource in the `resource_list` is looked up in the `resource_dict`, and its rarity score is summed.
     - If the resource's rarity is undefined, it defaults to the `Common` score.

    **TODO**: Analyze the impact changing the scores has on the end results. 

3. **Planet Scoring**:
   - **Function**: `score_planet(planet, inorganic_dict, organic_dict)`
   - **Components of the Planet Score**:
     - **Habitability Score**: Based on `planetary_habitation`, where higher values represent planets requiring higher skills for habitation. This is a placeholder, as I didn't have anything I wanted to do with this yet. 
     - **Inorganic Resource Score**:
       - Calculated by scoring each resource in the `inorganic` list, multiplied by a `biome_resource_ratio`.
       - The `biome_resource_ratio` adjusts the score based on the diversity of biomes, calculated as the ratio of inorganic groups to biomes, promoting planets with a wide variety of resources in fewer biomes.
     - **Organic Resource Score**:
       - Calculated only if the planet contains water, because you need that shit for greenhouses.
       - Each organic resource in the list is scored similarly to the inorganic resources but without the biome ratio.
   - **Planet’s Total Score**:
     - `planet_resource_score = resource_score_inorganic + resource_score_organic`

   - **Output**: Each planet gets a dictionary with detailed scores:
     ```json
     {
         "habitability_score": "3.000",
         "resource_score": "6.250",
         "organic_score": "2.000",
         "inorganic_score": "4.250"
     }
     ```

     **TODO**: Make a better habitability score. I'd like to get a list of 'nice planets' with forest and lakes and shit. 

4. **System-Level Scoring**:
   - **Function**: `score_system(system, inorganic_dict, organic_dict)`
   - **Purpose**: To aggregate and average planet scores within each star system.
   - **Process**:
     - Each system's `inorganic_score` and `organic_score` are calculated as averages of all planets' respective scores.
     - The final `resource_score` for the system is the sum of its average `inorganic_score` and `organic_score`.
   - **Output**: Each system is given a combined score dictionary:
     ```json
     {
         "resource_score": "8.500",
         "organic_score": "4.000",
         "inorganic_score": "4.500"
     }
     ```

     **TODO**: Instead of averaging scores, I'd love to analyze the system more deeply - systems with more overall unique resources should be weighted high, and then higher if those resources are central on few planets. However, this opens a can of worms since we don't have biome data.

### Usage

1. Ensure the cleaned data (`data/2_clean_systems_data.json`), resource group definitions (`data/inorganic_groups.json`), and resource dictionaries (`data/inorganic.csv`, `data/organic.csv`) are available.
2. Run the script to compute scores.

### Output

The scored data is saved to `data/3_scored_systems_data.json`, which includes scores for individual planets and their containing systems. This output enables prioritization of planets and systems based on resource availability and habitability considerations.

---

## Part 4: Analyzing Planetary Resources and Finding the Best Systems

This section details the core functions used to analyze planetary resources and determine the best systems based on resource availability.

### `analyze_planetary_resources`

The `analyze_planetary_resources` function evaluates each planet within a given system to assess the availability of inorganic resources and categorize them based on complete resource groups and unique resources.

#### Parameters:
- **`system_data`**: A list of systems, each containing planets with associated resources and scores.
- **`inorganic_groups`**: A dictionary that specifies the required resources for each inorganic resource group.
- **`unique_resources`**: A set of resources marked as unique for filtering purposes.

#### Function Logic:
1. **Initialization**: 
   - Creates two lists: `results` for planets with complete resource groups and `unique_results` for those with unique resources.

2. **Iterate Through Systems and Planets**:
   - For each planet, retrieve its inorganic resources and associated scores.
   - Construct a `base_info` dictionary containing essential planet details (e.g., scores, atmosphere).

3. **Check for Complete Resource Groups**:
   - Verify if the planet's resources fulfill the requirements of each inorganic resource group.
   - If conditions are met, append a modified copy of `base_info` to `results`.

4. **Identify Unique Resources**:
   - Gather any unique resources present on the planet.
   - If found, create a copy of `base_info` for `unique_results`.

5. **Sorting**:
   - Both `results` and `unique_results` are sorted by inorganic score in descending order.

#### Returns:
- A tuple containing:
  - `results`: List of planets with complete resource groups.
  - `unique_results`: List of planets with unique resources.

---

### `find_best_systems`

The `find_best_systems` function identifies the best systems based on the availability of resource groups and unique resources, emphasizing those systems that provide the most valuable resources.

#### Parameters:
- **`complete_resource_planets`**: List of planets that have complete resource groups.
- **`unique_resource_planets`**: List of planets that have unique resources.
- **`inorganic_groups_flat`**: A flat representation of inorganic resource groups for efficient look-up.

#### Function Logic:
1. **Initialization**:
   - Two lists: `final_planets` for the best planets and `unique_resource_systems` for tracking systems with unique resources.

2. **Collect Unique Resource Planets**:
   - Process `unique_resource_planets` to convert unique resources into a string under the `resource` key.
   - Append these planets to `final_planets` and note their systems.

3. **Append All Planets from Unique Resource Systems**:
   - For each unique system, all planets are added to `final_planets`.

4. **Tracking**:
   - Use `captured_resources` to track resources already noted and `processed_systems` to track evaluated systems.

5. **Iterative Processing**:
   - The function enters a loop until all uncaptured resources are collected:
     - Identify uncaptured resources from `inorganic_groups_flat`.
     - Score systems based on how many uncaptured resources they provide.
     - Sort systems by score and select the highest scoring system to add to `final_planets`.

#### Returns:
- `final_planets`: A list of planets from the best systems providing the most valuable resources.

