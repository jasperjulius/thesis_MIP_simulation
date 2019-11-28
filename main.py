import simulation

sim = simulation.Simulation(length=10, stock=101, stochastic=True)
sim.run(FIFO=False)
