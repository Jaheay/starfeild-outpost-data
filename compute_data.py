from common import *
import json


def get_grouped_resources(resources, resource_groups, full_chain=False):
    group_counts = {}
    flat_resources = {}

    # Flatten and map resources
    for group, group_resources in resource_groups.items():
        for item in group_resources:
            flat_resources[item] = group
        group_counts[group] = False if full_chain else 0  # Initialize based on `full_chain`

    if full_chain:
        # Set to True if a complete group is found
        for group_name, required_resources in resource_groups.items():
            if all(item in resources for item in required_resources):
                group_counts[group_name] = True
    else:
        # Count individual resource occurrences
        for resource in resources:
            if resource in flat_resources:
                group = flat_resources[resource]
                group_counts[group] += 1

    return {group: count for group, count in group_counts.items() if count}

"""
def score_resources(planet, inorganic_dict, organic_dict):
    habitability_score = int(planet['planetary_habitation'])  # Placeholder for habitability
    resource_score_inorganic = 0
    resource_score_organic = 0

    # Use the length of existing inorganic resource groups
    inorganic_group_count = len(planet['resource_groups']['inorganic']) \
                            + int('Helium-3' in planet['resources']['inorganic']) \
                            + int('Water' in planet['resources']['inorganic'])
    
    num_biomes = len(planet['biomes'])
    biome_resource_ratio = inorganic_group_count / num_biomes if num_biomes else 1

    # Inorganic resource score calculation
    resource_score_inorganic = score_resources(planet['resources']['inorganic'], inorganic_dict) * biome_resource_ratio

    # Organic resource score calculation, checking if organic resources are available
    if planet['water'] != 'None':
        resource_score_organic = score_resources(planet['resources']['organic'], organic_dict)


    return {
        'habitability_score': f"{round(habitability_score, 3):.3f}",
        'organic_score': f"{round(resource_score_organic, 3):.3f}",
        'inorganic_score': f"{round(resource_score_inorganic, 3):.3f}"
    }


def score_system(system, inorganic_dict, organic_dict):
    all_inorganic_resources = set()
    all_organic_resources = set()


    for planet in system['planets']:
        # Calculate scores for each planet
        planet_scores = score_resources(planet['resources'], inorganic_dict, organic_dict)
        planet['scores'] = planet_scores  # Append scores to the planet

        # Merge resources into sets for system score
        all_inorganic_resources.update(planet['resources']['inorganic'])
        all_organic_resources.update(planet['resources']['organic'])

    # Calculate system-level scores based on planets
    system_inorganic_score = score_resources(list(all_inorganic_resources), inorganic_dict) + (int('Helium-3' in planet['resources']['inorganic'])*10)
    system_organic_score = score_resources(list(all_organic_resources), organic_dict)

    return {
        'resource_score': f"{round(system_organic_score + system_inorganic_score, 3):.3f}",
        'organic_score': f"{round(system_organic_score, 3):.3f}",
        'inorganic_score': f"{round(system_inorganic_score, 3):.3f}"
    }
"""

def score_bonus(resources):
    bonus = 0
    if any(item in resources for item in GATHERABLE_INORGANIC):
        bonus += 12
    if 'Helium-3' in resources: 
        bonus += 14  # On top of +2 for being uncommon
    if 'Water' in resources:
        bonus += 5  # On top of +1 for being common

    return bonus

def calculate_habitability(planet):
    """
    Calculates the habitability score of a planet based on its attributes.
    """
    score = 0
    
    # Evaluate planetary habitation
    habitation = int(planet['planetary_habitation'])
    score += -habitation * 2  # Higher habitation score bad

    # Gravity assessment
    gravity = float(planet['gravity'][:-1])  # Remove the 'g' and convert to float
    if gravity >= 2.0:  # High gravity
        score -= 3  # Not fun
    elif gravity > 1.0:
        score -= 1  # Personal preference
    elif gravity <= 0.5:  # Low gravity
        score += 3  # Weeeeee

    # Temperature assessment
    temperature = planet['temperature']
    if temperature == 'Temperate':
        score += 4  # Huge bonus for temperate
    elif temperature in ['Hot', 'Cold']:
        score += 0  # Neutral score
    elif temperature in ['Frozen', 'Deep freeze']:
        score -= 3  # Very bad
    elif temperature in ['Inferno', 'Scorched']:
        score -= 6  # Extreme negative

    # Atmosphere assessment
    atmosphere = planet['atmosphere']
    if atmosphere['density'] in ['Extreme', 'High']:
        score -= 2  # Extreme densities are bad for habitability
    elif atmosphere['type'] == 'O2':
        score += 2  # Oxygen is good for life
    elif atmosphere['type'] == 'None':
        score += 1  # Neutral, better than toxic or corrosive

    # Water safety assessment
    water_safety = planet['water']
    if water_safety == 'Safe':
        score += 2  # Safe water is good for life
    elif water_safety in ['Radioactive', 'Chemical', 'Heavy metal']:
        score -= 3  # Bad for habitability

    # Biome assessment
    lush_biomes = {'Tropical', 'Wetlands', 'Savanna', 'Deciduous', 'Coniferous'}
    num_biomes = len(planet['biomes'])  
    
    # Give bonus for lush biomes
    lush_biome_count = sum(1 for biome in planet['biomes'] if biome in lush_biomes)
    score += lush_biome_count * 2  # Bonus for each lush biome
    
    # Add to score for biome diversity
    if num_biomes > 1:
        score += num_biomes  # More biomes generally increase habitability

    # Magnetosphere assessment
    magnetosphere = planet['magnetosphere']
    if magnetosphere in ['Extreme', 'Massive']:
        score -= 3  # Bad for habitability
    elif magnetosphere in ['Weak', 'Average']:
        score += 1  # Neutral to slightly positive
    elif magnetosphere in ['Powerful', 'Strong', 'Very strong']:
        score += 2  # Good for habitability
    elif magnetosphere == 'None':
        score -= 1  # Lacks protection from solar winds

    return score



