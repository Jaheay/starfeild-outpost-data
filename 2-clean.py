import json
import re

def classify_planet_type(planet):
    if "giant" in planet['planet_type'].lower():
        planet['planet_type'] = ['Gas', planet['planet_type']]
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


if __name__ == '__main__':
    with open('data/1_scraped_systems_data.json', 'r') as file:
        systems = json.load(file)

    for system in systems:
        for planet in system['planets']:
            # Classify planet type
            planet = classify_planet_type(planet)

            # Clean atmosphere data
            if planet['atmosphere']:
                planet['atmosphere'] = standardize_atmosphere(planet['atmosphere'])

            # Standardize Day Length
            planet['day_length'] = standardize_day_length(planet['day_length'])

    with open('data/2_clean_systems_data.json', 'w') as file:
        json.dump(systems, file, indent=4)

