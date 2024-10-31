import json
import csv
from common import *
from itertools import product
import matplotlib.pyplot as plt

def get_attribute_value(planet, attribute):
    """Extracts a comparable value for a specific attribute from the planet data."""
    if attribute == 'planet_type':
        return planet['attributes'].get(attribute, [None, None])[1]  # Return subtype only
    elif attribute == 'atmosphere':
        atmosphere = planet['attributes'].get('atmosphere')
        return f"{atmosphere.get('density', 'Unknown')} {atmosphere.get('type', 'Unknown')}" if atmosphere else None
    elif attribute == 'biomes':
        return planet.get(attribute, [])
    else:
        return planet['attributes'].get(attribute)

def get_unique_values(planets, attribute):
    """Fetch unique values for a given attribute from the dataset."""
    unique_values = set()
    for planet in planets:
        value = get_attribute_value(planet, attribute)
        if isinstance(value, list):
            unique_values.update(value)  # For lists like 'biomes'
        else:
            unique_values.add(value)
    print(f'Unique values for {attribute}: {unique_values}')  # Debug print
    return unique_values

def get_attribute_combos(planets, attribute1, attribute2):
    """Find combinations of unique attribute values, count planets, and save data."""
    unique_values1 = get_unique_values(planets, attribute1)
    unique_values2 = get_unique_values(planets, attribute2)
    
    combinations = list(product(unique_values1, unique_values2))
    combo_data = []

    for val1, val2 in combinations:
        matching_planets = [
            planet['name'] for planet in planets 
            if (get_attribute_value(planet, attribute1) == val1 or
                (attribute1 == 'biomes' and val1 in get_attribute_value(planet, attribute1))) and
               (get_attribute_value(planet, attribute2) == val2 or
                (attribute2 == 'biomes' and val2 in get_attribute_value(planet, attribute2)))
        ]
        count = len(matching_planets)
        combo_data.append([val1, val2, count, matching_planets])
        print(f'Combination {val1}, {val2}: count={count}, planets={matching_planets}')  # Debug print

    output_csv = f"graph_{attribute1}_{attribute2}.csv"
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([attribute1, attribute2, 'count', 'planet_list'])
        for row in combo_data:
            writer.writerow(row)
    print(f'Data written to {output_csv}')  # Debug print

    plot_bar_graph(combo_data, attribute1, attribute2)

def plot_bar_graph(combo_data, attribute1, attribute2):
    """Plot a bar graph for the attribute combinations and their counts with callouts for values."""
    labels = [f'{val1}, {val2}' for val1, val2, _, _ in combo_data]
    counts = [count for _, _, count, _ in combo_data]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, counts)
    plt.xticks(rotation=90)
    plt.xlabel(f'{attribute1} and {attribute2} combinations')
    plt.ylabel('Count')
    plt.title(f'Planet Count by {attribute1} and {attribute2}')
    
    # Adding callouts above each bar with the count value
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            int(yval),
            ha='center',
            va='bottom',
            fontsize=9
        )
    
    plt.tight_layout()
    plt.show()



    
def get_min_max(planets, parameter):
    """Return the planet name with the min and max values for a numerical parameter like gravity or day_length."""
    min_value, max_value = float('inf'), float('-inf')
    min_planet, max_planet = None, None

    for planet in planets:
        if parameter in planet:
            value = planet['attributes'][parameter]
            try:
                # Convert value to a float (e.g., '0.89g' to 0.89)
                if 'g' in value:
                    value = float(value.replace('g', ''))
                elif 'hours' in value:
                    value = float(value.split()[0])
                else:
                    value = float(value)

                # Update min and max values and track the planet names
                if value < min_value:
                    min_value, min_planet = value, planet['name']
                if value > max_value:
                    max_value, max_planet = value, planet['name']
            except ValueError:
                continue

    return (min_planet, min_value) if min_planet else None, (max_planet, max_value) if max_planet else None

def planet_with_most_resources(planets, resource_type):
    """Return all planets with the highest count of a given resource type."""
    max_resources = 0
    planets_with_max = []

    for planet in planets:
        count = len(planet['resources'].get(resource_type, []))
        
        if count > max_resources:
            max_resources = count
            planets_with_max = [planet['name']]
        elif count == max_resources and count > 0:
            planets_with_max.append(planet['name'])

    return planets_with_max, max_resources

