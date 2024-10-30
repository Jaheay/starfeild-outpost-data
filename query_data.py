import json
import csv
from common import *

def get_unique_values(planets, parameter):
    """Return all unique values for a given parameter across all planets."""
    unique_values = set()
    
    for planet in planets:
        if parameter == 'planet_type':
            unique_values.add(planet[parameter][1])  # Add subtype only
        elif parameter == 'atmosphere':
            atmosphere = planet.get('atmosphere')
            if atmosphere:
                unique_values.add(f"{atmosphere['density']} {atmosphere['type']}")
        else:
            if parameter in planet:
                unique_values.add(planet[parameter])
                
    return unique_values

def get_min_max(planets, parameter):
    """Return the planet name with the min and max values for a numerical parameter like gravity or day_length."""
    min_value, max_value = float('inf'), float('-inf')
    min_planet, max_planet = None, None

    for planet in planets:
        if parameter in planet:
            value = planet[parameter]
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
                    if parameter == 'planet_type' and planet[parameter][0] in values)
        
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
    systems = load_planets('data/3_scored_systems_data.json')
    planets = [planet for system in systems for planet in system['planets']]
    
    VALUES = False
    FUN_FACTS = False
    HIGHS_AND_LOWS = False
    TOP_10S = False

    
    if VALUES:
        planet_fields = ['planet_type', 'temperature', 'atmosphere', 'magnetosphere', 'water']
        print('----- Unique Values -----')
        for value in planet_fields: 
            print(f"Unique {value}:", get_unique_values(planets, value))

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

        highest_lowest_res_score = planet_with_highest_lowest_score(planets, 'resource_score')
        highest_lowest_sys_res_score = system_with_highest_lowest_score(systems, 'resource_score')
        highest_lowest_sys_org_score = system_with_highest_lowest_score(systems, 'organic_score')
        highest_lowest_sys_inorg_score = system_with_highest_lowest_score(systems, 'inorganic_score')

        print("----- Planet Scores -----")
        print(f"Planet with highest resource score: {highest_lowest_res_score[0][0]} ({highest_lowest_res_score[0][1]})")
        print(f"Planet with lowest resource score: {highest_lowest_res_score[1][0]} ({highest_lowest_res_score[1][1]})")

        print("\n----- System Scores -----")
        print(f"System with highest resource score: {highest_lowest_sys_res_score[0][0]} ({highest_lowest_sys_res_score[0][1]})")
        print(f"System with lowest resource score: {highest_lowest_sys_res_score[1][0]} ({highest_lowest_sys_res_score[1][1]})")
        print(f"System with highest organic score: {highest_lowest_sys_org_score[0][0]} ({highest_lowest_sys_org_score[0][1]})")
        print(f"System with lowest organic score: {highest_lowest_sys_org_score[1][0]} ({highest_lowest_sys_org_score[1][1]})")
        print(f"System with highest inorganic score: {highest_lowest_sys_org_score[0][0]} ({highest_lowest_sys_inorg_score[0][1]})")
        print(f"System with lowest inorganic score: {highest_lowest_sys_org_score[1][0]} ({highest_lowest_sys_inorg_score[1][1]})")

    if TOP_10S: 

        top_systems = top_n_systems(systems, 'resource_score', 10)
        top_planets = top_n_planets(planets, 'resource_score', 10)
        top_inorg_systems = top_n_systems(systems, 'inorganic_score', 10)
        top_inorg_planets = top_n_planets(planets, 'inorganic_score', 10)
        top_org_systems = top_n_systems(systems, 'organic_score', 10)
        top_org_planets = top_n_planets(planets, 'organic_score', 10)

        print("\n----- Top Systems -----")
        for i, (name, score) in enumerate(top_systems, start=1):
            print(f"{i}. {name}: {score}")

        print("\n----- Top Planets -----")
        for i, (planet_name, score) in enumerate(top_planets, start=1):
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
    

