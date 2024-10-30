import csv
import json

def load_resources(filename, shortname=True):
    resources = {}
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            resource_name = row['Resource'].strip()
            # Use resource name if short name is empty
            short_name = row['Short name'].strip() if row['Short name'].strip() else resource_name  
            if shortname: 
                resources[short_name] = {
                    'Resource': resource_name,
                    'Rarity': row['Rarity'].strip()
                }
            else: 
                resources[resource_name] = row['Rarity'].strip()
    
    return resources

def load_planets(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def load_resource_groups(filename): 
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)