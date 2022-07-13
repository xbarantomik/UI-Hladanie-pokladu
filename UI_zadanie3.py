import random
import copy
from configparser import ConfigParser
from timeit import default_timer as timer


#....list of constants.............................................................................
MAX_STEPS = 500
MEMORY_CELLS = 64

GENERATION_COUNT = 2000
INDIVIDUAL_COUNT = 100                   #min 30
INITIALIZED_MEMORY_CELLS = 32

MUTATION_RATE = 0.4                     #percenta
CROSSOVER_RATE = 0.4                    #percenta
RANDOM_RATE = 0.05                      #percenta
ELITISM = 4                             #cele cislo, max 4
# nech platí : MUTATION_RATE + RANDOM_RATE + CROSSOVER_RATE <= 0.85


#....map and treasures..............................................................................
treasures = []
map_x_len = 0
map_y_len = 0
map_x_start = 0
map_y_start = 0
treasure_number = 0

avegare_fitness = []
start_time = timer()


#....inicializacia mapy a pokladov.................................................................
def map_initialization():
        global treasures, map_x_len, map_y_len, map_x_start, map_y_start, treasure_number
        config = ConfigParser()
        config.read('map_and_treasures.ini')

        map_x_len = int(config['map']['x_len'])
        map_y_len = int(config['map']['y_len'])
        map_x_start = int(config['map']['x_start'])
        map_y_start = int(config['map']['y_start'])
        treasure_number = int(config['map']['treasure_num'])

        for p in range(treasure_number):
                x = int(config['T' + str(p + 1)]['x'])
                y = int(config['T' + str(p + 1)]['y'])
                treasures.append((x, y))


#....naplnanie buniek random hodnotami.............................................................
def make_random_instrucions(ini_memory_cells):
        instrucions = []
        for k in range(MEMORY_CELLS):
                instrucions.append(0)

        for m in range(ini_memory_cells):
                instrucions[m] = random.randint(0, 255)

        return instrucions


#....vytvorenie prvej generacie....................................................................
def create_first_generation():

        first_generation = {0: {'fitness': 0, 'instructions': [], 'path': [], 'treasure_path': [], 'found_treasures': []}}

        for n in range(INDIVIDUAL_COUNT):
                first_generation[n] = {}
                first_generation[n]['fitness'] = 0
                first_generation[n]['instructions'] = make_random_instrucions(INITIALIZED_MEMORY_CELLS)
                first_generation[n]['path'] = []
                first_generation[n]['treasure_path'] = []
                first_generation[n]['found_treasures'] = []

        return first_generation


#....skontroluje si MEMORY_CELLS sedi..............................................................
def check_position(num):
        if (num >= 0) and (num < MEMORY_CELLS):
                return True
        else:
                return False


#....zisit co kam sa bude mat pohnut...............................................................
def get_path_operator(instructions):
        #path = bin(instructions)[7:]
        path = bin(instructions)[2:].zfill(8)[6:]
        if path == '00':
                return 'H'
        elif path == '01':
                return 'D'
        elif path == '10':
                return 'L'
        elif path == '11':
                return 'P'


#....zistuje instrukcie a vykonava ich.............................................................
def virtual_machine(individual):

        step_count = 0
        cell_index = 0
        instructions_copy = individual['instructions'].copy()

        individual['path'] = []
        individual['treasure_path'] = []
        individual['found_treasures'] = []

        while check_position(cell_index) and step_count < MAX_STEPS:
                operator = (bin(instructions_copy[cell_index])[2:].zfill(8)[:2])
                address = int((bin(instructions_copy[cell_index])[2:].zfill(8)[2:]), 2)
                step_count += 1
                cell_index += 1

                # increment
                if operator == '00':
                        instructions_copy[address] += 1
                        if instructions_copy[address] == 256:
                                instructions_copy[address] = 0
                # decrement
                elif operator == '01':
                        instructions_copy[address] -= 1
                        if instructions_copy[address] == -1:
                                instructions_copy[address] = 255
                # jump
                elif operator == '10':
                        cell_index = address
                # write path
                elif operator == '11':
                        individual['path'].append(get_path_operator(instructions_copy[address]))

        # print("check")