def score_planet(planet, rarity, groups, full_chain=False, bonus=False):
    habitability_score = calculate_habitability(planet)
    resource_score_inorganic = 0
    resource_score_organic = 0
    biome_group_ratio = 1

    resource_groups = get_grouped_resources(planet['resources']['inorganic'], groups['inorganic'], full_chain)
    
    # Don't do the biome bonus when calcualting for full chains, 
    # as full chains will always be in one biome
    if not full_chain: 
        num_biomes = len(planet['biomes'])
        inorganic_group_count = len(resource_groups)
        biome_group_ratio = inorganic_group_count / num_biomes

    # Inorganic resource score calculation
    resource_score_inorganic = score_resources(planet['resources']['inorganic'], rarity['inorganic']) * biome_group_ratio
    resource_score_inorganic += score_bonus(planet['resources']['inorganic'])

    # Organic resource score calculation, checking if organic resources are available
    if 'Water' in planet['resources']['inorganic']:
        resource_score_organic = score_resources(planet['resources']['organic'], rarity['organic'])

    

    return {
        'habitability_score': f"{round(habitability_score, 3):.3f}",
        'organic_score': f"{round(resource_score_organic, 3):.3f}",
        'inorganic_score': f"{round(resource_score_inorganic, 3):.3f}"
    }

def score_system(system, rarity):
    all_inorganic_resources = set()
    all_organic_resources = set()
    system_habitability_score = 0

    # Merge resources into sets for system score
    for planet in system['planets']:
        all_inorganic_resources.update(planet['resources']['inorganic'])
        all_organic_resources.update(planet['resources']['organic'])
        system_habitability_score += calculate_habitability(planet)

    # Calculate system-level scores based on planets
    system_inorganic_score = score_resources(list(all_inorganic_resources), rarity['inorganic'])
    system_organic_score = score_resources(list(all_organic_resources), rarity['organic'])

    return {
        'habitability_score': f"{round(system_habitability_score, 3):.3f}",
        'organic_score': f"{round(system_organic_score, 3):.3f}",
        'inorganic_score': f"{round(system_inorganic_score, 3):.3f}"
    }



if __name__ == '__main__':
    inorganic_rarity = load_resources(INORGANIC_DATA_PATH, shortname=False)
    organic_rarity = load_resources(ORGANIC_DATA_PATH, shortname=False)
    rarity = { 'inorganic': inorganic_rarity, 'organic': organic_rarity}
    unique = {
        category: {key: value for key, value in items.items() if value == 'Unique'}
        for category, items in rarity.items()
    }
    
    exit
    inorganic_groups = load_resource_groups(INORGANIC_GROUPS_PATH, unique['inorganic'])
    groups = {'inorganic': inorganic_groups}

    all_systems = load_system_data(RAW_SYSTEM_DATA_PATH)

    """
    for system in systems:
        # For each system, calculate resource groups and scores
        for planet in system['planets']:
            inorganic_resource_groups = get_inorganic_groups(planet['resources']['inorganic'], inorganic_groups)
            planet['resource_groups'] = {'inorganic': inorganic_resource_groups}

        for planet in system['planets']:
            scores = score_planet(planet, inorganic_rarity, organic_rarity)
            planet['scores'] = scores

        system_scores = score_system(system, inorganic_rarity, organic_rarity)
        system['scores'] = system_scores
    """

    for system in all_systems: 
        for planet in system['planets']:
            planet['scores'] = score_planet(planet, rarity, groups)
        system['scores'] = score_system(system, rarity, groups)

    save_system_data(SCORED_SYSTEM_DATA_PATH)