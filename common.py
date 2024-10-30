import csv
import json

RAW_SYSTEM_DATA_PATH = 'data/raw_systems_data.json'
INORGANIC_DATA_PATH = 'data/inorganic.csv'
ORGANIC_DATA_PATH = 'data/organic.csv'
INORGANIC_GROUPS_PATH='data/inorganic_groups.json'

GATHERABLE_INORGANIC = ['Aqueous Hematite', 'Caelumite']

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

def load_planets(filename=RAW_SYSTEM_DATA_PATH):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def load_resource_groups(filename=INORGANIC_GROUPS_PATH): 
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)