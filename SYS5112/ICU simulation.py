import numpy as np
import pandas as pd
import matplotlib.pyplot as plt1
import matplotlib.pyplot as plt2

import random
from collections import deque

random.seed(25)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Define patient classes (severity × LoS group)
patient_classes = {
    1: {"severity": 1, "los_group": 1, "mu": (3.0, 0.5)},
    2: {"severity": 1, "los_group": 2, "mu": (3.2, 0.6)},
    3: {"severity": 1, "los_group": 3, "mu": (3.3, 0.6)},
    4: {"severity": 2, "los_group": 1, "mu": (3.6, 0.7)},
    5: {"severity": 2, "los_group": 2, "mu": (3.7, 0.7)},
    6: {"severity": 2, "los_group": 3, "mu": (3.5, 0.6)},
    7: {"severity": 3, "los_group": 1, "mu": (5.0, 0.8)},
    8: {"severity": 3, "los_group": 2, "mu": (5.1, 0.9)},
    9: {"severity": 3, "los_group": 3, "mu": (4.8, 0.7)},
}

def sample_service_time(class_id):
    mu, sigma = patient_classes[class_id]["mu"]
    return np.random.lognormal(mean=mu, sigma=sigma)

def exponential(rate):
    return random.expovariate(rate)

class Customer:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.class_id = random.randint(1, 9)
        self.server_id = None
        self.waiting_time = None
        self.start_service = None
        self.time_in_system = None
        self.departure_time = None
        self.arrival_time = None
        self.service_time = None
        self.interArrival_time = None

# Simulation parameters
lambda_rate = 4.0
k_servers = 6
simulation_time = 1000
ARRIVAL = "ARRIVAL"
DEPARTURE = "DEPARTURE"

# State
fel = []
queue = []
servers = [None] * k_servers
simulation_time_Clock = 0.0
customers = []

# Priority sort (severity descending, LoS ascending)
def priority_sort(queue):
    return sorted(queue, key=lambda c: (-patient_classes[c.class_id]["severity"], patient_classes[c.class_id]["mu"][0]))

# Optional dynamic priority (commented)
# def dynamic_priority(customer, current_time, alpha=0.1):
#     severity_weight = patient_classes[customer.class_id]["severity"]
#     waiting_time = current_time - customer.arrival_time
#     return severity_weight + alpha * waiting_time

def find_free_server():
    for i in range(k_servers):
        if servers[i] is None:
            return i
    return None

def compute_readmission_load(customer, current_time):
    remaining_los = customer.service_time - (current_time - customer.start_service)
    return_rate = 0.1
    return_los = 40.0
    return remaining_los + return_rate * return_los

def attempt_bump(new_customer, current_time):
    if patient_classes[new_customer.class_id]["severity"] < 3:
        return False
    candidates = [c for c in customers if c.server_id is not None and patient_classes[c.class_id]["severity"] < 3]
    if not candidates:
        return False
    bumped = min(candidates, key=lambda c: compute_readmission_load(c, current_time))
    servers[bumped.server_id] = new_customer.customer_id
    new_customer.server_id = bumped.server_id
    new_customer.start_service = current_time
    new_customer.waiting_time = 0.0
    new_customer.service_time = sample_service_time(new_customer.class_id)
    fel.append((current_time + new_customer.service_time, DEPARTURE, new_customer))
    bumped.departure_time = current_time
    bumped.time_in_system = bumped.departure_time - bumped.arrival_time
    return True

# Initialize first arrival
customers.append(Customer(0))
customers[0].interArrival_time = 0
fel.append((simulation_time_Clock, ARRIVAL, customers[0]))

