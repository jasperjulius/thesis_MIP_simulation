import simulation

sim = simulation.Simulation(length=100, stock=100, stochastic=True)
sim.run(FIFO=False)
results_mip = sim.collect_statistics()
sim.reset()
sim.run(FIFO=True)
results_fifo = sim.collect_statistics()
print("mip:  ", results_mip)
print("fifo: ", results_fifo)
results_difference = []  # mip - fifo

for i, j in zip(results_mip, results_fifo):
    temp = []
    for r in range(len(i)):
        temp.append(i[r]-j[r])
    results_difference.append(temp)


print("difference: ", results_difference)
