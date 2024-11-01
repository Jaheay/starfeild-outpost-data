from common import *
import json

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
    planet_scores = {}

    for planet in candidate_planets:

        organic_group_counts = get_grouped_organics(resources=planet['resources']['organic'], flora=planet['flora']['domesticable'], fauna=planet['fauna']['domesticable'], resource_groups=groups['organic'])

        # Gather only desired organics for scoring
        planet_flora = [resource for resource in planet['flora']['domesticable'] if resource in desired_organics]
        planet_fauna = [resource for resource in planet['flora']['domesticable'] if resource in desired_organics]
        planet_inorganics = [resource for resource in planet['resources']['inorganic'] if resource in desired_inorganics]
        
        # Score resources based on rarity, if available
        resource_score_inorganic = score_inorganic(planet_inorganics, rarity['inorganic'], full_chain=True)
        resource_score_organic = score_organics(planet_flora, planet_fauna, organic_group_counts, rarity['organic'])

        planet_scores[planet['name']] = resource_score_inorganic + resource_score_organic  
    
    return planet_scores


def find_best_systems(system_data, unique_resources, resources_by_rarity, groups):
    """
    Identifies systems with unique resources, captures full chains within those systems, and iteratively
    selects additional systems to minimize the number of outposts needed to capture all resources.
    """
    inorganic_groups = groups['inorganic']
    all_inorganic_resources = set(resources_by_rarity['inorganic'].keys())
    all_organic_resources = set(resources_by_rarity['organic'].keys())
    
    captured_inorganic_groups = set()
    captured_inorganics = set()
    captured_organics = set()
    processed_systems = set()
    final_planets = []

    # Step 1: Capture unique resource systems and any full chains within those systems
    for system in system_data:
        unique_system = False
        for planet in system['planets']:
            candidacy = planet.get('outpost_candidacy', {})

            # Check if this planet has unique resources
            if candidacy.get('unique', False):
                unique_system = True
                final_planets.append(planet)  # Add planet for outpost setup
                
                # Capture only unique inorganic resources
                # We can't assume other resources are nearby
                # Also, no unique is also a fullchain
                for resource in planet['resources'].get('inorganic', []):
                    if resource in unique_resources['inorganic']:
                        captured_inorganics.add(resource)
                
                # Capture organic resources available on the unique planets
                for resource in planet['resources'].get('organic', []):
                    if resource in unique_resources['organic']:
                        captured_organics.add(resource)
                    
                    # Check if resource is in flora or fauna domesticable resources
                    # TODO: outpost count: We only capture if the type matches the ideal type, we could capture non-ideal, and potentially lower outpost count
                    for type in groups['organic']:
                        if resource in planet.get(type, {}).get('domesticable', {}) and resource in groups['organic'][type]: 
                            captured_organics.add(resource)
        
        # If the system contains unique resources, capture full chains within it
        if unique_system:
            processed_systems.add(system['name'])  # Mark system as processed
            for planet in system['planets']:
                candidacy = planet.get('outpost_candidacy', {})
                # Skip planets that already have a unique resource to avoid duplication - it happened, Fermi-VII-a man. 
                if candidacy.get('full_resource_chain') and planet not in final_planets:
                    final_planets.append(planet)
                    for group in candidacy['full_resource_chain']:
                        captured_inorganic_groups.add(group)
                        captured_inorganics.update(groups['inorganic'][group])

                        # Check if resource is in flora or fauna domesticable resources
                        # TODO: outpost count: We only capture if the type matches the ideal type, we could capture non-ideal, and potentially lower outpost count
                        for type in groups['organic']:
                            if resource in planet.get(type, {}).get('domesticable', {}) and resource in groups['organic'][type]: 
                                captured_organics.add(resource)
       

    # Step 2: Iteratively find additional systems with uncaptured full chains
    while True:
        # Determine remaining uncaptured resources
        uncaptured_inorganic_groups = [group for group in inorganic_groups if group not in captured_inorganic_groups]
        uncaptured_inorganics = [res for res in all_inorganic_resources if res not in captured_inorganics]
        uncaptured_organics = [res for res in all_organic_resources if res not in captured_organics]
        
        if not uncaptured_inorganic_groups:
            break  # Exit if all resource groups are captured

       # Score systems based on unique uncaptured full chains
        system_scores = {}
        for system in system_data:
            if system['name'] in processed_systems:
                continue

            # Track unique uncaptured groups within the system
            unique_uncaptured_groups = set()
            for planet in system['planets']:
                candidacy = planet.get('outpost_candidacy', {})
                if candidacy.get('full_resource_chain'):
                    # Add only uncaptured groups to avoid duplicate scoring within the same system
                    unique_uncaptured_groups.update(
                        group for group in candidacy['full_resource_chain'] if group in uncaptured_inorganic_groups
                    )

            # Score based on the count of unique uncaptured groups in this system
            if unique_uncaptured_groups:
                system_scores[system['name']] = len(unique_uncaptured_groups)

        if not system_scores:
            raise Exception("No more systems with uncaptured full chains available.")


        # Identify the maximum count of uncaptured groups and select those systems
        max_score = max(system_scores.values(), default=0)
        candidate_systems = [
            system for system, score in system_scores.items() if score == max_score
        ]

        # Collect candidate planets with full chains in the top-scoring systems
        candidate_planets = []
        for system in system_data:
            if system['name'] in candidate_systems:
                for planet in system['planets']:
                    if planet.get('outpost_candidacy', {}).get('full_resource_chain'):
                        candidate_planets.append(planet)

        # Use `score_by_desired` to rank candidates based on desired organics and desired inorganics
        scored_planets = score_by_desired(
            candidate_planets,
            desired_inorganics=uncaptured_inorganics, #['Helium-3', 'Water']
            desired_organics=uncaptured_organics,
            resources_by_rarity=resources_by_rarity,
            groups=groups
        )

        # Aggregate scores by system to determine the top system
        system_aggregate_scores = {}
        for planet_name, planet_score in scored_planets.items():
            # Find the system for this planet
            planet_system = next(
                system['name'] for system in system_data
                if any(planet['name'] == planet_name for planet in system['planets'])
            )
            if planet_system in system_aggregate_scores:
                system_aggregate_scores[planet_system] += planet_score
            else:
                system_aggregate_scores[planet_system] = planet_score


        # Select the system with the highest aggregated score
        best_system_name = max(system_aggregate_scores, key=system_aggregate_scores.get)
        processed_systems.add(best_system_name)

        # Capture resources from the selected system
        for system in system_data:
            if system['name'] == best_system_name:
                for planet in system['planets']:
                    if planet.get('outpost_candidacy', {}).get('full_resource_chain'):
                        final_planets.append(planet)
                        for group in planet['outpost_candidacy']['full_resource_chain']:
                            captured_inorganic_groups.add(group)
                            captured_inorganics.update(groups['inorganic'][group])

                            # Check if resource is in flora or fauna domesticable resources
                            # TODO: outpost count: We only capture if the type matches the ideal type, we could capture non-ideal, and potentially lower outpost count
                            for type in groups['organic']:
                                if resource in planet.get(type, {}).get('domesticable', {}) and resource in groups['organic'][type]: 
                                    captured_organics.add(resource)
                break
    
    print(f"BEFORE HIGHLANDER: {len(final_planets)}")
    ## Step 3: Apply Highlander Rules - Deduplicate Planets with the Same Full Resource Chain
    # Separate list to ensure unique resource planets are always included
    unique_resource_planets = []
    # Track full chains provided by unique-resource planets
    locked_full_chains = set()

    # First, process planets with unique resources to lock their chains
    for planet in final_planets:
        # Check if this planet has a unique resource
        if planet.get('outpost_candidacy', {}).get('unique'):
            unique_resource_planets.append(planet)
            
            # If it has a full resource chain, lock it to prevent duplicates
            full_resource_chain = tuple(planet['outpost_candidacy'].get('full_resource_chain', []))
            if full_resource_chain:
                locked_full_chains.add(full_resource_chain)

    # Dictionary to track the best representative for each remaining full resource chain
    unique_full_chain_planets = {}

    # Now, process non-unique planets and only add them if their chain is unlocked
    for planet in final_planets:
        # Skip unique-resource planets, as they are already handled
        if planet.get('outpost_candidacy', {}).get('unique'):
            continue
        
        # Apply Highlander rules for non-unique planets with full chains
        full_resource_chain = tuple(planet['outpost_candidacy'].get('full_resource_chain', []))
        if not full_resource_chain or full_resource_chain in locked_full_chains:
            continue  # Skip if no chain or if the chain is already locked by a unique resource planet

        planet_organics = set()

        # Calculate unique organics on this planet
        for resource_type in groups['organic']:
            for resource in planet.get(resource_type, {}).get('domesticable', {}):
                if resource in groups['organic'][resource_type] and resource not in captured_organics:
                    planet_organics.add(resource)

        # For non-unique planets, keep only the best representative for each chain
        if full_resource_chain not in unique_full_chain_planets or len(planet_organics) > len(unique_full_chain_planets[full_resource_chain][1]):
            unique_full_chain_planets[full_resource_chain] = (planet, planet_organics)

    # Retain the final list of planets, including all unique resource planets and the best representatives for each full resource chain
    final_planets = unique_resource_planets + [planet for planet, organics in unique_full_chain_planets.values()]






    # Reset captured_inorganics and captured_organics
    captured_inorganics.clear()
    captured_organics.clear()

    # Update captured resources based on final_planets
    for planet in final_planets:
        # Capture inorganic resources
        captured_inorganics.update(planet['resources'].get('inorganic', []))
        captured_inorganics.update(groups['gatherable_only'].get('inorganic', []))

        # Capture organic resources
        captured_organics.update(planet['resources'].get('organic', []))
        captured_organics.update(groups['gatherable_only'].get('organic', []))

    # Calculate uncaptured resources
    uncaptured_inorganics = [res for res in all_inorganic_resources if res not in captured_inorganics]
    uncaptured_organics = [res for res in all_organic_resources if res not in captured_organics]

    print(f"Uncaptured Inorganics: {uncaptured_inorganics}")
    print(f"Uncaptured Organics: {uncaptured_organics}")


    print(f"AFTER HIGHLANDER: {len(final_planets)}")
    for planet in final_planets:
        full_resource_chain = planet['outpost_candidacy'].get('full_resource_chain', "")
        unique_resource = planet['outpost_candidacy'].get('unique', "")
        print(f"{planet['name']}: Reason: {full_resource_chain}{unique_resource}")

    # TODO: Thoughts. We have 22 at this point. So, only 2 more and already over our ideal budget.
    # Maybe I need to rework, to find planets that can replace full chain planets. 

    return final_planets




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
