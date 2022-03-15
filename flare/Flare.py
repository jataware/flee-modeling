import Ruleset
from Country import Country


if __name__ == "__main__":

    simulation_period = 2000
    flare_window_size = 100
    total_windows = int(simulation_period / flare_window_size)

    ethiopia = Country("ethiopia", flare_window_size)

    burundi = Country("burundi", flare_window_size)
    car = Country("car", flare_window_size)
    ethiopia = Country("ethiopia", flare_window_size)
    mali = Country("mali", flare_window_size)
    nigeria = Country("nigeria", flare_window_size)
    ssudan = Country("ssudan", flare_window_size)
    ssudan_food = Country("ssudan_food", flare_window_size)
    ssudan_whole_revised = Country("ssudan_whole_revised", flare_window_size)
    syria2013 = Country("syria2013", flare_window_size)

#     algeria = Country("algeria", flare_window_size)
#     burundi = Country("burundi", flare_window_size)
#     congo_brazzaville = Country("congo_brazzaville", flare_window_size)
#     congo_kinshasa = Country("congo_kinshasa", flare_window_size)
#     cote_divoire = Country("cote_divoire", flare_window_size)
#     guinea_bissau = Country("guinea-bissau", flare_window_size)
#     liberia = Country("liberia", flare_window_size)



    simulation_dataset = Ruleset.Simulation(ethiopia, total_windows, flare_window_size)
    #elicitation_dataset = Ruleset.Elicitation([])
#     for i in 'burundi  car  ethiopia  mali  nigeria  ssudan  ssudan_food  ssudan_whole_revised  syria2013'.split():
#         try:
#             print(f"Trying {i}")
#             simulation_dataset = Ruleset.Simulation(locals()[i], total_windows, flare_window_size)
#             print("Success")
#         except:
#             print("Failure")
