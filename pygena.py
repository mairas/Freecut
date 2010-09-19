#! /usr/bin/python

# Genetic algorithm library for Python

# Original inspiration taken from the ActiveState Python Cookbook 
# Recipe 199121

# Copyright (c) 2003 Sean Ross
# Copyright (c) 2007-2010 Matti Airas

# Licensed under the PSF License

import random as r
from copy import deepcopy

MAXIMIZE, MINIMIZE = 11, 22

# generic base chromosome class

class BaseChromosome(object):
    optimization = MINIMIZE
    length = None # redefine in a subclass!

    def __init__(self):
        self.score = None  # set during evaluation

    def randomize(self):
        raise NotImplementedError

    def crossover(self,other):
        raise NotImplementedError

    def mutate(self,mutationRate):
        raise NotImplementedError

    def repair(self):
        raise NotImplementedError

    def evaluate(self):
        raise NotImplementedError

    def asString(self):
        raise NotImplementedError

    def __repr__(self):
        "returns string representation of self"
        return '<%s chromosome="%s" score=%s>' % \
               (self.__class__.__name__,
                self.asString(), self.score)

    def __cmp__(self, other):
        if self.optimization == MINIMIZE:
            return cmp(self.score, other.score)
        else: # MAXIMIZE
            return cmp(other.score, self.score)

    # broken!
    #def copy(self):
    #    twin = self.__class__(self.chromosome[:])
    #    return twin


def simple_tournament(population, size=8, choosebest=0.90):
    #competitors = [r.choice(population) for i in range(size)]
    competitiors = r.sample(population,size)
    competitors.sort()
    if r.random() < choosebest:
        return competitors[0]
    else:
        return r.choice(competitors[1:])
    
def roulette_tournament(population):
    if population[0].optimization==MAXIMIZE:
        transform = lambda x: x**2
    else:
        transform = lambda x: 1/(x+1e-10)
    tot = sum([transform(p.score) for p in population])
    rnd = tot*r.random()

    i = 0
    cums = transform(population[i].score)
    while rnd>cums:
        cums += transform(population[i].score)
        i += 1
    return population[i]

def default_report(self):
    print "="*70
    print "generation:   ", self.generation
    print "pop size:     ", len(self.population)
    #for p in self.population:
    #    print p
    print "median score: ", median([c.score for c in self.population])
    print "best:         ", self.best()


class Population(object):
    def __init__(self, kind, population=None, size=100, maxgenerations=100, 
                 maxplateau=10,
                 crossover_rate=0.70, mutation_rate=0.01,
                 tournament=simple_tournament, elitism=True, optimum=None,
                 report_callback=default_report):
        self.kind = kind
        self.size = size
        self.optimum = optimum
        if population:
            self.population = population
        else:
            self.population = self.make_population()
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.maxgenerations = maxgenerations
        self.maxplateau = maxplateau
        self.generation = 0
        self.prev_improvement_gen = 0
        self.prev_score = None
        self.elitism=elitism
        self.tournament = tournament
        self.report_callback = report_callback
        self.population.sort()


    def make_population(self):
        pop = []
        for i in range(self.size):
            ch = self.kind()
            pop.append(ch)
        return pop
    
    def run(self):
        best = None
        sign = (-1,1)[self.population[0].optimization==MAXIMIZE]
        while not self.goal():
            self.step()
            if best is not None:
                if sign*best.score<sign*self.best().score:
                    best = self.best()
            else:
                best = self.best()
        self.report()
        return best
    
    def goal(self):
        sign = (-1,1)[self.population[0].optimization==MAXIMIZE]
        if self.prev_score is None:
            self.prev_score = sign*self.best().score
        if self.maxplateau:
            if sign*self.best().score > self.prev_score:
                self.prev_score = sign*self.best().score
                self.prev_improvement_gen = self.generation
            elif self.generation >= \
                     self.prev_improvement_gen + self.maxplateau:
                return True

        return self.generation >= self.maxgenerations or \
               self.best().score == self.optimum
    
    def step(self):
        self.report()
        self.crossover()
        self.population.sort()
        self.generation += 1
    
    def crossover(self):
        next_population = []
        if self.elitism==True:
            for i in range(5):
                next_population.append(deepcopy(self.population[i]))
        while len(next_population) < self.size:
            mate1 = self.tournament(self.population)
            if r.random() < self.crossover_rate:
                mate2 = self.tournament(self.population)
                offspring = mate1.crossover(mate2)
            else:
                offspring = [deepcopy(mate1)]
            for individual in offspring:
                individual.mutate(self.mutation_rate)
                next_population.append(individual)
        self.population = next_population[:self.size]
        
    def best(self):
        "individual with best fitness score in population."
        return self.population[0]

    def report(self):
        self.report_callback(self)


def median(numbers):
    "Return the median of the list of numbers."
    # Sort the list and take the middle element.
    n = len(numbers)
    copy = numbers[:] # So that "numbers" keeps its original order
    copy.sort()
    if n & 1:         # There is an odd number of elements
        return copy[n // 2]
    else:
        return (copy[n // 2 - 1] + copy[n // 2]) / 2
    