while simulation_time_Clock < simulation_time:
    fel = sorted(fel, key=lambda p: p[0])
    evt = fel.pop(0)
    evt_type = evt[1]
    customer = evt[-1]
    customer_id = customer.customer_id
    simulation_time_Clock = evt[0]

    if evt_type == ARRIVAL:
        customer.arrival_time = simulation_time_Clock
        customers.append(Customer(customer_id + 1))
        interArrival = exponential(lambda_rate)
        next_arrival = simulation_time_Clock + interArrival
        if next_arrival < simulation_time:
            customers[customer_id + 1].interArrival_time = interArrival
            customers[customer_id + 1].arrival_time = next_arrival
            fel.append((next_arrival, ARRIVAL, customers[customer_id + 1]))

        server_id = find_free_server()
        if server_id is not None:
            servers[server_id] = customer_id
            service_time = sample_service_time(customer.class_id)
            customer.start_service = simulation_time_Clock
            customer.waiting_time = 0.0
            customer.service_time = service_time
            customer.server_id = server_id
            fel.append((simulation_time_Clock + service_time, DEPARTURE, customer))
        else:
            if not attempt_bump(customer, simulation_time_Clock):
                queue.append(customer)

    elif evt_type == DEPARTURE:
        customer.departure_time = simulation_time_Clock
        customer.time_in_system = customer.departure_time - customer.arrival_time
        servers[customer.server_id] = None
        current_server_released_id = customer.server_id
        if len(queue) > 0:
            queue = priority_sort(queue)
            next_idCustomer = queue.pop(0).customer_id
            for i in customers:
                if i.customer_id == next_idCustomer:
                    service_time = sample_service_time(i.class_id)
                    servers[current_server_released_id] = i.customer_id
                    i.start_service = simulation_time_Clock
                    i.service_time = service_time
                    i.waiting_time = simulation_time_Clock - i.arrival_time
                    i.server_id = current_server_released_id
                    fel.append((simulation_time_Clock + service_time, DEPARTURE, i))

# DataFrame
data = {
    "Customer_id": [c.customer_id for c in customers if c.departure_time is not None],
    "Arrival": [c.arrival_time for c in customers if c.departure_time is not None],
    "Interarrival": [c.interArrival_time for c in customers if c.departure_time is not None],
    "Start_service": [c.start_service for c in customers if c.departure_time is not None],
    "Service_time": [c.service_time for c in customers if c.departure_time is not None],
    "Departure": [c.departure_time for c in customers if c.departure_time is not None],
    "Time_in_system": [c.time_in_system for c in customers if c.departure_time is not None],
    "Waiting_time": [c.waiting_time for c in customers if c.departure_time is not None],
    "Server_id": [c.server_id for c in customers if c.departure_time is not None],
    "Class_id": [c.class_id for c in customers if c.departure_time is not None],
    "Severity": [patient_classes[c.class_id]["severity"] for c in customers if c.departure_time is not None]
}
df = pd.DataFrame(data)
df.set_index("Customer_id", inplace=True)
print(df.round(2))
service_times = [i.service_time for i in customers if i.departure_time != None ]
somme = 0.0
for time in service_times:
    somme = somme + time
busy_time = somme / (simulation_time * k_servers)
waiting_times = [i.waiting_time for i in customers if i.departure_time != None ]
somme = 0.0
for time in waiting_times:
    somme = somme + time
mean_waiting = somme / len(waiting_times)
print(f"  busy time in system by simulation  : {busy_time:.2f}")
print(f"  the value of current K is   : {k_servers:.2f}")
print(f"  the mean waiting by simulation   : {mean_waiting:.2f}")
print(f"  the simulation time   : {simulation_time:.2f}")


# Performance metrics
def compute_performance_metrics(df, simulation_time, k_servers):
    n_bar = df["Time_in_system"].sum() / simulation_time
    U = df["Service_time"].sum() / simulation_time
    λ = len(df) / simulation_time
    W = n_bar / λ if λ > 0 else 0
    Q = W - (U / λ) if λ > 0 else 0

    print("\n--- Performance Metrics by closed form (formulars)---")
    print(f"Mean number in system (n̄): {n_bar:.2f}")
    print(f"Server utilization (U): {U:.2f}")
    print(f"Throughput (λ): {λ:.2f}")
    print(f"Mean response time (W): {W:.2f}")
    print(f"Mean waiting time (Q): {Q:.2f}")

compute_performance_metrics(df, simulation_time, k_servers)

# Waiting time histogram
waiting_times = [c.waiting_time for c in customers if c.departure_time is not None]
plt1.figure(figsize=(10, 5))
plt1.hist(waiting_times,bins = 20, color='skyblue', edgecolor='black')
plt1.title('Waiting Time Distribution')
plt1.xlabel('Waiting Time (Hour)')
plt1.ylabel('Number of Patients')
plt1.grid(True)
plt1.show()
# Visualization
