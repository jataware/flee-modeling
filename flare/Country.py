from flee import InputGeography


def get_flare_window(flare_day, window_size):
    lower_boundary_of_window = 1
    upper_boundary_of_window = window_size
    current_window = 1

    if flare_day == "":
        return -1
    elif int(flare_day) == 0:
        return 0
    else:
        window_found = False
        while not window_found:
            if lower_boundary_of_window <= int(flare_day) <= upper_boundary_of_window:
                return current_window
            else:
                upper_boundary_of_window += window_size
                lower_boundary_of_window += window_size
                current_window += 1
                window_found = False

def get_flare_indicator(flare_day):
    if flare_day == "":
        return 0
    else:
        return 1


class Country:
    def __init__(self, country_name, window_size):

        self.name = country_name
        input_directory = "input/" + self.name + "/input_csv/"

        input_geography = InputGeography.InputGeography()

        input_geography.ReadLocationsFromCSV("%slocations.csv" % input_directory)

        no_ancillary_input_data = False
        try:
            input_geography.ReadLinksFromCSV("%sroutes.csv" % input_directory)
            input_geography.ReadClosuresFromCSV("%sclosures.csv" % input_directory)
        except FileNotFoundError:
            no_ancillary_input_data = True

        self.locations = {}

        self.location_names = []
        self.population = 0
        self.regions = {}
        for location in input_geography.locations:
            if location[7].lower() == self.name.lower():
                try:
                    pop = int(location[1])
                except:
                    continue
                location_name = location[0]
                self.location_names.append(location_name)
                self.locations[location_name] = {
                    "population": pop,
                    "latitude": location[2],
                    "longitude": location[3],
                    "type": location[4],
                    "flare_day": location[5],
                    "region": location[6],
                    "country": location[7]
                }
                print(self.locations[location_name])

                # Save the location's flare window:
                self.locations[location_name]["flare_window"] = (get_flare_window(self.locations[location_name]["flare_day"], window_size))

                # Save the location's flare indicator:
                self.locations[location_name]["flare_indicator"] = get_flare_indicator(self.locations[location_name]["flare_day"])

                # Add the location's population to the national population:
                self.population += int(self.locations[location_name]["population"])

                # Add the location and its population to its region:
                self.add_member_and_population_to_region(location_name, self.locations[location_name]["population"], self.locations[location_name]["region"])

        self.links = []
        if not no_ancillary_input_data:
            self.filter_out_external_links(input_geography.links)

        for location_name in self.locations:
            self.locations[location_name]["links"] = self.get_links(location_name)

            # Add what percent of the national population this location is:
            self.locations[location_name]["pc_national_population"] = ((int(self.locations[location_name]["population"]) / self.population) * 100)

            # Add what percent of the regional population this location is:
            try:
                regional_population = self.regions[self.locations[location_name]["region"]]["population"]
                self.locations[location_name]["pc_regional_population"] = ((int(self.locations[location_name]["population"]) / regional_population) * 100)
            except ZeroDivisionError:
                self.locations[location_name]["pc_regional_population"] = 0.0

            self.locations[location_name]["regional_neighbours"] = self.regions[self.locations[location_name]["region"]]["members"]

    def filter_out_external_links(self, links):
        for link in links:
            if link[0] and link[1] in self.location_names:
                self.links.append(link)

    def add_member_and_population_to_region(self, name, population, region_name):
        if region_name not in self.regions:
            self.regions[region_name] = {
                "members": [],
                "population": 0
            }
        self.regions[region_name]["members"].append(name)
        self.regions[region_name]["population"] += int(population)

    def get_links(self, name):
        links = []
        for link in self.links:
            if link[0] == name:
                links.append([link[1], link[2]])
            elif link[1] == name:
                links.append([link[0], link[2]])
        return links