def system_with_most(systems, parameter, values):
    """Return all systems with the most planets of specified types, e.g., 'gas giants'."""
    max_count = 0
    systems_with_max = []

    for system in systems:
        count = sum(1 for planet in system['planets'] 
                    if parameter == 'planet_type' and planet['attributes'][parameter][0] in values)
        
        # Track the systems with the highest count
        if count > max_count:
            max_count = count
            systems_with_max = [system['name']]
        elif count == max_count and count > 0:
            systems_with_max.append(system['name'])

    return systems_with_max, max_count

def system_with_most_planets(systems):
    """Return the system with the most planets."""
    return max(systems, key=lambda system: len(system['planets']))['name']

def system_with_least_planets(systems):
    """Return the system with the most planets."""
    return min(systems, key=lambda system: len(system['planets']))['name']


def planet_with_highest_lowest_score(planets, score_type):
    """Return the planets with the highest and lowest specified score."""
    max_planet, min_planet = None, None
    max_score, min_score = float('-inf'), float('inf')

    for planet in planets:
        score = float(planet['scores'].get(score_type, 0))
        
        if score > max_score:
            max_score = score
            max_planet = planet['name']
        if score < min_score:
            min_score = score
            min_planet = planet['name']

    return (max_planet, max_score), (min_planet, min_score)

def system_with_highest_lowest_score(systems, score_type):
    """Return the systems with the highest and lowest specified score."""
    max_system, min_system = None, None
    max_score, min_score = float('-inf'), float('inf')

    for system in systems:
        score = float(system['scores'].get(score_type, 0))
        
        if score > max_score:
            max_score = score
            max_system = system['name']
        if score < min_score:
            min_score = score
            min_system = system['name']

    return (max_system, max_score), (min_system, min_score)

def top_n_systems(systems, score_type, n=10):
    """Return the top N systems based on the specified score type."""
    sorted_systems = sorted(systems, key=lambda x: float(x['scores'].get(score_type, 0)), reverse=True)
    return [(system['name'], float(system['scores'].get(score_type, 0))) for system in sorted_systems[:n]]

def top_n_planets(planets, score_type, n=10):
    """Return the top N planets based on the specified score type."""
    sorted_planets = sorted(planets, key=lambda x: float(x['scores'].get(score_type, 0)), reverse=True)
    return [(planet['name'], float(planet['scores'].get(score_type, 0))) for planet in sorted_planets[:n]]

