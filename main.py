
import argparse, json, requests
from datetime import datetime



def parse_arguments():
    parser = argparse.ArgumentParser(description="Searches for available flixbus routes from one city, to all cities in a specified country list")
    parser.add_argument(
        "-c", metavar="Country", default="Poland",
        help="Countries you would like to search for routes for. (e.g. Poland) (e.g. Hungary,Romania,Slovakia)"
    )

    parser.add_argument(
        "--file", metavar="File",
        help="Path to file containing list of countries you would like to search for routes for."
    )

    parser.add_argument(
        "depart_city",
        help="The city where you would like to depart from (e.g. Lviv)"
    )

    parser.add_argument(
        "date",
        help="The date you wish to depart in the format (dd.mm.yyyy) e.g. (25.01.2023)"
    )

    return parser.parse_args()


def get_list_of_cities(countryName):
    cities = list()
    res = requests.get(f"https://global.flixbus.com/bus/{countryName.lower()}").content.decode()
    res = res.split("<a href=\"/bus/")
    # If res > 1, we have cities.
    # If res ~2000, it returned all cities for all countries, we don't want this.
    if len(res) > 1 and len(res) < 200:
        [cities.append(city.split("\"")[0]) for city in res[1:]]
    return cities


def get_city_uuid(city):
    res = requests.get(f"https://global.api.flixbus.com/search/autocomplete/cities?q={city.capitalize()}&lang=en&country=en&flixbus_cities_only=true").content.decode()
    return json.loads(res)[0]["id"]


def get_route_from_depart_city(city, depart_id, depart_date):
    res = json.loads(requests.get(
        f"https://global.api.flixbus.com/search/service/v4/search?" + \
        f"from_city_id={depart_id}&" + \
        f"to_city_id={get_city_uuid(city)}&" + \
        f"departure_date={depart_date}&" + \
        f"products={{\"adult\":2,\"bike_slot\":0}}&" + \
        f"currency=EUR&" + \
        f"locale=en&search_by=cities&include_after_midnight_rides=0").content.decode())
    return res["trips"][0]["results"]




if __name__ == "__main__":
    args = parse_arguments()

    # Check if --file is specified, and if so use that.
    if args.file is None:
        if ',' in args.c:
            countries = args.c.split(",")
        else:
            countries = [args.c]
    else:
        with open(args.file, "r") as f:
            countries = f.read().split("\n")
            # Remove any trailing newlines, think this is important as this could make the city list grabbing act out.
            if '\n' in countries:
                countries.remove('\n')

    depart_id = get_city_uuid(args.depart_city)
    for country in countries:
        count = 0
        for city in get_list_of_cities(country):
            routes = get_route_from_depart_city(city, depart_id, args.date)
            for route in routes:
                route = routes[route]
                if route["status"] == "full":
                    continue
                prix = route["price"]
                prix_total = prix["total"]
                if prix_total > 31:
                    continue
                count += 1
                heureDep = route['departure']['human_time']
                heureArr = route['arrival']['human_time']
                time_1 = datetime.strptime(heureDep,"%H:%M")
                time_2 = datetime.strptime(heureArr,"%H:%M")
                time_interval = time_2 - time_1
                #print(time_interval)
                total_seconds = time_interval.total_seconds()
                total_minutes = int(total_seconds // 60)
                if total_minutes > 120:
                    continue
                if time_1.hour > 12:
                    continue

                #duree = heureArr - heureDep
                #print(total_minutes)
                print(f"Route found (Paris -> {city})\n===")
                print(f"- Departure: {route['departure']['human_time']} {route['departure']['human_date']}")
                print(f"- Arrival: {route['arrival']['human_time']} {route['arrival']['human_date']}")
                print(f"- Price: E{route['price']['total']}")
                print(f"- Duration: {time_interval}")
                print(f"- Remaining seats: {route['available']['seats']}")
        print(f"{count} routes found from {args.depart_city} to {country}!\n")