#....zistuje ci nasiel nejake poklady..............................................................
def check_for_treasutes(individual, generation_count, individual_count):
        x_pos = map_x_start
        y_pos = map_y_start

        for s in individual['path']:
                if s == 'H':
                        y_pos -= 1
                elif s == 'D':
                        y_pos += 1
                elif s == 'L':
                        x_pos -= 1
                elif s == 'P':
                        x_pos += 1

                if x_pos < 0 or y_pos < 0 or x_pos >= map_x_len or y_pos >= map_y_len:
                        return

                for j in treasures:
                        if x_pos == j[0] and y_pos == j[1]:
                                if j not in individual['found_treasures']:
                                        individual['found_treasures'].append(j)

        #z path zapisem do treasure_path len po posledny najdeny poklad
        x_pos = map_x_start
        y_pos = map_y_start
        not_important = []
        for q in individual['path']:
                if len(individual['found_treasures']) == len(not_important):
                        break

                if q == 'H':
                        y_pos -= 1
                elif q == 'D':
                        y_pos += 1
                elif q == 'L':
                        x_pos -= 1
                elif q == 'P':
                        x_pos += 1

                if x_pos < 0 or y_pos < 0 or x_pos >= map_x_len or y_pos >= map_y_len:
                        return

                individual['treasure_path'].append(q)
                for w in treasures:
                        if x_pos == w[0] and y_pos == w[1]:
                                if w not in not_important:
                                        not_important.append(w)

        #kontrola ci nenasiel vsetky poklady
        if len(individual['found_treasures']) == treasure_number:
                end_with_all_treasures(individual, generation_count, individual_count)


#....vypocitanie fitness hodnoty...................................................................
def get_fitness(individual):
        individual["fitness"] = 0
        map_size = map_x_len * map_y_len
        treasures_count = len(individual['found_treasures'])
        path_len = len(individual['treasure_path'])
        path_map_ratio = path_len / map_size

        if path_len == 0:
                individual["fitness"] = 0
                return

        if treasures_count > 0:
                if path_map_ratio < 1:
                        individual["fitness"] = treasures_count + (1 - path_map_ratio)
                else:
                        while path_map_ratio >= 1:
                                path_map_ratio /= 10
                        individual["fitness"] = treasures_count + (path_map_ratio/10)

        elif treasures_count == 0:
                while path_map_ratio >= 1:
                        path_map_ratio /= 10
                individual["fitness"] = treasures_count + path_map_ratio

        #print(3)


#....vzoradi indexy jedincov podla fitness hodnoty zostupne........................................
def get_sorted_individuals(generation):
        global avegare_fitness
        fitness_sum = 0
        sorted_indexes = []

        sorted_dictionary_indexes = sorted(generation.items(), key=lambda k: k[True]['fitness'])
        #sorted_dictionary_indexes2 = OrderedDict(sorted(gen.items(), key=lambda x: getitem(x[True], 'fitness')))
        for u in range(len(sorted_dictionary_indexes)):
                sorted_indexes.append(sorted_dictionary_indexes[u][False])
        sorted_indexes.reverse()

        for i in range(INDIVIDUAL_COUNT):
                fitness_sum += generation[i]['fitness']
        avegare_fitness.append(round(fitness_sum/INDIVIDUAL_COUNT, 5))

        return sorted_indexes


#....vytvorenie novej generacie....................................................................
def create_new_generation(previous_generation, sorted_index):

        previous_gen = previous_generation.copy()
        new_generation = {0: {'fitness': 0, 'instructions': [], 'path': [], 'treasure_path': [], 'found_treasures': []}}

        mutation_r = round(INDIVIDUAL_COUNT * MUTATION_RATE)
        crossover_r = round(INDIVIDUAL_COUNT * CROSSOVER_RATE)
        random_r = round(INDIVIDUAL_COUNT * RANDOM_RATE)
        elitism = ELITISM
        rest = INDIVIDUAL_COUNT - (mutation_r + random_r + elitism + crossover_r)

        for i in range(elitism):
                new_generation[i] = {}
                new_generation[i] = previous_gen[sorted_index[i]]

        end = elitism + mutation_r
        for i in range(elitism, end):
                new_generation[i] = {}
                new_generation[i] = mutation(previous_gen)

        start = elitism + mutation_r
        end = elitism + mutation_r + crossover_r
        for i in range(start, end):
                parent_1 = roulette(previous_gen)
                parent_2 = roulette(previous_gen)
                while parent_1 == parent_2:
                        parent_2 = roulette(previous_gen)
                new_generation[i] = {}
                new_generation[i] = crossover(parent_1, parent_2)

        start = elitism + mutation_r + crossover_r
        end = start + random_r
        for i in range(start, end):
                new_generation[i] = {}
                new_generation[i] = make_new_individual(new_generation[i])

        start = elitism + mutation_r + crossover_r + random_r
        end = start + rest
        for i in range(start, end):
                new_generation[i] = {}
                new_generation[i] = previous_gen[random.randint(0, (INDIVIDUAL_COUNT - 1))]

        del parent_1, parent_2, previous_gen
        #print(2)
        return new_generation


