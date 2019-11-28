import simulation

sim = simulation.Simulation(length=10, stock=101, stochastic=True)
sim.run(FIFO=False)
print(sim.collect_statistics())
sim.reset()
sim.run(FIFO=True)
print(sim.collect_statistics())
