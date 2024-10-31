from common import *
import json

def get_base_info(system, planet):
    """Extracts base information for a given planet within a system."""
    planet_scores = planet['scores']
    return {
        'system': system['name'],
        'planet': planet['name'],
        'inorganic_score': float(planet_scores['inorganic_score']),
        'organic_score': float(planet_scores['organic_score']),
        'habitability_score': float(planet_scores['habitability_score'])
    }

def get_unique_resources(planet_resources, unique_resources):
    """Get unique resources present on the planet."""
    unique_res = [resource for resource in planet_resources if resource in unique_resources]
    return unique_res

def find_fullchain_planets(system_data, inorganic_groups):
    fullchain_planets = []

    # Loop through systems and planets to check resources
    for system in system_data:
        for planet in system.get('planets', []):
            base_info = get_base_info(system, planet)  # Retrieve base info

            # Check for complete groups using get_grouped_resources with full_chain=True
            grouped_resources = get_grouped_resources(planet['resources']['inorganic'], inorganic_groups, full_chain=True)
            for group_name, is_complete in grouped_resources.items():
                if is_complete:
                    group_info = base_info.copy()
                    group_info['resource'] = group_name
                    fullchain_planets.append(group_info)

    # Sort by inorganic score in descending order
    fullchain_planets.sort(key=lambda x: x['inorganic_score'], reverse=True)

    return fullchain_planets

def find_unique_resources(system_data, unique_resources):
    unique_planets = []

    # Loop through systems and planets to check unique resources
    for system in system_data:
        for planet in system.get('planets', []):
            base_info = get_base_info(system, planet)  # Retrieve base info

            # Check for unique resources
            for type in unique_resources:
                found_unique_resources = get_unique_resources(planet['resources'][type], unique_resources[type])
                for unique_resource in found_unique_resources:
                    unique_info = base_info.copy()
                    unique_info['resource'] = unique_resource
                    unique_planets.append(unique_info)

    return unique_planets


