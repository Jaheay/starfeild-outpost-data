# Local Imports
from config import *
from common import get_grouped_inorganics, get_grouped_organics, score_inorganic, score_organics, load_resource_groups, load_resources, load_system_data

def find_fullchain_planets(system_data, inorganic_groups):

    for system in system_data:
        for planet in system['planets']:
            grouped_resources = get_grouped_inorganics(planet['resources']['inorganic'], inorganic_groups, full_chain=True)
            
            # Determine if full resource chain exists
            full_chain = any(is_complete for is_complete in grouped_resources.values())
            if full_chain:
                planet.setdefault('outpost_candidacy', {})
                planet['outpost_candidacy']['full_resource_chain'] = list(grouped_resources.keys())

def find_unique_resources(system_data, unique_resources):

    for system in system_data:
        for planet in system['planets']:
            unique_resources_found = []

            # Check each resource type in unique_resources
            for resource_type in unique_resources:
                unique_resources_found.extend(
                    resource for resource in planet['resources'].get(resource_type, [])
                    if resource in unique_resources[resource_type]
                )
            
            # If any unique resources are found, update outpost_candidacy
            if unique_resources_found:
                planet.setdefault('outpost_candidacy', {})
                planet['outpost_candidacy']['unique'] = unique_resources_found




def score_by_desired(candidate_planets, groups, desired_inorganics=[], desired_organics=[], resources_by_rarity=None):
    """
    A scoring function that only scores based on desired resources. 
    It loses some of the complexity of the proper scores, but not meaningfully so for its purpose. 
    """
    planet_scores = {}

    for planet in candidate_planets:
        resource_score_organic = 0
        resource_score_inorganic = 0
        

        # Gather only desired organics for scoring
        if len(desired_organics) > 0:
            organic_group_counts = get_grouped_organics(resources=planet['resources']['organic'], flora=planet['flora']['domesticable'], fauna=planet['fauna']['domesticable'], resource_groups=groups['organic'])
            planet_flora = [resource for resource in planet['flora']['domesticable'] if resource in desired_organics]
            planet_fauna = [resource for resource in planet['flora']['domesticable'] if resource in desired_organics]
            resource_score_organic = score_organics(planet_flora, planet_fauna, organic_group_counts, rarity['organic'])
        if len(desired_inorganics) > 0:
            planet_inorganics = [resource for resource in planet['resources']['inorganic'] if resource in desired_inorganics]
            resource_score_inorganic = score_inorganic(planet_inorganics, rarity['inorganic'], full_chain=True)
        
        
        planet_scores[planet['name']] = resource_score_inorganic + resource_score_organic  
    
    return planet_scores

def score_systems_by_full_chains(system_data, uncaptured_inorganic_groups, processed_systems):
    """
    Scores systems based on the number of uncaptured full resource chains they contain.
    Returns a dictionary of system names and their scores.
    """
    system_scores = {}
    for system in system_data:
        if system['name'] in processed_systems:
            continue

        unique_uncaptured_groups = set()
        for planet in system['planets']:
            candidacy = planet.get('outpost_candidacy', {})
            if candidacy.get('full_resource_chain'):
                unique_uncaptured_groups.update(
                    group for group in candidacy['full_resource_chain'] if group in uncaptured_inorganic_groups
                )

        if unique_uncaptured_groups:
            system_scores[system['name']] = len(unique_uncaptured_groups)

    return system_scores

def collect_candidate_planets(system_data, candidate_systems):
    """
    Collects candidate planets with full resource chains from the top-scoring systems.
    Returns a list of candidate planets.
    """
    candidate_planets = []
    for system in system_data:
        if system['name'] in candidate_systems:
            for planet in system['planets']:
                if planet.get('outpost_candidacy', {}).get('full_resource_chain'):
                    candidate_planets.append(planet)
    return candidate_planets


