from time import sleep
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import json
from common import *


def clean_output(text):
    """
    Cleans the given text by converting subscripts to normal numbers,
    removing unwanted Unicode characters, and excessive spaces.
    """
    
    # Convert subscripts (this is specific to numbers, extend as needed)
    subscripts = {
        '\u2080': '0',
        '\u2081': '1',
        '\u2082': '2',
        '\u2083': '3',
        '\u2084': '4',
        '\u2085': '5',
        '\u2086': '6',
        '\u2087': '7',
        '\u2088': '8',
        '\u2089': '9'
    }

    # Replace subscript numbers with normal ones
    for sub, norm in subscripts.items():
        text = text.replace(sub, norm)

    # Remove unwanted Unicode characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Remove excessive spaces (e.g., around "100%")
    text = re.sub(r'\s+', ' ', text)
    
    return text


def scrape_star_system(url):
    """Scrapes the star system data from INARA the given url to the system"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract and clean system name
    name = clean_output(soup.find('h2', class_='itemname').text.strip()).strip()
    # Extract planet data
    planets = []
    tree_items = soup.find_all('li', class_='treeitem')

    for tree_item in tree_items:
        planet = {}

        # Clean planet name (header)
        planet['name'] = clean_output(tree_item.find('h3', class_='bodyname').text.strip()).strip()

        # Planet attributes
        attributes = tree_item.find_all('div', class_='itempaircontainer')
        for attr in attributes:
            label = attr.find('div', class_='itempairlabel').text.strip().lower().replace(" ", "_")
            value = clean_output(attr.find('div', class_='itempairvalue').text.strip()).strip()
            planet[label] = value

        # Resources
        resources = [clean_output(res.text.strip()).strip() for res in tree_item.find_all('a', class_='tag')]
        planet['resources'] = resources

        # Biomes
        biomes = [clean_output(biome.text.strip()).strip() for biome in tree_item.find_all('span', class_='tag minor')]
        planet['biomes'] = [biome.split()[0] for biome in biomes]

        # Domesticable flora and fauna
        planet['domesticable'] = {'flora': {}, 'fauna': {}}
        domesticable_section = tree_item.find(string='domesticable')
        if domesticable_section:
            for item in domesticable_section.find_next('ul').find_all('li'):
                color_class = item.find('span')['class']
                value = clean_output(item.text.split('(')[1].split(')')[0].strip())
                domesticable_name = clean_output(item.find('a').text.strip())
                if 'npcfloracolor' in color_class:
                    planet['domesticable']['flora'][value] = domesticable_name
                elif 'npcfaunacolor' in color_class:
                    planet['domesticable']['fauna'][value] = domesticable_name

        # Gatherable flora and fauna
        planet['gatherable'] = {'flora': {}, 'fauna': {}}
        gatherable_section = tree_item.find(string='gatherable')
        if gatherable_section:
            for item in gatherable_section.find_next('ul').find_all('li'):
                color_class = item.find('span')['class']
                value = clean_output(item.text.split('(')[1].split(')')[0].strip())
                gatherable_name = clean_output(item.find('a').text.strip())
                if 'npcfloracolor' in color_class:
                    planet['gatherable']['flora'][value] = gatherable_name
                elif 'npcfaunacolor' in color_class:
                    planet['gatherable']['fauna'][value] = gatherable_name

        # Traits
        traits_section = tree_item.find(string='Traits')
        if traits_section:
            planet['traits'] = [clean_output(trait.text.strip()) for trait in traits_section.find_next('div', class_='tagcontainer').find_all('span', class_='tag')]

        planets.append(planet)

    return {
        'name': name,
        'planets': planets
    }

def process_resources(planet, organic_dict, inorganic_dict):
    """
    Processes the resources of a planet, categorizing them into organic,
    inorganic, and others.
    """
     
    organic = []
    inorganic = []
    special = []
    unknown = []

    # Resources to be pulled into special
    special_resources = ['Aqueous Hematite', 'Caelumite']

    # Gatherable resources
    gatherable_resources = set()
    gatherable = planet.get('gatherable', {})
    
    # Collecting gatherable flora
    for flora, name in gatherable.get('flora', {}).items():
        gatherable_resources.add(flora)
        
    # Collecting gatherable fauna
    for fauna, name in gatherable.get('fauna', {}).items():
        gatherable_resources.add(fauna)

    # Domesticable resources
    domesticable_resources = set()
    domesticable = planet.get('domesticable', {})
    
    # Collecting domesticable flora
    for flora, name in domesticable.get('flora', {}).items():
        domesticable_resources.add(flora)
        
    # Collecting domesticable fauna
    for fauna, name in domesticable.get('fauna', {}).items():
        domesticable_resources.add(fauna)

    # Process each resource
    for resource in planet.get('resources', []):
        cleaned_resource = clean_output(resource)
        if cleaned_resource in special_resources:
            special.append(resource)  # Add to special instead of inorganic
        elif cleaned_resource in inorganic_dict:
            inorganic.append(inorganic_dict[cleaned_resource]['Resource'])
        elif cleaned_resource in organic_dict:
            organic.append(organic_dict[cleaned_resource]['Resource'])
        else:
            unknown.append(resource)

    # Remove gatherable resources that are not domesticable from the organic list
    organic = [res for res in organic if res not in gatherable_resources or res in domesticable_resources]

    resources = {
        'inorganic': inorganic,
        'organic': organic,
        'special': special,
    }
    if unknown:
        resources['unknown'] = unknown

    planet['resources'] = resources


def classify_planet_type(planet):
    if "giant" in planet['planet_type'].lower():
        planet['planet_type'] = ['Jovian', planet['planet_type']]
    else:
        planet['planet_type'] = ['Terrestrial', planet['planet_type']]
    return planet

def standardize_atmosphere(atmosphere):
    atmosphere = atmosphere.replace('Extr', 'Extreme').replace('Std', 'Standard')

    pattern = r"^(Standard|Thin|High|Extreme) (\w+)(?: \((\w+)\))?$"
    match = re.match(pattern, atmosphere)
    if match:
        density, atm_type, property_ = match.groups()
        return {
            'density': density,
            'type': atm_type,
            'property': property_ or None
        }
    return {'density': 'None', 'type': 'None', 'property': None}

def standardize_day_length(day_length): 
    if 'days' in day_length:
        day_length = float(day_length.split()[0]) * 24  # Convert days to hours
    elif 'hours' in day_length:
        day_length = float(day_length.split()[0])

    return f"{day_length} hours"

def clean_metadata(planet): 

    if 'planetary_habitation' in planet:
        # Convert "Rank X required" to just "X"
        match = re.search(r'Rank (\d)', planet['planetary_habitation'])
        if match:
            planet['planetary_habitation'] = match.group(1)  # Extract the number
        elif planet['planetary_habitation'] == '-':
            planet['planetary_habitation'] = '0'
        else:
            planet['planetary_habitation'] = str(planet['planetary_habitation']).strip()

    
    if 'planet_type' in planet: 
        planet = classify_planet_type(planet)

    if 'gravity' in planet:
        planet['gravity'] = planet['gravity'].replace(' ', '')
        
    if 'atmosphere' in planet:
        planet['atmosphere'] = standardize_atmosphere(planet['atmosphere'])

    if 'day_length' in planet:
        planet['day_length'] = standardize_day_length(planet['day_length'])



if __name__ == '__main__':
    
    inorganic_dict = load_resources(INORGANIC_DATA_PATH, shortname=True)
    organic_dict = load_resources(ORGANIC_DATA_PATH, shortname=True)

    if os.path.exists(RAW_SYSTEM_DATA_PATH):
        with open(RAW_SYSTEM_DATA_PATH, 'r') as f:
            all_system_data = json.load(f)
        system_ids = {system['id'] for system in all_system_data}
    else:
        all_system_data = []
        system_ids = set()

    new_data = []
    for system_id in range(1, 2):  # Inclusive of 1 to 122
        if system_id in system_ids:
            continue

        print(f'Scraping system #{system_id}...')
        inara_url = f'https://inara.cz/starfield/starsystem/{system_id}'
        try:
            system_data = scrape_star_system(inara_url)
            system_data['id'] = system_id  # Add ID

            if not isinstance(system_data, dict):
                raise TypeError('Expected a dictionary for system_data')
            if 'name' not in system_data:
                raise KeyError('Missing key: name')
            if 'planets' not in system_data or not isinstance(system_data['planets'], list):
                raise KeyError('Missing key: planets')

            for planet in system_data['planets']:

                
                if not isinstance(planet, dict):
                    raise TypeError('Expected a dictionary for planet data')
                if 'name' not in planet:
                    raise KeyError(f'Missing key in planet data: {planet}')

                process_resources(planet, organic_dict, inorganic_dict)
                clean_metadata(planet)

            print(f'System Name Processed: {system_data["name"]}') 
            new_data.append(system_data)

        except Exception as e:
            print(f'Failed to scrape system #{system_id}: {e}')
            continue


        sleep(5)

    all_system_data.extend(new_data)           


    with open(RAW_SYSTEM_DATA_PATH, 'w') as output_file:
        json.dump(all_system_data, output_file, indent=4)