def score_by_desired(candidate_systems, all_systems, desired_inorganics=[], desired_organics=[], resources_by_rarity=None):
    desire_scores = {}
    
    for system in candidate_systems:
        desired_score = 0
        for system_data in all_systems:
            if system_data['name'] == system:
                for planet in system_data.get('planets', []):
                    # Gather uncaptured individual resources for scoring
                    planet_inorganics = [resource for resource in planet['resources']['inorganic'] if resource in desired_inorganics]
                    planet_organics = [resource for resource in planet['resources']['organic'] if resource in desired_organics]

                    # Score the uncaptured resources and sum
                    if resources_by_rarity: 
                        desired_score += score_resources(planet_inorganics, resources_by_rarity['inorganic'])
                        desired_score += score_resources(planet_organics, resources_by_rarity['organic'])
                    else: 
                        desired_score += len(planet_inorganics) + len(planet_organics)

        desire_scores[system] = desired_score

    # Sort candidate systems by their tie-break score
    sorted_systems = sorted(
        desire_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_systems


def score_by_desired(candidate_planets, all_systems, desired_inorganics=[], desired_organics=[], resources_by_rarity=None):
    planet_scores = {}

    for planet in candidate_planets:
        planet_score = 0
        for system_data in all_systems:
            for system_planet in system_data.get('planets', []):
                if system_planet['name'] == planet['planet']:
                    # Gather only desired organics for scoring
                    planet_organics = [resource for resource in system_planet['resources']['organic'] if resource in desired_organics]
                    
                    # Score resources based on rarity, if available
                    if resources_by_rarity:
                        planet_score += score_resources(planet_organics, resources_by_rarity['organic'])
                    else:
                        planet_score += len(planet_organics)

        planet_scores[planet['planet']] = planet_score

    # Aggregate scores by system
    system_scores = {}
    for planet, score in planet_scores.items():
        system = next(sys for sys in candidate_planets if sys['planet'] == planet)['system']
        if system not in system_scores:
            system_scores[system] = 0
        system_scores[system] += score

    # Sort systems by tie-breaking score
    sorted_systems = sorted(
        system_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_systems





def find_best_systems(all_systems, fullchain_inorganic_planets, unique_resource_planets, resources_by_rarity, groups):
    
    ### Part 1: Start with Unique Resources, and capture any inorganic fullchains in system. 
    ### Then, capture organics on fullchain planets and unique planets)
    final_planets = []
    unique_resource_systems = []
    inorganic_groups = groups['inorganic']
    inorganic_resources = set(resources_by_rarity['inorganic'].keys())
    organic_resources = set(resources_by_rarity['organic'].keys())

    # Append all planets from unique resource systems
    for fullchain_planet in unique_resource_planets:
        final_planets.append(fullchain_planet)
        unique_resource_systems.append(fullchain_planet['system'])
    for unique_system in unique_resource_systems:
        for fullchain_planet in fullchain_inorganic_planets:
            if fullchain_planet['system'] == unique_system:
                final_planets.append(fullchain_planet)

    # Track captured resources and systems already processed
    captured_inorganic_groups = set()
    captured_organics = set()
    captured_inorganics = set()
    processed_systems = set(unique_resource_systems)

    # Capture resources on our unique planets
    for final_planet in final_planets:
        resource = final_planet.get('resource')
        if resource in inorganic_groups:
            # Add all members of the inorganic group to captured_inorganics
            captured_inorganic_groups.add(resource)
            captured_inorganics.update(groups['inorganic'][resource])
        elif resource in inorganic_resources:
            captured_inorganics.add(resource)
        elif resource in organic_resources:
            captured_organics.add(resource)

    ### Part 2: Look for systems with multiple fullchains, and select the ones that give us the most fullchains
    ### Then, tie-break with available on those planets. 
    while True:
        # Identify uncaptured groups and resources
        uncaptured_inorganic_groups = [resource for resource in inorganic_groups if resource not in captured_inorganic_groups]
        uncaptured_inorganics = [resource for resource in inorganic_resources if resource not in captured_inorganics and resource not in GATHERABLE_INORGANIC]
        uncaptured_organics = [resource for resource in organic_resources if resource not in captured_organics]

        if not uncaptured_inorganic_groups:
            break

        # Count uncaptured groups per system
        system_scores = {}
        counted_resources = {}
        candidate_planets = set()
        # First, score systems based on uncaptured groups in fullchain_inorganic
        for uncaptured in uncaptured_inorganic_groups:
            for fullchain_planet in fullchain_inorganic_planets:
                if fullchain_planet['system'] not in processed_systems:
                    if fullchain_planet['system'] not in system_scores:
                        system_scores[fullchain_planet['system']] = 0
                        counted_resources[fullchain_planet['system']] = set()  # Initialize a set for this system

                    # Increment score if this system provides an uncaptured resource group
                    if fullchain_planet['resource'] == uncaptured and uncaptured not in counted_resources[fullchain_planet['system']]:
                        counted_resources[fullchain_planet['system']].add(uncaptured)
                        system_scores[fullchain_planet['system']] += 1

       # Identify the maximum count of uncaptured groups and select those systems
        max_score = max(system_scores.values(), default=0)
        candidate_systems = [
            system for system in system_scores
            if system_scores[system] == max_score
        ]
        candidate_planets = [
            planet for planet in fullchain_inorganic_planets
            if planet['system'] in candidate_systems
        ]

        # Calculate tie-breaking score for candidates based on uncaptured individual resources
        # Call score_by_desired with empty desired_inorganics to only score organics
        scored_planets = score_by_desired(
            candidate_planets,
            all_systems,
            desired_inorganics=[],
            desired_organics=uncaptured_organics,
            resources_by_rarity=resources_by_rarity
        )

        # Aggregate scores by system using scored planets
        for candidate_planet in scored_planets:
            system_name = candidate_planet[0]  # system name
            planet_score = candidate_planet[1]  # score of the planet

            if system_name in system_scores:
                system_scores[system_name] += planet_score
            else:
                system_scores[system_name] = planet_score

        # Sort systems by aggregated score
        sorted_systems = sorted(
            system_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        
        # Take the first (highest-scoring) system
        selected_system = sorted_systems[0][0]
        # Add other full chain planets in system
        for fullchain_planet in fullchain_inorganic_planets:
            if fullchain_planet['system'] == selected_system:
                final_planets.append(fullchain_planet)
                captured_inorganic_groups.add(fullchain_planet['resource'])
                # Add resources in resource groups to captured_inorganics
                captured_inorganics.update(groups['inorganic'][fullchain_planet['resource']])

                # Capture any organic resoureces available on a captured full chain
                for system in all_systems:
                    if system['name'] == selected_system:
                        for planet in system['planets']:
                            if planet['name'] == fullchain_planet['planet']:
                                captured_organics.update(planet['resources']['organic'])
        processed_systems.add(selected_system)
    

    uncaptured_inorganic_groups = [resource for resource in inorganic_groups if resource not in captured_inorganic_groups]
    uncaptured_inorganics = [resource for resource in inorganic_resources if resource not in captured_inorganics and resource not in GATHERABLE_INORGANIC]
    uncaptured_organics = [resource for resource in organic_resources if resource not in captured_organics]

    print(f"{uncaptured_inorganic_groups}")
    print(f"{uncaptured_inorganics}")
    print(f"{uncaptured_organics}")
    return final_planets





def write_to_csv(data, filename, output_folder='output', include_unique_resources=False):
    """Write data to a CSV file in an output folder, sorted by 'system' and 'planet' alphabetically."""
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Sort data by 'system' and 'planet' alphabetically
    sorted_data = sorted(data, key=lambda x: (x.get('system', ''), x['planet']))
    
    # Full path for the output file
    file_path = os.path.join(output_folder, filename)

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Adjusted header order with single quotes for static text
        header = [
            'System', 'Planet', 'Resource Group' if not include_unique_resources else 'Unique Resources', 
            'Inorganic Score', 'Organic Score', 'Habitability Score', 
        ]
        writer.writerow(header)
        
        # Write sorted data rows with reordered columns
        for row in sorted_data:
            writer.writerow([
                row.get('system', ''), row['planet'], 
                row.get('resource', '') if not include_unique_resources else ', '.join(row.get('unique_resources', [])),
                row['inorganic_score'], row['organic_score'], row['habitability_score'],
            ])
    
    print(f"Data written to {file_path}")


if __name__ == '__main__':
    inorganic_rarity = load_resources(INORGANIC_DATA_PATH, shortname=False)
    organic_rarity = load_resources(ORGANIC_DATA_PATH, shortname=False)
    rarity = { 'inorganic': inorganic_rarity, 'organic': organic_rarity}
    
    # I do it like this to keep the door open for organic groups. 
    unique = {
    category: {
        key: value
        for key, value in items.items()
        if value == 'Unique' and key not in GATHERABLE_INORGANIC
    }
    for category, items in rarity.items()
}

    inorganic_groups = load_resource_groups(INORGANIC_GROUPS_PATH, unique['inorganic'])
    groups = {'inorganic': inorganic_groups}

    all_systems = load_system_data(SCORED_SYSTEM_DATA_PATH)

    fullchain_inorganic_planets = find_fullchain_planets(all_systems, groups['inorganic'])
    unique_resource_planets = find_unique_resources(all_systems, unique)
    selected_systems = find_best_systems(all_systems, fullchain_inorganic_planets, unique_resource_planets, rarity, groups)