def capture_unique_resource_systems(system_data, unique_resources, groups):
    """
    Captures systems with unique resources and any full chains within those systems.
    Returns the list of planets and the captured resources.
    """
    captured_inorganics = set()
    captured_organics = set()
    captured_inorganic_groups = set()
    processed_systems = set()
    final_planets = []

    for system in system_data:
        unique_system = False
        for planet in system['planets']:
            candidacy = planet.get('outpost_candidacy', {})

            # Check if this planet has unique resources
            if candidacy.get('unique', False):
                unique_system = True
                final_planets.append(planet)  # Add planet for outpost setup

                # Capture only unique inorganic resources
                for resource in planet['resources'].get('inorganic', []):
                    if resource in unique_resources['inorganic']:
                        captured_inorganics.add(resource)

                # Capture organic resources available on the unique planets
                for resource in planet['resources'].get('organic', []):
                    if resource in unique_resources['organic']:
                        captured_organics.add(resource)

        # If the system contains unique resources, capture full chains within it
        if unique_system:
            processed_systems.add(system['name'])  # Mark system as processed
            for planet in system['planets']:
                candidacy = planet.get('outpost_candidacy', {})
                # Skip planets already in final_planets to avoid duplicates
                if candidacy.get('full_resource_chain') and planet not in final_planets:
                    final_planets.append(planet)
                    for group in candidacy['full_resource_chain']:
                        captured_inorganic_groups.add(group)
                        captured_inorganics.update(groups['inorganic'][group])

    captured_resources = {
        'inorganics': captured_inorganics,
        'organics': captured_organics,
        'inorganic_groups': captured_inorganic_groups,
    }

    return final_planets, processed_systems, captured_resources


def capture_full_chain_systems(system_data, processed_systems, final_planets, captured_resources, resources_by_rarity, groups):
    """
    Iteratively selects additional systems to minimize the number of outposts needed to capture all resources.
    Returns the updated list of final planets and captured resources.
    """
    inorganic_groups = groups['inorganic']
    all_inorganic_resources = set(resources_by_rarity['inorganic'].keys())
    all_organic_resources = set(resources_by_rarity['organic'].keys())

    captured_inorganics = captured_resources['inorganics']
    captured_organics = captured_resources['organics']
    captured_inorganic_groups = captured_resources['inorganic_groups']

    while True:
        # Determine remaining uncaptured resources
        uncaptured_inorganic_groups = [
            group for group in inorganic_groups if group not in captured_inorganic_groups
        ]
        uncaptured_inorganics = [
            res for res in all_inorganic_resources if res not in captured_inorganics
        ]
        uncaptured_organics = [
            res for res in all_organic_resources if res not in captured_organics
        ]

        if not uncaptured_inorganic_groups:
            break  # Exit if all resource groups are captured

        # Score systems based on the count of uncaptured full chains
        system_scores = score_systems_by_full_chains(
            system_data, uncaptured_inorganic_groups, processed_systems
        )

        if not system_scores:
            raise Exception("No more systems with uncaptured full chains available.")

        # Identify the maximum count of uncaptured groups and select those systems
        max_score = max(system_scores.values(), default=0)
        candidate_systems = [
            system for system, score in system_scores.items() if score == max_score
        ]

        # Collect candidate planets with full chains in the top-scoring systems
        candidate_planets = collect_candidate_planets(system_data, candidate_systems)

        # Use `score_by_desired` to rank candidates based on desired organics and desired inorganics
        scored_planets = score_by_desired(
            candidate_planets,
            desired_inorganics=uncaptured_inorganics,
            desired_organics=uncaptured_organics,
            resources_by_rarity=resources_by_rarity,
            groups=groups
        )

        # Select the best planet(s)
        best_planet_name = max(scored_planets, key=scored_planets.get)

        # Find the system name for the best planet
        best_system_name = next(
            system['name'] for system in system_data
            if any(planet['name'] == best_planet_name for planet in system['planets'])
        )
        processed_systems.add(best_system_name)

        # Capture resources from the selected system
        for system in system_data:
            if system['name'] == best_system_name:
                for planet in system['planets']:
                    if planet.get('outpost_candidacy', {}).get('full_resource_chain'):
                        if planet not in final_planets:
                            final_planets.append(planet)
                        for group in planet['outpost_candidacy']['full_resource_chain']:
                            captured_inorganic_groups.add(group)
                            captured_inorganics.update(groups['inorganic'][group])
                break

    # Update captured resources
    captured_resources.update({
        'inorganics': captured_inorganics,
        'organics': captured_organics,
        'inorganic_groups': captured_inorganic_groups,
    })

    return final_planets, processed_systems, captured_resources


