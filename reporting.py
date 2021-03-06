"""
Makes possible reporter classes,
which are triggered on particular events and may provide information to the user,
may do something else such as checkpointing, or may do both.
"""
from __future__ import division, print_function

import time

from neat.math_util import mean, stdev, median
from neat.six_util import itervalues, iterkeys
from utility.mail import report
from utility.visualize import plot_species_stagnation, plot_fitness_over_gen
import os
# TODO: Add a curses-based reporter.


class ReporterSet(object):
    """
    Keeps track of the set of reporters
    and gives methods to dispatch them at appropriate points.
    """

    def __init__(self):
        self.reporters = []

    def add(self, reporter):
        self.reporters.append(reporter)

    def remove(self, reporter):
        self.reporters.remove(reporter)

    def start_generation(self, gen, config, population, species_set):
        for r in self.reporters:
            r.start_generation(gen, config, population, species_set)

    def end_generation(self, config, population, species_set):
        for r in self.reporters:
            r.end_generation(config, population, species_set)

    def post_evaluate(self, config, population, species, best_genome):
        for r in self.reporters:
            r.post_evaluate(config, population, species, best_genome)

    def post_reproduction(self, config, population, species):
        for r in self.reporters:
            r.post_reproduction(config, population, species)

    def complete_extinction(self):
        for r in self.reporters:
            r.complete_extinction()

    def found_solution(self, config, generation, best):
        for r in self.reporters:
            r.found_solution(config, generation, best)

    def species_stagnant(self, sid, species):
        for r in self.reporters:
            r.species_stagnant(sid, species)

    def info(self, msg):
        for r in self.reporters:
            r.info(msg)


class BaseReporter(object):
    """Definition of the reporter interface expected by ReporterSet."""

    def start_generation(self, generation, config, population, species_set):
        pass

    def end_generation(self, config, population, species_set):
        pass

    def post_evaluate(self, config, population, species, best_genome):
        pass

    def post_reproduction(self, config, population, species):
        pass

    def complete_extinction(self):
        pass

    def found_solution(self, config, generation, best):
        pass

    def species_stagnant(self, sid, species):
        pass

    def info(self, msg):
        pass


class StdOutReporter(BaseReporter):
    """Uses `print` to output information about the run; an example reporter class."""

    def __init__(self, show_species_detail):
        self.show_species_detail = show_species_detail
        self.generation = None
        self.generation_start_time = None
        self.generation_times = []
        self.num_extinctions = 0

    def start_generation(self, generation, config, population, species_set):
        self.generation = generation

        print('\n ****** Running generation {0} ****** \n'.format(generation))
        report('\n ****** Running generation {0} ****** \n'.format(generation))

        if not os.path.isfile('fitness_population') or generation == 0:
            with open('fitness_population', 'w') as f:
                pass

        with open('fitness_population', 'a') as f:
            f.write('{},'.format(generation))

        self.generation_start_time = time.time()

    def end_generation(self, config, population, species_set):
        body = []
        ng = len(population)
        ns = len(species_set.species)

        if self.show_species_detail:
            print(
                'Population of {0:d} members in {1:d} species:'.format(ng, ns))
            body.append(
                'Population of {0:d} members in {1:d} species:\n'.format(ng, ns))

            sids = list(iterkeys(species_set.species))
            sids.sort()

            print("   ID   age  size  fitness  adj fit  stag")
            print("  ====  ===  ====  =======  =======  ====")

            body.append("   ID   age  size  fitness  adj fit  stag\n")
            body.append("  ====  ===  ====  =======  =======  ====\n")

            for sid in sids:
                s = species_set.species[sid]
                a = self.generation - s.created
                n = len(s.members)
                f = "--" if s.fitness is None else "{:.1f}".format(s.fitness)
                af = "--" if s.adjusted_fitness is None else "{:.3f}".format(
                    s.adjusted_fitness)
                st = self.generation - s.last_improved
                print(
                    "  {: >4}  {: >3}  {: >4}  {: >7}  {: >7}  {: >4}".format(sid, a, n, f, af, st))
                body.append(
                    "  {: >4}  {: >3}  {: >4}  {: >7}  {: >7}  {: >4}\n".format(sid, a, n, f, af, st))
        else:
            print(
                'Population of {0:d} members in {1:d} species'.format(ng, ns))
            body.append(
                'Population of {0:d} members in {1:d} species\n'.format(ng, ns))

        elapsed = time.time() - self.generation_start_time
        self.generation_times.append(elapsed)
        self.generation_times = self.generation_times[-10:]
        average = sum(self.generation_times) / len(self.generation_times)

        print('Total extinctions: {0:d}'.format(self.num_extinctions))
        body.append('Total extinctions: {0:d}\n'.format(self.num_extinctions))

        if len(self.generation_times) > 1:
            print("Generation time: {0:.3f} sec ({1:.3f} average)".format(
                elapsed, average))
            body.append(
                "Generation time: {0:.3f} sec ({1:.3f} average)\n".format(elapsed, average))
        else:
            print("Generation time: {0:.3f} sec".format(elapsed))
            body.append("Generation time: {0:.3f} sec\n".format(elapsed))
        if body:
            img = plot_species_stagnation(body, 'species_plot.png')
            report(body, img)

    def post_evaluate(self, config, population, species, best_genome):
        body = []
        fitnesses = [c.fitness for c in itervalues(population)]
        fit_mean = mean(fitnesses)
        fit_std = stdev(fitnesses)
        fit_median = median(fitnesses)
        best_species_id = species.get_species_id(best_genome.key)

        with open('fitness_population', 'a') as f:
            f.write('{},{},{},{}\n'.format(
                fit_mean, fit_std, best_genome.fitness, fit_median))

        with open('fitness_generation_{}'.format(self.generation), 'a') as g:
            for c in itervalues(population):
                g.write('{0},{1},{2}\n'.format(
                    self.generation, c.key, c.fitness))

        print('Population\'s average fitness: {0:3.5f} stdev: {1:3.5f} median: {2:3.5f}'.format(
            fit_mean, fit_std, fit_median))

        print(
            'Best fitness: {0:3.5f} - complexity: {1!r} - species {2} - id {3}'.format(best_genome.fitness,
                                                                                       best_genome.size(),
                                                                                       best_species_id,
                                                                                       best_genome.key))
        body.append('Population\'s average fitness: {0:3.5f} stdev: {1:3.5f} median: {2:3.5f}\n'.format(
            fit_mean, fit_std, fit_median))
        body.append(
            'Best fitness: {0:3.5f} - complexity: {1!r} - species {2} - id {3}\n'.format(best_genome.fitness,
                                                                                         best_genome.size(),
                                                                                         best_species_id,
                                                                                         best_genome.key))
        if body:
            img = plot_fitness_over_gen(
                'fitness_population', 'fitness_population.png')
            report(body, img)

    def complete_extinction(self):
        self.num_extinctions += 1
        print('All species extinct.')

    def found_solution(self, config, generation, best):
        print('\nBest individual in generation {0} meets fitness threshold - complexity: {1!r}'.format(
            self.generation, best.size()))

    def species_stagnant(self, sid, species):
        if self.show_species_detail:
            print("\nSpecies {0} with {1} members is stagnated: removing it".format(
                sid, len(species.members)))
            report("\nSpecies {0} with {1} members is stagnated: removing it".format(
                sid, len(species.members)))

    def info(self, msg):
        print(msg)
