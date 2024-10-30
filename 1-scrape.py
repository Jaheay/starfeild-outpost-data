from time import sleep
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import json
from common import load_resources


def clean_output(text):

    
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


def scrape_star_system(system_id):
    url = f"https://inara.cz/starfield/starsystem/{system_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract and clean system name
    system_name = clean_output(soup.find('h2', class_='itemname').text.strip()).strip()

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
        planet['biomes'] = biomes

        planets.append(planet)

    return {
        'system_name': system_name,
        'planets': planets
    }

def process_resources(planet, organic_dict, inorganic_dict):
    organic = []
    inorganic = []
    other = []

    # Process each resource
    for resource in planet.get('resources', []):
        cleaned_resource = clean_output(resource)
        if cleaned_resource in inorganic_dict:
            inorganic.append(inorganic_dict[cleaned_resource]['Resource'])
        elif cleaned_resource in organic_dict:
            organic.append(organic_dict[cleaned_resource]['Resource'])
        else:
            other.append(resource)
    
    planet['resources'] = {
        'inorganic': inorganic,
        'organic': organic,
        'other': other
    }

def process_biomes(planet):
    # Clean up the biomes by removing any percentages
    planet['biomes'] = [biome.split()[0] for biome in planet.get('biomes', [])]

def process_metadata(planet):
    # Remove space in gravity and adjust planetary habitation
    if 'gravity' in planet:
        planet['gravity'] = planet['gravity'].replace(' ', '')
        
    if 'planetary_habitation' in planet:
        # Convert "Rank X required" to just "X"
        match = re.search(r'Rank (\d)', planet['planetary_habitation'])
        if match:
            planet['planetary_habitation'] = match.group(1)  # Extract the number
        elif planet['planetary_habitation'] == '-':
            planet['planetary_habitation'] = '0'
        else:
            planet['planetary_habitation'] = str(planet['planetary_habitation']).strip()
   

if __name__ == '__main__':
    inorganic_dict = load_resources('data/inorganic.csv')
    organic_dict = load_resources('data/organic.csv')

    if os.path.exists('data/star_systems_data.json'):
        with open('data/star_systems_data.json', 'r') as f:
            existing_data = json.load(f)
        existing_system_ids = {system['id'] for system in existing_data}
    else:
        existing_data = []
        existing_system_ids = set()

    new_data = []
    for system_id in range(1, 123):  # Inclusive of 1 to 122
        if system_id in existing_system_ids:
            continue

        print(f"Scraping system #{system_id}...")
        try:
            star_system_data = scrape_star_system(system_id)
            star_system_data['id'] = system_id  # Add ID
            print(f"System Name Processed: {star_system_data['name']}")

            for planet in star_system_data['planets']:
                process_resources(planet, organic_dict, inorganic_dict)
                process_biomes(planet)
                process_metadata(planet)

            new_data.append(star_system_data)

        except Exception as e:
            print(f"Failed to scrape system #{system_id}: {e}")
            continue

        sleep(5)

    existing_data.extend(new_data)

    with open('data/1_scraped_systems_data.json', 'w') as output_file:
        json.dump(existing_data, output_file, indent=4)



