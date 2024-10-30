import csv
import json
import os

RAW_SYSTEM_DATA_PATH = 'data/raw_systems_data.json'
SCORED_SYSTEM_DATA_PATH = 'data/raw_systems_data.json'
INORGANIC_DATA_PATH = 'data/inorganic.csv'
ORGANIC_DATA_PATH = 'data/organic.csv'
INORGANIC_GROUPS_PATH='data/inorganic_groups.json'

GATHERABLE_INORGANIC = ['Aqueous Hematite', 'Caelumite']
RARITY_SCORES = {'Common': 1, 'Uncommon': 2, 'Rare': 4, 'Exotic': 8, 'Unique': 16}

def load_resources(filename, shortname=False):
    resources = {}
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            resource_name = row['Resource'].strip()
            if shortname: 
                # Use resource name if short name is empty
                short_name = row['Short name'].strip() if row['Short name'].strip() else resource_name 
                resources[short_name] = {
                    'Resource': resource_name,
                    'Rarity': row['Rarity'].strip()
                }
            else: 
                resources[resource_name] = row['Rarity'].strip()
    
    return resources

def load_system_data(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            all_system_data = json.load(f)
    else:
        all_system_data = []
    return all_system_data

def save_system_data(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
def load_resource_groups(filename, unique_resource):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    result = {}

    for key, values in data.items():
        if isinstance(values, list):
            # Filter and add lists directly to the result
            filtered_values = [item for item in values if item not in unique_resource]
            if filtered_values:
                result[key] = filtered_values
        elif isinstance(values, dict):
            # Flatten nested structures with 'Main' list
            main_values = values.get('Main', [])
            for sub_key, sub_values in values.items():
                if sub_key != 'Main':  # Ignore the 'Main' key itself
                    combined_values = main_values + sub_values
                    filtered_combined = [item for item in combined_values if item not in unique_resource]
                    if filtered_combined:
                        result[f"{sub_key}"] = filtered_combined
    return result

    
def get_gatherable_domesticable(planet, flora_only=False, fauna_only=False):
    """Collect gatherable and domesticable resources from a planet."""
    
    # Gatherable resources
    gatherable_resources = set()
    domesticable_resources = set()

    # Accessing fauna and flora data
    fauna_data = planet.get('fauna', {})
    flora_data = planet.get('flora', {})

    # Collecting gatherable flora
    if not fauna_only:
        for flora, name in flora_data.get('gatherable', {}).items():
            gatherable_resources.add(flora)

    # Collecting gatherable fauna
    if not flora_only:
        for fauna, name in fauna_data.get('gatherable', {}).items():
            gatherable_resources.add(fauna)

    # Collecting domesticable flora
    if not fauna_only:
        for flora, name in flora_data.get('domesticable', {}).items():
            domesticable_resources.add(flora)

    # Collecting domesticable fauna
    if not flora_only:
        for fauna, name in fauna_data.get('domesticable', {}).items():
            domesticable_resources.add(fauna)

    return domesticable_resources, gatherable_resources

def score_resources(resource_list, resource_rarity):
    
    score = 0
    for resource in resource_list:
        rarity = resource_rarity.get(resource, 'Common')
        score += RARITY_SCORES.get(rarity, 1)  # Default to common score if unknown
    return score
