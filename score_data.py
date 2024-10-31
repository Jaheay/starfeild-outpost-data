from common import *
import json


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
    attributes = planet['attributes']
    biomes = planet['biomes'] if planet['biomes'] else []

    # Evaluate planetary habitation
    habitation = int(attributes['planetary_habitation'])
    score += -habitation * 2  # Higher habitation score bad

    # Gravity assessment
    gravity = float(attributes['gravity'][:-1])  # Remove the 'g' and convert to float
    if gravity >= 2.0:  # High gravity
        score -= 2  # Not fun
    elif gravity > 1.0:
        score -= 1  # Personal preference
    elif gravity <= 0.5:  # Low gravity
        score += 2  # Weeeeee

    # Temperature assessment
    temperature = attributes['temperature']
    if temperature == 'Temperate':
        score += 3  # Huge bonus for temperate
    elif temperature in ['Hot', 'Cold']:
        score += 0  # Neutral score
    elif temperature in ['Frozen', 'Deep freeze']:
        score -= 2  # Very bad
    elif temperature in ['Inferno', 'Scorched']:
        score -= 3  # Extreme negative

    # Atmosphere assessment
    atmosphere = attributes['atmosphere']
    if atmosphere['density'] == 'Extreme':
        score -= 2  # Extreme densities are bad for habitabilitye
    elif atmosphere['density'] =='High':
        score -= 1 # A tad high
    elif atmosphere['type'] == 'O2':
        score += 2  # Oxygen is good for life
    elif atmosphere['type'] == 'None':
        score += 1  # Neutral, better than toxic or corrosive

    # Water safety assessment
    water_safety = attributes['water']
    if water_safety == 'Safe':
        score += 3  # Safe water is good for life
    elif water_safety in ['Radioactive', 'Chemical', 'Heavy metal']:
        score -= 3  # Bad for habitability

    # Biome assessment
    desirable_biomes = {'Tropical', 'Wetlands', 'Savanna', 'Deciduous', 'Coniferous'}
    desolate_biomes = {'Craters', 'Frozen', 'Volcanic'}
    
    desirable_biome_count = sum(1 for biome in biomes if biome in desirable_biomes)
    desolate_biome_count = sum(1 for biome in biomes if biome in desolate_biomes)
    score += desirable_biome_count * 2  # Bonus for each lush biome
    score -= desolate_biome_count * 2 # Penalty for each desolate biome

    num_biomes = len(biomes)  
    if num_biomes > 1:
        score += num_biomes/2  # More biomes generally increase habitability

    # Magnetosphere assessment
    magnetosphere = attributes['magnetosphere']
    if magnetosphere in ['Average']:
        score += 2  # Good for habitability
    elif magnetosphere in ['Strong', 'Very strong', ]:
        score += 3  # Great for habitability
    elif magnetosphere in ['Powerful']:
        score += 2  # Too strong
    elif magnetosphere in ['Very weak', 'Weak']:
        score -= 1  # Too weak
    elif magnetosphere in ['Extreme', 'Massive']:
        score -= 3  # Gas Giant Powerful, Bad
    elif magnetosphere == 'None':
        score -= 3  # Lacks protection from solar winds

    # Bonus for moons. Because moons are cool. 
    # I'd do moons of gas giants specifically, but that would take too much effort. 
    if score >= 0:
        if attributes['isMoon'] == True:
            score += 6

    return score



def score_planet(planet, rarity, groups, full_chain=False, bonus=False):
    # Skip gas giants
    if planet['attributes']['planet_type'][0] == 'Jovian':
        return {
            'habitability_score': f"{round(0, 3):.3f}",
            'organic_score': f"{round(0, 3):.3f}",
            'inorganic_score': f"{round(0, 3):.3f}"
        }

    resource_score_inorganic = 0
    resource_score_organic = 0
    biome_group_ratio = 1
    habitability_score = calculate_habitability(planet)

    resource_groups = get_grouped_resources(planet['resources']['inorganic'], groups['inorganic'], full_chain)
    
    # Don't do the biome bonus when calcualting for full chains, 
    # as full chains will always be in one biome
    if not full_chain: 
        num_biomes = len(planet['biomes'])
        inorganic_group_count = len(resource_groups)
        biome_group_ratio = inorganic_group_count / num_biomes if num_biomes else 1

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
        system_habitability_score += float(planet['scores']['habitability_score']) if float(planet['scores']['habitability_score']) > 0 else 0

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
    
    # I do it like this to keep the door open for organic groups. 
    unique = {
        category: {key: value for key, value in items.items() if value == 'Unique'}
        for category, items in rarity.items()
    }
    inorganic_groups = load_resource_groups(INORGANIC_GROUPS_PATH, unique['inorganic'])
    groups = {'inorganic': inorganic_groups}

    all_systems = load_system_data(RAW_SYSTEM_DATA_PATH)

    for system in all_systems: 
        for planet in system['planets']:
            planet['scores'] = score_planet(planet, rarity, groups)
        system['scores'] = score_system(system, rarity)

    save_system_data(SCORED_SYSTEM_DATA_PATH, all_systems)