def capture_full_chain_systems(system_data, processed_systems, final_planets, captured_resources, resources_by_rarity, groups):
    """
    Iteratively selects additional systems to minimize the number of outposts needed to capture all resources.
    Returns the updated list of final planets and captured resources.
    """
    inorganic_groups = groups['inorganic']
    all_inorganic_resources = set(resources_by_rarity['inorganic'].keys())
    all_organic_resources = set(resources_by_rarity['organic'].keys())

    captured_inorganics = captured_resources['inorganics']
    captured_organics = captured_resources['organics']
    captured_inorganic_groups = captured_resources['inorganic_groups']

    while True:
        # Determine remaining uncaptured resources
        uncaptured_inorganic_groups = [
            group for group in inorganic_groups if group not in captured_inorganic_groups
        ]
        uncaptured_inorganics = [
            res for res in all_inorganic_resources if res not in captured_inorganics
        ]
        uncaptured_organics = [
            res for res in all_organic_resources if res not in captured_organics
        ]

        if not uncaptured_inorganic_groups:
            break  # Exit if all resource groups are captured

        # Score systems based on the count of uncaptured full chains
        system_scores = score_systems_by_full_chains(
            system_data, uncaptured_inorganic_groups, processed_systems
        )

        if not system_scores:
            raise Exception("No more systems with uncaptured full chains available.")

        # Identify the maximum count of uncaptured groups and select those systems
        max_score = max(system_scores.values(), default=0)
        candidate_systems = [
            system for system, score in system_scores.items() if score == max_score
        ]

        # Collect candidate planets with full chains in the top-scoring systems
        candidate_planets = collect_candidate_planets(system_data, candidate_systems)

        # Use `score_by_desired` to rank candidates based on desired organics and desired inorganics
        scored_planets = score_by_desired(
            candidate_planets,
            desired_inorganics=uncaptured_inorganics,
            desired_organics=uncaptured_organics,
            resources_by_rarity=resources_by_rarity,
            groups=groups
        )

        # Select the best planet(s)
        best_planet_name = max(scored_planets, key=scored_planets.get)

        # Find the system name for the best planet
        best_system_name = next(
            system['name'] for system in system_data
            if any(planet['name'] == best_planet_name for planet in system['planets'])
        )
        processed_systems.add(best_system_name)

        # Capture resources from the selected system
        for system in system_data:
            if system['name'] == best_system_name:
                for planet in system['planets']:
                    if planet.get('outpost_candidacy', {}).get('full_resource_chain'):
                        if planet not in final_planets:
                            final_planets.append(planet)
                        for group in planet['outpost_candidacy']['full_resource_chain']:
                            captured_inorganic_groups.add(group)
                            captured_inorganics.update(groups['inorganic'][group])
                break

    # Update captured resources
    captured_resources.update({
        'inorganics': captured_inorganics,
        'organics': captured_organics,
        'inorganic_groups': captured_inorganic_groups,
    })

    return final_planets, processed_systems, captured_resources

def apply_highlander_rules(final_planets, captured_resources, resources_by_rarity, groups):
    """
    Applies the Highlander rules to eliminate duplicate resource chains,
    favoring unique resource planets.
    Returns the updated list of final planets.
    """
    unique_resource_planets = []
    locked_full_chains = set()

    # First, process planets with unique resources to lock their chains
    for planet in final_planets:
        if planet.get('outpost_candidacy', {}).get('unique'):
            unique_resource_planets.append(planet)
            full_resource_chain = tuple(planet['outpost_candidacy'].get('full_resource_chain', []))
            if full_resource_chain:
                locked_full_chains.add(full_resource_chain)

    # Dictionary to track the best representative for each remaining full resource chain
    unique_full_chain_planets = {}

    # Now, process non-unique planets and only add them if their chain is unlocked
    for planet in final_planets:
        if planet.get('outpost_candidacy', {}).get('unique'):
            continue

        full_resource_chain = tuple(planet['outpost_candidacy'].get('full_resource_chain', []))
        if not full_resource_chain or full_resource_chain in locked_full_chains:
            continue

        # Collect planets by resource chain for scoring
        if full_resource_chain not in unique_full_chain_planets:
            unique_full_chain_planets[full_resource_chain] = []
        unique_full_chain_planets[full_resource_chain].append(planet)

    # Determine the best planet for each full resource chain
    best_planets = []
    for chain, candidates in unique_full_chain_planets.items():
        # Score candidate planets for this chain
        uncaptured_organics = [
            res for res in resources_by_rarity['organic'] if res not in captured_resources['organics']
        ]

        scored_planets = score_by_desired(
            candidates,
            groups=groups,
            desired_inorganics=[], # We only care about organics here
            desired_organics=uncaptured_organics,
            resources_by_rarity=resources_by_rarity
        )

        # Find the planet with the highest score
        best_planet_name = max(scored_planets, key=scored_planets.get)
        best_planet = next(planet for planet in candidates if planet['name'] == best_planet_name)
        best_planets.append(best_planet)

    # Retain the final list of planets
    final_planets = unique_resource_planets + best_planets

    return final_planets

