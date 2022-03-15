import copy
import math
import random
from collections import Counter, OrderedDict
import tqdm

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn import metrics, tree, model_selection


def create_dataframe(dataset):
    data = []
    headers = []
    for country in dataset:
        for location in country.locations:
            data.append(country.locations[location].values())
            if len(headers) == 0:
                headers = country.locations[location].keys()
    df = pd.DataFrame(data, columns=headers)
    return df

class Elicitation:
    def __init__(self, dataset):

        self.df = create_dataframe(dataset)
        self.df = self.df.drop(columns=["latitude", "flare_day", "longitude", "type", "region", "links", "country", "regional_neighbours"])

        print(self.df.describe())
        print(self.df)

        self.current_lead = "pc_regional_population"

        self.plot_lead()

        self.find_and_plot_best_fitting_tree(1500000, .2)


    def plot_lead(self):
        sns.set(style="whitegrid", color_codes=True)
        sns.set(rc={"figure.figsize": (12, 5)})

        sns.barplot(x='flare_indicator', y=self.current_lead, data=self.df)
        plt.show()

        sns.barplot(x='flare_window', y=self.current_lead, data=self.df)
        plt.show()

    def find_and_plot_best_fitting_tree(self, number_of_runs, percentage_of_testing_data):
        attributes = self.df[[self.current_lead]]
        targets = self.df['flare_window']

        best_fitting_tree = 0
        best_mcc = -1
        key_of_best_fitting_tree = 0

        print("Searching for best tree...")
        # Sometimes during a run, "RuntimeWarning: invalid value encountered in double_scalars" is outputted. It just
        # means that a run failed because sklearn.metrics tried to find the square root of a negative number or zero.
        # The algorithm will move on to the next run when this happens.
        for run in tqdm.tqdm(range(0, number_of_runs)):
            training_attributes, testing_attributes, training_targets, testing_targets = \
                model_selection.train_test_split(attributes, targets, test_size=percentage_of_testing_data,
                                                 shuffle=True)

            best_fitting_tree_candidate = tree.DecisionTreeClassifier()
            best_fitting_tree_candidate = best_fitting_tree_candidate.fit(training_attributes, training_targets)

            target_prediction = best_fitting_tree_candidate.predict(testing_attributes)

            candidate_mcc = metrics.matthews_corrcoef(testing_targets, target_prediction)

            if candidate_mcc > best_mcc:
                best_fitting_tree = best_fitting_tree_candidate
                best_mcc = candidate_mcc

                # The following is needed in order to be able to map the bins in the .dot file to the targets:
                window_counters = dict(Counter(training_targets))
                key = OrderedDict(sorted(window_counters.items()))

        tree.export_graphviz(best_fitting_tree, out_file="tree-out.dot")
        print("Best fitting tree identified and can be found at 'Flare/tree-out.dot', here are the details:")
        print("     - MCC: " + str(best_mcc))
        print("     - Key (bin, frequency): " + str(key))


def test_threshold(flare_threshold):
    threshold_tester = random.uniform(0.001, 1)
    if threshold_tester <= flare_threshold:
        return True
    else:
        return False


def initialise_location(location):
    if location["flare_window"] == 0:
        location["is_flared"] = True
    else:
        location["is_flared"] = False


def initialise_dataset(dataset):
    copy_of_dataset = copy.deepcopy(dataset)
    for location in copy_of_dataset.locations:
        initialise_location(copy_of_dataset.locations[location])
    return copy_of_dataset


