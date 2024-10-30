from common import load_resources, load_planets, load_resource_groups
import json

def count_resource_groups(input_list, resource_groups):
    group_counts = {}
    flat_resources = {}

    for group, resources in resource_groups.items():
        if isinstance(resources, dict):
            for branch, items in resources.items():
                full_name = f"{group}-{branch.split('-')[-1]}"
                flat_resources.update({item: full_name for item in items})
                group_counts[full_name] = 0
        else:
            flat_resources.update({item: group for item in resources})
            group_counts[group] = 0

    for resource in input_list:
        if resource in flat_resources:
            group = flat_resources[resource]
            group_counts[group] = group_counts.get(group, 0) + 1

    return {group: count for group, count in group_counts.items() if count > 0}

def score_resources(resource_list, resource_dict):
    RARITY_SCORES = {'Common': 1, 'Uncommon': 2, 'Rare': 4, 'Exotic': 8, 'Unique': 16}
    score = 0
    for resource in resource_list:
        rarity = resource_dict.get(resource, 'Common')
        score += RARITY_SCORES.get(rarity, 1)  # Default to common score if unknown
    return score

def score_planet(planet, inorganic_dict, organic_dict):
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

    # Final resource score for planet
    planet_resource_score = resource_score_inorganic + resource_score_organic

    return {
        'habitability_score': f"{round(habitability_score, 3):.3f}",
        'resource_score': f"{round(planet_resource_score, 3):.3f}",
        'organic_score': f"{round(resource_score_organic, 3):.3f}",
        'inorganic_score': f"{round(resource_score_inorganic, 3):.3f}"
    }


def score_system(system, inorganic_dict, organic_dict):
    all_inorganic_resources = set()
    all_organic_resources = set()


    for planet in system['planets']:
        # Calculate scores for each planet
        planet_scores = score_planet(planet, inorganic_dict, organic_dict)
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

if __name__ == '__main__':
    inorganic_dict = load_resources('data/inorganic.csv', shortname=False)
    inorganic_groups = load_resource_groups('data/inorganic_groups.json')
    organic_dict = load_resources('data/organic.csv', shortname=False)
    systems = load_planets('data/2_clean_systems_data.json')

    for system in systems:
        # For each system, calculate resource groups and scores
        for planet in system['planets']:
            inorganic_resource_groups = count_resource_groups(planet['resources']['inorganic'], inorganic_groups)
            planet['resource_groups'] = {'inorganic': inorganic_resource_groups}

        for planet in system['planets']:
            scores = score_planet(planet, inorganic_dict, organic_dict)
            planet['scores'] = scores

        system_scores = score_system(system, inorganic_dict, organic_dict)
        system['scores'] = system_scores

    # Save the modified systems data with scores embedded
    with open('data/3_scored_systems_data.json', 'w') as f:
        json.dump(systems, f, indent=4)