def recalculate_captured_resources(final_planets, groups):
    """
    Recalculates captured inorganic and organic resources based on the final list of planets.
    Returns inorganics and organics sets.
    """
    captured_inorganics = set()
    captured_organics = set()

    for planet in final_planets:
        # Capture inorganic resources
        captured_inorganics.update(planet['resources'].get('inorganic', []))
        # Capture organic resources
        captured_organics.update(planet['resources'].get('organic', []))

    captured_resources = {
        'inorganics': captured_inorganics,
        'organics': captured_organics,
    }
    return captured_resources



def calculate_uncaptured_resources(captured_resources, resources_by_rarity, gatherable_only):
    """
    Calculates uncaptured inorganic and organic resources.
    Returns uncaptured_inorganics and uncaptured_organics.
    """
    all_inorganic_resources = set(resources_by_rarity['inorganic'].keys())
    all_organic_resources = set(resources_by_rarity['organic'].keys())

    uncaptured_inorganics = all_inorganic_resources - captured_resources['inorganics'] - set(gatherable_only['inorganic'])
    uncaptured_organics = all_organic_resources - captured_resources['organics'] - set(gatherable_only['organic'])

    uncaptured_resources = {
        'inorganics': uncaptured_inorganics,
        'organics': uncaptured_organics,
    }

    return uncaptured_resources




def find_best_systems(system_data, unique_resources, resources_by_rarity, groups):
    """
    Identifies the best systems for outpost setup based on unique resources and full resource chains.
    Returns the final list of planets for outpost placement.
    """
    # Step 1: Capture unique resource systems
    final_planets, processed_systems, captured_resources = capture_unique_resource_systems(
        system_data, unique_resources, groups
    )

    # Step 2: Iteratively find additional systems with uncaptured full chains
    #final_planets, processed_systems, captured_resources = capture_full_chain_systems(
    #    system_data, processed_systems, final_planets, captured_resources, resources_by_rarity, groups
    #)

    final_planets, processed_systems, captured_resources = capture_full_chain_systems(
        system_data, processed_systems, final_planets, captured_resources, resources_by_rarity, groups
    )

    # Step 3: Apply Highlander Rules
    final_planets = apply_highlander_rules(
        final_planets, captured_resources, resources_by_rarity, groups
    )

    # Recalculate captured resources based on final_planets after Highlander Rules
    captured_resources = recalculate_captured_resources(final_planets, groups)
    uncaptured_resources = calculate_uncaptured_resources(captured_resources, resources_by_rarity, groups['gatherable_only'])

    # Print final results
    print_final_results(final_planets, uncaptured_resources)

    return final_planets





def print_final_results(final_planets, uncaptured_resources):
    """
    Prints the final planets, the count of final planets, and uncaptured resources.
    """
    print(f"\nFinal Planets ({len(final_planets)}):")
    for planet in final_planets:
        full_resource_chain = planet.get('outpost_candidacy', {}).get('full_resource_chain', "")
        unique_resource = planet.get('outpost_candidacy', {}).get('unique', "")
        if full_resource_chain and unique_resource:
            print(f"{planet['name']}: Reason: Full Chain: {full_resource_chain}, Unique Resource: {unique_resource}")
        elif full_resource_chain: 
            print(f"{planet['name']}: Reason: Full Chain: {full_resource_chain}")
        elif unique_resource:
            print(f"{planet['name']}: Reason: Unique Resource: {unique_resource}")

    print("\nUncaptured Inorganics:")
    print(sorted(uncaptured_resources['inorganics']))

    print("\nUncaptured Organics:")
    print(sorted(uncaptured_resources['organics']))




if __name__ == '__main__':
    inorganic_rarity = load_resources(INORGANIC_DATA_PATH, shortname=False)
    organic_rarity = load_resources(ORGANIC_DATA_PATH, shortname=False)
    gatherable_only = load_resource_groups(GATHERABLE_ONLY_PATH) 
    
    rarity = { 'inorganic': inorganic_rarity, 'organic': organic_rarity}
    
    unique = {
        category: {key: value for key, value in items.items() 
        if value == 'Unique' and key not in gatherable_only[category]}
        for category, items in rarity.items()
    }

    inorganic_groups = load_resource_groups(INORGANIC_GROUPS_PATH, unique['inorganic'])
    organic_groups = load_resource_groups(ORGANIC_GROUPS_PATH, unique['inorganic'])
    groups = {'inorganic': inorganic_groups, 'organic': organic_groups, 'gatherable_only': gatherable_only}

    all_systems = load_system_data(SCORED_SYSTEM_DATA_PATH)

    fullchain_inorganic_planets = find_fullchain_planets(all_systems, groups['inorganic'])
    unique_resource_planets = find_unique_resources(all_systems, unique)
    selected_systems = find_best_systems(all_systems, unique, rarity, groups)
