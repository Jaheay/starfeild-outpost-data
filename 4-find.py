from common import load_resources, load_planets, load_resource_groups
import json
import csv
from collections import defaultdict
import os

def get_unique_resources(planet_resources, unique_resources):
    """Get unique resources present on the planet."""
    unique_res = [resource for resource in planet_resources if resource in unique_resources]
    return unique_res

def check_complete_group(resources, resource_group):
    """Check if the planet has a complete set of resources from a resource group."""
    complete = all(item in resources for item in resource_group)
    return complete

def flatten_and_filter_resource_groups(data, unique_resource):
    # Split the unique resources into a set for efficient look-up
    result = {}

    # Helper function to process nested structures
    for key, values in data.items():
        if isinstance(values, list):
            # If it's a list, filter and add directly to the result
            filtered_values = [item for item in values if item not in unique_resource]
            if filtered_values:  # Only add if not empty
                result[key] = filtered_values
        elif isinstance(values, dict):
            # Extract the 'Main' list
            main_values = values.get('Main', [])
            # Prepare to flatten subgroups
            for sub_key, sub_values in values.items():
                if sub_key != 'Main':  # Ignore the 'Main' key itself
                    combined_values = main_values + sub_values
                    # Filter out unique resources
                    filtered_combined = [item for item in combined_values if item not in unique_resource]
                    # Add to the result with the combined key
                    if filtered_combined:  # Only add if not empty
                        result[f"{sub_key}"] = filtered_combined
    print(json.dumps(result, indent=4))
    return result


def analyze_inorganic_resources(system_data, inorganic_groups, unique_resources):
    results = []
    unique_results = []

    # Loop through systems and planets to check resources
    for system in system_data:
        for planet in system.get('planets', []):
            planet_resources = planet['resources']['inorganic']
            planet_scores = planet['scores']

            # Create a base info dictionary for the planet
            base_info = {
                'system': system['name'],
                'planet': planet['name'],
                'inorganic_score': float(planet_scores['inorganic_score']),
                'organic_score': float(planet_scores['organic_score']),
                'atmosphere_density': planet['atmosphere']['density'],
                'atmosphere_type': planet['atmosphere']['type'],
                'atmosphere_property': planet['atmosphere']['property'],
                'habitability_score': float(planet_scores['habitability_score'])
            }

            # Check for all complete resource groups
            for group_name, required_resources in inorganic_groups.items():
                if check_complete_group(planet_resources, required_resources):
                    # Copy base_info for each group to avoid overwriting
                    group_info = base_info.copy()
                    group_info['resource'] = group_name
                    results.append(group_info)

            # Check for unique resources separately
            unique_res = get_unique_resources(planet_resources, unique_resources)
            if unique_res:
                unique_info = base_info.copy()
                unique_info['unique_resource'] = unique_res
                unique_results.append(unique_info)

    # Sort by inorganic score in descending order
    results.sort(key=lambda x: x['inorganic_score'], reverse=True)
    unique_results.sort(key=lambda x: x['inorganic_score'], reverse=True)

    return results, unique_results

def print_highest_score_planet_per_group(inorganic_groups_flat, complete_resource_planets):
    highest_score_planets = {}

    # Loop through each group in inorganic_groups_flat
    for group_name in inorganic_groups_flat:
        # Filter for planets that contain the current resource group
        group_planets = [planet for planet in complete_resource_planets if planet.get('resource') == group_name]

        if group_planets:
            # Find the planet with the highest inorganic score in this group
            highest_score_planet = max(group_planets, key=lambda p: p['inorganic_score'])
            highest_score_planets[group_name] = (highest_score_planet['planet'], highest_score_planet['inorganic_score'])
        else:
            # If no planets match, set result to None
            highest_score_planets[group_name] = ('None', None)

    # Print the result for each group
    for group, (planet_name, score) in highest_score_planets.items():
        print(f"{group}: {planet_name}, Score: {score}")

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
            'Atmosphere Density', 'Atmosphere Type', 'Atmosphere Property'
        ]
        writer.writerow(header)
        
        # Write sorted data rows with reordered columns
        for row in sorted_data:
            writer.writerow([
                row.get('system', ''), row['planet'], 
                row.get('resource', '') if not include_unique_resources else ', '.join(row.get('unique_resources', [])),
                row['inorganic_score'], row['organic_score'], row['habitability_score'],
                row['atmosphere_density'], row['atmosphere_type'], row['atmosphere_property']
            ])
    
    print(f"Data written to {file_path}")


