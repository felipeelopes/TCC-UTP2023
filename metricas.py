import json
import csv
from collections import defaultdict


def calculate_total_possible_dependencies(dataset):
    return len(dataset) * (len(dataset) - 1)


def dependency_to_predicate(dependency):
    predicates = dependency["predicates"]
    predicate_strings = []

    for predicate in predicates:
        column1 = predicate["column1"]["columnIdentifier"]
        column2 = predicate["column2"]["columnIdentifier"]
        op = predicate["op"]

        # Convertendo o operador JSON para a notação de predicado
        if op == "EQUAL":
            op_str = "="
        elif op == "UNEQUAL":
            op_str = "≠"
        # Adicione outros operadores conforme necessário

        predicate_str = f"t0.{column1} {op_str} t1.{column2}"
        predicate_strings.append(predicate_str)

    return f"∀t0∈Hospital.csv,t1∈Hospital.csv:\n¬[{ '∧'.join(predicate_strings) }]"


def dependency_satisfied(pair, dependency):
    # Desempacotar o par de registros
    record1, record2 = pair

    # Para cada predicado na dependência
    for predicate in dependency["predicates"]:
        # Obter os identificadores das colunas envolvidas no predicado
        column1 = predicate["column1"]["columnIdentifier"]
        column2 = predicate["column2"]["columnIdentifier"]
        # Obter o operador do predicado (EQUAL ou UNEQUAL)
        op = predicate["op"]

        # Obter os valores das colunas para os registros em questão
        value1 = record1[column1]
        value2 = record2[column2]

        # Verificar se os valores satisfazem o predicado
        if op == "EQUAL" and value1 != value2:
            return False
        elif op == "UNEQUAL" and value1 == value2:
            return False

    # Se todos os predicados forem satisfeitos, retorne True
    return True


def calculate_succinctness(dcfinder_output):
    print("calculate_succinctness")
    # Calcula o tamanho de cada dependência
    lengths = [len(dc["predicates"]) for dc in dcfinder_output]

    # Encontra o tamanho da menor dependência
    min_length = min(lengths)

    # Calcula a succinctness para cada dependência
    succinctness_values = [min_length / length for length in lengths]

    return succinctness_values


def calculate_coverage(dcfinder_output, dataset):
    # Inicializar o contador para pares satisfeitos e total de pares relevantes
    satisfied_pairs = 0
    total_relevant_pairs = 0

    dataset_size = len(dataset)
    # Define um intervalo para feedback (1% do dataset)
    progress_interval = max(1, dataset_size // 100)

    # Para cada dependência
    for dependency in dcfinder_output:
        # Analisar os pares relevantes para essa dependência
        for i in range(dataset_size):
            for j in range(i + 1, dataset_size):
                total_relevant_pairs += 1
                if dependency_satisfied((dataset[i], dataset[j]), dependency):
                    satisfied_pairs += 1

            percent_complete = (i + 1) / dataset_size * 100
            print(
                f"Processando... {i + 1}/{dataset_size} tuplas analisadas ({percent_complete:.2f}% completo).")

    # Calcular a cobertura como proporção de pares satisfeitos em relação ao total de pares relevantes
    coverage = satisfied_pairs / total_relevant_pairs if total_relevant_pairs > 0 else 0
    return coverage


def calculate_degree_of_approximation(dcfinder_output, truth_standard):
    print('calculate_degree_of_approximation')
    matching_dependencies = set(map(json.dumps, dcfinder_output)).intersection(
        set(map(json.dumps, truth_standard)))
    return len(matching_dependencies) / len(dcfinder_output)


def calculate_interestingness(dcfinder_output):
    print('calculate_interestingness')
    dependency_freq = {json.dumps(dep): dcfinder_output.count(
        dep) for dep in dcfinder_output}
    max_freq = max(dependency_freq.values())
    interestingness = {dep: freq / max_freq for dep,
                       freq in dependency_freq.items()}
    return interestingness


def load_multiple_json_objects(file):
    objects = []
    for line in file:
        try:
            obj = json.loads(line)
            objects.append(obj)
        except json.JSONDecodeError:
            continue
    return objects


def load_dataset_from_csv(file_path):
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        return list(reader)


def main():
    with open("output.json", "r") as file:
        dcfinder_output = load_multiple_json_objects(file)

    # Suposições para simplificar o exemplo:
    dataset = load_dataset_from_csv("dataset.csv")
    truth_standard = load_dataset_from_csv("dataset.csv")

    succinctness_values = calculate_succinctness(dcfinder_output)
    #coverage_value = calculate_coverage(dcfinder_output, dataset)
    degree_of_approximation_value = calculate_degree_of_approximation(
        dcfinder_output, truth_standard)
    interestingness_values = calculate_interestingness(dcfinder_output)

    # Criando uma lista de dicionários com todas as informações
    data_list = []
    for dependency, succinctness in zip(dcfinder_output, succinctness_values):
        predicate_form = dependency_to_predicate(dependency)
        interestingness_value = interestingness_values[json.dumps(dependency)]
        size = len(dependency['predicates'])

        data = {
            'predicate_form': predicate_form,
            'succinctness': succinctness,
            'degree_of_approximation': degree_of_approximation_value,
            'interestingness': interestingness_value,
            'size': size
        }
        data_list.append(data)

    # Ordenando a lista pelo tamanho do predicado do maior para o menor
    sorted_data_list = sorted(data_list, key=lambda x: x['size'], reverse=True)

    # Imprimindo a saída ordenada
    for data in sorted_data_list:
        print("Predicado:")
        print(data['predicate_form'])
        print(f"Succinctness: {data['succinctness']}")
        print(f"Degree of Approximation: {data['degree_of_approximation']}")
        print(f"Interestingness: {data['interestingness']}")
        print(f"Size: {data['size']}\n")


if __name__ == "__main__":
    main()