class Simulation:
    def __init__(self, dataset, total_windows, window_size, output_file_name=None):

        self.dataset = initialise_dataset(dataset)
        if output_file_name is None:
            self.output_file_name = "output.csv"
        else:
            self.output_file_name = output_file_name
        header_row = [location_name for location_name in self.dataset.locations]
        window_rows = []

        for window in range(total_windows):
            window_row = []
            for location in self.dataset.locations:
                if self.dataset.locations[location]["is_flared"]:
                    flare_predicted = True
                else:
                    flare_predicted = self.make_prediction(location, window)

                if flare_predicted:
                    self.dataset.locations[location]["is_flared"] = True
                    window_row.append(1)
                else:
                    window_row.append(0)
            window_rows.append(window_row)
        self.evaluate(window_rows)
        self.output_to_flee(window_rows, window_size, header_row)

    def evaluate(self, predictions):
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        error_counter = 0

        transposed_predictions = [list(i) for i in zip(*predictions)]
        prediction_count = 0
        for location in self.dataset.locations:
            target = (self.dataset.locations[location]["flare_window"])
            prediction = transposed_predictions[prediction_count]
            if 1 in prediction:
                if target >= 0:
                    if target != prediction.index(1):
                        error_counter += 1
                    true_positives += 1
                else:
                    false_positives += 1
            else:
                if target >= 0:
                    true_negatives += 1
                else:
                    false_negatives += 1
            prediction_count += 1

        try:
            precision = true_positives / (true_positives + false_positives)
            recall = true_positives / (true_positives + false_negatives)
        except ZeroDivisionError:
            print("Error - Metrics couldn't be calculated because of a zero division error")
            precision = 0
            recall = 0

        try:
            mcc = ((true_positives * true_negatives) - (false_positives * false_negatives)) / \
                  math.sqrt((true_positives + false_positives) * (true_positives + false_negatives) *
                            (true_negatives + false_positives) * (true_negatives + false_negatives))
        except ZeroDivisionError:
            print("Error - Metric couldn't be calculated because of a zero division error")
            mcc = -1

        print("How well does Flare correctly predict whether or not a conflict will erupt in a location?")
        print("     - True positives: " + str(true_positives))
        print("     - False positives: " + str(false_positives))
        print("     - True negatives: " + str(true_negatives))
        print("     - False negatives: " + str(false_negatives))
        print()
        print("     - Precision: " + str(precision))
        print("     - Recall: " + str(recall))
        print("     - MCC: " + str(mcc))
        print()

        print("In cases where Flare correctly predicts that a conflict will erupt in a location, how often does it "
              "predict the incorrect starting window? ")
        try:
            print("    - Error rate: " + str(error_counter/true_positives))
        except ZeroDivisionError:
            print("    - There were no such cases.")

    def output_to_flee(self, predictions, window_size, header_row):
        transposed_predictions = [list(i) for i in zip(*predictions)]
        all_expanded_predictions = []
        for location in transposed_predictions:
            expanded_predictions = []
            has_flared_before = False
            for window in location:
                if window == 0:
                    for day in range(window_size):
                        expanded_predictions.append(0)
                if window == 1:
                    if has_flared_before:
                        for day in range(window_size):
                            expanded_predictions.append(1)
                    else:
                        random_day_of_flare = random.randint(0, window_size)
                        for day in range(window_size):
                            if day >= random_day_of_flare:
                                expanded_predictions.append(1)
                            else:
                                expanded_predictions.append(0)
                    has_flared_before = True
            all_expanded_predictions.append(expanded_predictions)
        detransposed_predictions = [list(i) for i in zip(*all_expanded_predictions)]

        df = pd.DataFrame(data=detransposed_predictions, columns=header_row)
        df.to_csv(self.output_file_name, index_label="#Days")

    def make_prediction(self, location, window):
        votes = [self.cast_national_population_vote(location, window),
                 self.cast_regional_population_vote(location, window)]
        winner = max(votes, key=votes.count)
        return winner

    def cast_adjacency_vote(self, location):
        adjacent_flare_multiplier = 0.005
        total_flared_links = 0
        for link in self.dataset.locations[location]["links"]:
            linked_location = link[0]
            if self.dataset.locations[linked_location]["is_flared"]:
                total_flared_links += 1
        flare_predicted = test_threshold(adjacent_flare_multiplier * total_flared_links)
        if flare_predicted:
            return 1
        else:
            return 0

    def cast_national_population_vote(self, location, window):
        flare_predicted = False
        pc_natpop = self.dataset.locations[location]["pc_national_population"]
        if 31.841 < pc_natpop:
            if window == 3:
                flare_predicted = test_threshold(0.75)
        elif 1.348 < pc_natpop <= 31.841:
            if window == 1:
                flare_predicted = test_threshold(0.14285714285)
            elif window in [2, 4, 5, 8, 11, 12, 14]:
                flare_predicted = test_threshold(0.02857142857)
            elif window in [7, 10]:
                flare_predicted = test_threshold(0.05714285714)
        elif .362 < pc_natpop <= 1.348:
            if window in [1, 10, 11, 13, 15, 16]:
                flare_predicted = test_threshold(0.0078125)
            elif window in [2, 3, 4]:
                flare_predicted = test_threshold(0.0234375)
            elif window == 9:
                flare_predicted = test_threshold(0.0390625)
        elif .019 < pc_natpop <= .362:
            if window in [1, 4]:
                flare_predicted = test_threshold(0.0390625)
            elif window in [2, 3, 5, 6, 8, 11, 12, 14]:
                flare_predicted = test_threshold(0.00398406374)
            elif window == 10:
                flare_predicted = test_threshold(0.01195219123)
        if flare_predicted:
            return 1
        else:
            return 0

    def cast_regional_population_vote(self, location, window):
        flare_predicted = False
        pc_regpop = self.dataset.locations[location]["pc_regional_population"]
        if 50.226 < pc_regpop:
            if window == 1:
                flare_predicted = test_threshold(0.08)
            elif window in [2, 7, 9, 10]:
                flare_predicted = test_threshold(0.04)
            elif window in [3, 5, 8, 14]:
                flare_predicted = test_threshold(0.02666666666)
            elif window in [4, 6, 11, 12, 13, 16]:
                flare_predicted = test_threshold(0.01333333333)
        elif 0.031 < pc_regpop <= 7.543:
            if window == 13:
                flare_predicted = test_threshold(0.0071942446)
        elif 7.543 < pc_regpop <= 20.588:
            if window in [1, 2, 4, 10, 11, 12, 14]:
                flare_predicted = test_threshold(0.00833333333)
            elif window == 15:
                flare_predicted = test_threshold(0.01666666666)
        elif 20.588 < pc_regpop <= 50.226:
            if window in [1, 4]:
                flare_predicted = test_threshold(0.0487804878)
            elif window in [3, 5, 6, 7, 9, 11]:
                flare_predicted = test_threshold(0.01219512195)

        if flare_predicted:
            return 1
        else:
            return 0