if __name__ == '__main__':
    systems = load_system_data(SCORED_SYSTEM_DATA_PATH)
    planets = [planet for system in systems for planet in system['planets']]
    
    VALUES = False
    TWO_VALUE_HISTOGRAM = False
    FUN_FACTS = False
    HIGHS_AND_LOWS = True
    TOP_10S = True

    
    if VALUES:
        planet_fields = ['planet_type', 'temperature', 'atmosphere', 'magnetosphere', 'water', 'biomes']
        print('----- Unique Values -----')
        for value in planet_fields: 
            print(f"Unique {value}:", get_unique_values(planets, value))


    if TWO_VALUE_HISTOGRAM:
      
        #get_attribute_combos(planets, 'magnetosphere', 'planet_type')
        get_attribute_combos(planets, 'atmosphere', 'planetary_habitation')


    if FUN_FACTS:
        terrestrial_planets = [planet for planet in planets if planet['planet_type'][0] == 'Terrestrial']
        gas_planets = [planet for planet in planets if planet['planet_type'][0] == 'Gas']
        
        print('\n----- Ranges -----')
        print("Gravity range:", get_min_max(terrestrial_planets, 'gravity'))
        print("Day length range (in hours):", get_min_max(terrestrial_planets, 'day_length'))

        print('\n----- Resource Queries -----')
        print("Planet with most inorganic resources:", planet_with_most_resources(terrestrial_planets, 'inorganic'))
        print("Planet with most organic resources:", planet_with_most_resources(terrestrial_planets, 'organic'))

        print('\n----- System Queries -----')
        print("System with most planets:", system_with_most_planets(systems))
        print("System with most gas giants:", system_with_most(systems, 'planet_type', {'Gas'}))
        print("System with least planets:", system_with_least_planets(systems))
    
    if HIGHS_AND_LOWS:

        highest_lowest_hab_score = planet_with_highest_lowest_score(planets, 'habitability_score')
        highest_lowest_org_score = planet_with_highest_lowest_score(planets, 'organic_score')
        highest_lowest_inorg_score = planet_with_highest_lowest_score(planets, 'inorganic_score')

        highest_lowest_sys_hab_score = system_with_highest_lowest_score(systems, 'habitability_score')
        highest_lowest_sys_org_score = system_with_highest_lowest_score(systems, 'organic_score')
        highest_lowest_sys_inorg_score = system_with_highest_lowest_score(systems, 'inorganic_score')

        print("----- Planet Scores -----")
        print(f"Planet with highest habitability score: {highest_lowest_hab_score[0][0]} ({highest_lowest_hab_score[0][1]})")
        print(f"Planet with lowest habitability score: {highest_lowest_hab_score[1][0]} ({highest_lowest_hab_score[1][1]})")
        print(f"Planet with highest organic score: {highest_lowest_org_score[0][0]} ({highest_lowest_org_score[0][1]})")
        print(f"Planet with lowest organic score: {highest_lowest_org_score[1][0]} ({highest_lowest_org_score[1][1]})")
        print(f"Planet with highest inorganic score: {highest_lowest_inorg_score[0][0]} ({highest_lowest_inorg_score[0][1]})")
        print(f"Planet with lowest inorganic score: {highest_lowest_inorg_score[1][0]} ({highest_lowest_inorg_score[1][1]})")

        print("\n----- System Scores -----")
        print(f"System with highest habitability score: {highest_lowest_sys_hab_score[0][0]} ({highest_lowest_sys_hab_score[0][1]})")
        print(f"System with lowest habitability score: {highest_lowest_sys_hab_score[1][0]} ({highest_lowest_sys_hab_score[1][1]})")
        print(f"System with highest organic score: {highest_lowest_sys_org_score[0][0]} ({highest_lowest_sys_org_score[0][1]})")
        print(f"System with lowest organic score: {highest_lowest_sys_org_score[1][0]} ({highest_lowest_sys_org_score[1][1]})")
        print(f"System with highest inorganic score: {highest_lowest_sys_inorg_score[0][0]} ({highest_lowest_sys_inorg_score[0][1]})")
        print(f"System with lowest inorganic score: {highest_lowest_sys_inorg_score[1][0]} ({highest_lowest_sys_inorg_score[1][1]})")

    if TOP_10S: 

        top_hab_systems = top_n_systems(systems, 'habitability_score', 10)
        top_hab_planets = top_n_planets(planets, 'habitability_score', 10)
        top_inorg_systems = top_n_systems(systems, 'inorganic_score', 10)
        top_inorg_planets = top_n_planets(planets, 'inorganic_score', 10)
        top_org_systems = top_n_systems(systems, 'organic_score', 10)
        top_org_planets = top_n_planets(planets, 'organic_score', 10)

        print("\n----- Top Habitable Systems -----")
        for i, (name, score) in enumerate(top_hab_systems, start=1):
            print(f"{i}. {name}: {score}")

        print("\n----- Top Habitable Planets -----")
        for i, (planet_name, score) in enumerate(top_hab_planets, start=1):
            print(f"{i}. {planet_name}: {score}")

        print("\n----- Top Inorganic Systems -----")
        for i, (name, score) in enumerate(top_inorg_systems, start=1):
            print(f"{i}. {name}: {score}")

        print("\n----- Top Inorganic Planets -----")
        for i, (planet_name, score) in enumerate(top_inorg_planets, start=1):
            print(f"{i}. {planet_name}: {score}")

        print("\n----- Top Organic Systems -----")
        for i, (name, score) in enumerate(top_org_systems, start=1):
            print(f"{i}. {name}: {score}")

        print("\n----- Top Organic Systems -----")
        for i, (planet_name, score) in enumerate(top_org_planets, start=1):
            print(f"{i}. {planet_name}: {score}")
    

