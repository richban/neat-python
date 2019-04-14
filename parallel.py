"""
Runs evaluation functions in parallel subprocesses
in order to evaluate multiple genomes at once.
"""
from multiprocessing import Pool
import math
import itertools


class ParallelEvaluator(object):
    def __init__(self, num_workers, eval_function, clients, settings, timeout=None):
        """
        eval_function should take one argument, a tuple of
        (genome object, config object), and return
        a single float (the genome's fitness).
        """
        self.num_workers = num_workers
        self.eval_function = eval_function
        self.timeout = timeout
        self.clients = clients
        self.settings = settings
        self.pool = Pool(num_workers)
        self.chunks = None

    def __del__(self):
        self.pool.close()  # should this be terminate?
        self.pool.join()

    def _chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def evaluate(self, genomes, config):

        jobs = []
        self.chunks = list(self._chunks(
            genomes, math.floor(len(genomes)/self.num_workers)))

        for i in self.clients:
            jobs.append(self.pool.apply_async(
                self.eval_function, (self.clients[i], self.settings, self.chunks[i], config)))
        self.pool.close()
        self.pool.join()
        # assign the fitness back to each genome
        for job in jobs:
            genomes = list(itertools.chain(job.get(timeout=self.timeout)))