def print_selected_systems(selected_systems, results):
    """Print the selected systems and the resources they cover."""
    for system in selected_systems:
        print(f'System: {system}')
        for planet in results:
            if planet['system'] == system:
                print(f"  {planet['planet']}: {planet['resource']}, Score: {planet['inorganic_score']}")


def find_best_systems(complete_resource_planets, unique_resource_planets, inorganic_groups_flat):
    final_planets = []
    unique_resource_systems = []

    # Convert single-entry 'unique_resource' lists to the string in 'resource'
    for planet in unique_resource_planets:
        planet['resource'] = planet.pop('unique_resource', [None])[0]

    # Step 1: Collect unique resource planets
    for planet in unique_resource_planets:
        final_planets.append(planet)
        unique_resource_systems.append(planet['system'])

    # Step 2: Append all planets from unique resource systems
    for unique_system in unique_resource_systems:
        for planet in complete_resource_planets:
            if planet['system'] == unique_system:
                final_planets.append(planet)

    # Track captured resources and systems already processed
    captured_resources = {planet['resource'] for planet in final_planets}
    processed_systems = set(unique_resource_systems)

    while True:
        # Step 3: Identify uncaptured resources
        uncaptured_resources = [resource for resource in inorganic_groups_flat if resource not in captured_resources]

        if not uncaptured_resources:
            break

        # Step 4: Score systems based on uncaptured resources
        system_scores = {}
        counted_resources = {}

        for uncaptured in uncaptured_resources:
            for planet in complete_resource_planets:
                if planet['system'] not in processed_systems:
                    if planet['system'] not in system_scores:
                        system_scores[planet['system']] = 0
                        counted_resources[planet['system']] = set()  # Initialize a set for this system

                    # Increment score if this system provides an uncaptured resource
                    if planet['resource'] == uncaptured:
                        # Only increment if this resource hasn't been counted yet for the system
                        if uncaptured not in counted_resources[planet['system']]:
                            counted_resources[planet['system']].add(uncaptured)
                            system_scores[planet['system']] += 1
        
        # Step 5: Sort systems based on score
        max_score = max(system_scores.values(), default=0)
        sorted_systems = sorted(
            [
                (planet['system'], planet['inorganic_score'])
                for planet in complete_resource_planets
                if planet['system'] not in processed_systems and system_scores[planet['system']] == max_score
            ],
            key=lambda x: x[1],
            reverse=True
        )

        # Step 6: Add highest-scoring system to final planets and update tracked data
        for system_name, _ in sorted_systems:
            for planet in complete_resource_planets:
                if planet['system'] == system_name:
                    final_planets.append(planet)
                    captured_resources.add(planet['resource'])

            # Mark system as processed
            processed_systems.add(system_name)
            break  # Exit after processing one system

    return final_planets




if __name__ == '__main__':
    # Load data
    inorganic_dict = load_resources('data/inorganic.csv', shortname=False)
    inorganic_groups = load_resource_groups('data/inorganic_groups.json')
    organic_dict = load_resources('data/organic.csv', shortname=False)
    #systems = load_planets('data/3_scored_systems_data.json')
    unique_resources = {resource for resource, rarity in inorganic_dict.items() if rarity == 'Unique'}
    inorganic_groups_flat = flatten_and_filter_resource_groups(inorganic_groups, unique_resources)

    # Analyze resources and print results
    complete_resource_planets, unique_resource_planets = analyze_inorganic_resources(systems, inorganic_groups_flat, unique_resources)
    selected_systems = find_best_systems(complete_resource_planets, unique_resource_planets, inorganic_groups_flat)
    #print_highest_score_planet_per_group(inorganic_groups_flat, complete_resource_planets)

   

    # Print the selected systems and the resources they cover
    #print_selected_systems(selected_systems, complete_resource_planets)

    # Write results to CSV files
    write_to_csv(complete_resource_planets, 'complete_resource_groups.csv')
    write_to_csv(unique_resource_planets, 'unique_resources.csv', include_unique_resources=True)
    write_to_csv(selected_systems, 'selected_systems.csv')