#....krizenie......................................................................................
def crossover(parent1, parent2):
        new_instructions = []
        for i in range(MEMORY_CELLS):
                if i % 2 == 0:
                        new_instructions.append(parent1['instructions'][i])
                else:
                        new_instructions.append(parent2['instructions'][i])

        new_individual = {'fitness': 0, 'instructions': new_instructions, 'path': [], 'treasure_path': [], 'found_treasures': []}
        return new_individual


#....zmutuje jeden bit v bunke.....................................................................
def mutation(previous_gen):
        rand_individual = random.randint(0, (INDIVIDUAL_COUNT - 1))
        new_inidividual = copy.deepcopy(previous_gen[rand_individual])
        rand_cell = random.randint(0, (MEMORY_CELLS - 1))

        lucky_instruction = new_inidividual['instructions'][rand_cell]
        if lucky_instruction == 0:
                lucky_binlist = ['0', '0', '0', '0', '0', '0', '0', '0']
        else:
                lucky_binlist = [d for d in bin(lucky_instruction)[2:]]

        rand_inst_index = random.randint(0, len(lucky_binlist) - 1)
        if lucky_binlist[rand_inst_index] == '1':
                lucky_binlist[rand_inst_index] = '0'
        else:
                lucky_binlist[rand_inst_index] = '1'

        new_inidividual['instructions'][rand_cell] = int(''.join(lucky_binlist), 2)
        return new_inidividual


#....vyberie jedinca pomocou rulety................................................................
def roulette(previous_gen):
        fitness_sum = 0
        for i in range(len(previous_gen)):
                fitness_sum += previous_gen[i]['fitness']

        rand_num = random.uniform(0, fitness_sum)
        fitness_sum = 0
        for i in range(len(previous_gen)):
                fitness_sum += previous_gen[i]['fitness']
                if fitness_sum > rand_num:
                        return previous_gen[i]


#....vytvorenie noveho jedinca.....................................................................
def make_new_individual(individual):

        individual['fitness'] = 0
        individual['instructions'] = make_random_instrucions(MEMORY_CELLS)
        individual['path'] = []
        individual['treasure_path'] = []
        individual['found_treasures'] = []

        return individual


#....vypocita priemerny fitness....................................................................
def get_average_fitness():
        avg_sum = 0
        for i in range(GENERATION_COUNT):
                avg_sum += avegare_fitness[i]
        return str(round(avg_sum / GENERATION_COUNT, 4))


#....pri najdeni vsetktch pokladoch vypis .........................................................
def end_with_all_treasures(individual, generation_count, individual_count):
        get_fitness(individual)
        print("---------------------------------")
        print("All treasures were found!")
        print()
        print("Generation number: " + str(generation_count + 1))
        print("Individual number: " + str(individual_count + 1))
        print("Individual's fitness: " + str(round(individual['fitness'], 3)))
        end_time_t = timer()
        print("Time: " + str(round(end_time_t - start_time, 4)) + " seconds")
        print()
        print(f"Path to treasure: {len(individual['treasure_path'])}")
        for i in individual['treasure_path']:
                if i == "H":
                        print("Up", end=" ")
                if i == "L":
                        print("Left", end=" ")
                if i == "P":
                        print("Right", end=" ")
                if i == "D":
                        print("Down", end=" ")
        print()
        quit()


#....main..........................................................................................
if __name__ == "__main__":

        map_initialization()
        generation_now = create_first_generation()
        sorted_best_index = []
        for gens in range(GENERATION_COUNT):
                #print(gens)
                for indi in range(INDIVIDUAL_COUNT):
                        virtual_machine(generation_now[indi])
                        check_for_treasutes(generation_now[indi], gens, indi)
                        get_fitness(generation_now[indi])
                sorted_best_index = get_sorted_individuals(generation_now)
                if gens == (GENERATION_COUNT - 1):
                        break
                generation_now = create_new_generation(generation_now, sorted_best_index)

        print("---------------------------------------")
        print("All the treasures were NOT found")
        print()
        print("Avegare fitness: " + get_average_fitness())
        print("Best fitness in last generation: " + str(round(generation_now[sorted_best_index[0]]['fitness'], 4)))
        end_time = timer()
        print('Time: ' + str(round(end_time - start_time, 4)) + ' seconds')
        print()
