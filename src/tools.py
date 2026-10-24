from strands import tool
from dotenv import load_dotenv
import requests
import logging
import os

load_dotenv()

@tool
def get_country_info(country: str) -> str:
    """Get the information about the country, specifically 
    official name, language, capital and population number.
    
    Args:
        country: name of the country to get information for
    """

    url = f"https://api.restcountries.com/countries/v5"
    api_key = os.getenv("REST_COUNTRIES_API_KEY")

    # Parameter names like names.official can be found in reference fields
    params = {
        "q": country,
        "response_fields": "names.official,languages,capitals,population"
    }
    headers = {
        "Authorization": f'Bearer {api_key}'
    }

    try: 
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err} (Status code: {response.status_code})"

    except requests.exceptions.ConnectionError:
        return "Connection error: Unable to connect to the server. Please check your network."

    except requests.exceptions.Timeout:
        return "Timeout error: The server took too long to respond."

    except requests.exceptions.RequestException as err:
        return f"An unexpected request error occurred: {err}"

    else:
        data = response.json()
        item = data['data']['objects'][0]

        official_name = item['names']['official']
        language = item['languages'][0]['name']
        capital = item['capitals'][0]['name']
        population =  item['population']

    return f"{country}'s official name is {official_name}, language is {language}, capital is {capital}, population is {population}."

@tool
def population_ratio_difference(pop1: int, pop2: int) -> float:
    """Calculates the absolute difference and ratio between two population figures.

    Useful when comparing the population size of two countries or regions.

    Args:
        pop1: The population count of the first entity.
        pop2: The population count of the second entity.

    Returns:
        A formatted string describing the absolute difference and relative ratio.
    """
    if pop1 <= 0 or pop2 <= 0:
        return "Both populations must be greater than 0 for ratio calculation"

    difference = abs(pop1 - pop2)

    if pop1 > pop2:
        ratio = pop1 / pop2
        return(
            f"The difference is {difference}"
            f"The first population is {ratio:.2f} times than that of the second"
        )
    elif pop2 > pop1:
        ratio = pop2 / pop1
        return(
            f"The difference is {difference}"
            f"The second population is {ratio:.2f} times than that of the first"
        )
    else:
        return(f"Both populations are identical")
    
if __name__ == "__main__":
    result = get_country_info("Japan")
    print(result)