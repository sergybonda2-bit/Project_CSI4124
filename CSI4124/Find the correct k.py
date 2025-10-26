import numpy as np
import pandas as pd
from collections import deque
import random
import pandas as pd
random.seed(25)
pd.set_option('display.max_columns', None)  # Show all columns
# Set it to None to display all columns in the dataframe
pd.set_option('display.max_columns', None) #the default value is 4 column max
# Width of the display in characters. If set to None and pandas will correctly auto-detect the width.
pd.set_option('display.width', None) #https://python.19633.com/fr/python-tag-1/Pandas-1/1001005959.html

#Customer class, essential property customer_id and server_id
class Customer :
    def __init__ (self, customer_id, server_id=None) :
        self._customer_id = customer_id
        self._server_id= None
        self._waiting_time = None
        self._start_service = None
        self._time_in_system = None
        self._departure_time = None
        self._arrival_time = None
        self._service_time = None
        self._interArrival_time = None

    @property
    def customer_id (self) :
        return self._customer_id
    @customer_id.setter
    def customer_id (self, value) :
        self._customer_id = value

    @property
    def server_id(self):
        return self._server_id
    @server_id.setter
    def server_id(self, value):
        self._server_id = value

    @property
    def waiting_time(self):
        return self._waiting_time
    @waiting_time.setter
    def waiting_time (self, value):
        self._waiting_time = value

    @property
    def start_service(self):
        return self._start_service
    @start_service.setter
    def start_service (self, value):
        self._start_service = value

    @property
    def time_in_system(self):
        return self._time_in_system
    @time_in_system.setter
    def time_in_system (self, value):
        self._time_in_system = value

    @property
    def departure_time(self):
        return self._departure_time
    @departure_time.setter
    def departure_time(self, value):
        self._departure_time = value

    @property
    def arrival_time(self):
        return self._arrival_time
    @arrival_time.setter
    def arrival_time(self, value):
        self._arrival_time = value

    @property
    def service_time(self):
        return self._service_time
    @service_time.setter
    def service_time(self, value):
        self._service_time = value

    @property
    def interArrival_time(self):
        return self._interArrival_time
    @interArrival_time.setter
    def interArrival_time(self, value):
        self._interArrival_time = value
   # def __repr__(self):
       # return f"{self.eventype} {self.time} "

# model input
lambda_rate = 4.0   # Taux d'arrivée
mu_rate = 1.0       # Taux de service

k_servers = 1     # server number
simulation_time = 100.0 # simulation Time
busy_time = 0

def simulation (lambda_rate, mu_rate, k_servers, simulation_time) :
    # Types d'événements
    ARRIVAL = "ARRIVAL"
    DEPARTURE = "DEPARTURE"

    fel = []  # Future Event List

    # État du système
    queue = []
    servers = [None] * k_servers  # None = libre, sinon contient customer_id, syntax create a table of none k_server times

    simulation_time_Clock = 0.0

    # Statistiques par client/contains all the customers instance
    customers = []

    # initialisation
    # fel.append((simulation_time_Clock+30,ARRIVAL,Customer(1)))
    # fel.append((simulation_time_Clock+10,ARRIVAL,Customer(1)))
    # fel.append((simulation_time_Clock+2,ARRIVAL,Customer(1)))
    # fel = sorted(fel, key=lambda p: p[0])#trie par rapport a chaque position 0 qui est le temps des dictionnaires
    # print(fel)
    def exponential(rate):
        return random.expovariate(rate)

    def find_free_server():  # find free server
        for i in range(k_servers):
            if servers[i] is None:
                return i
        return None

    # initialisation
    customers.append(Customer(0))
    customers[0].interArrival_time = 0
    fel.append((simulation_time_Clock, ARRIVAL, customers[0]))

    while simulation_time_Clock < simulation_time:
        fel = sorted(fel, key=lambda p: p[0])  # sort to take the imminent event
        evt = fel.pop(0)  # retrieve the event with the less time and rid it off
        evt_type = evt[1]  # extract the event
        customer = evt[-1]  # extract customer
        customer_id = customer.customer_id  # set arrival for next customer in arrival
        server_id = customer.server_id  # specify to the next customer the server newly idle is available to take, or specify that the current customer as the server is idle want the departure on it
        simulation_time_Clock = evt[0]  # extract the clock
        if (evt_type == ARRIVAL):
            customer.arrival_time = simulation_time_Clock
            customers.append(Customer(customer_id + 1))  # prepare next arrival
            interArrival = exponential(lambda_rate)
            next_arrival = simulation_time_Clock + interArrival  # next arrival
            if next_arrival < simulation_time:
                customers[customer_id + 1].interArrival_time = interArrival
                customers[customer_id + 1].arrival_time = next_arrival  # set the arrival of the next customer
                fel.append((next_arrival, ARRIVAL, customers[customer_id + 1]))  # schedule his arrival with the fel

            server_id = find_free_server()  # because we have k server, we looking if some one is free, otherwise the customer go in queue
            if server_id is not None:
                servers[server_id] = customer_id  # the customer take the i server idle
                service_time = exponential(mu_rate)
                customer.start_service = simulation_time_Clock
                customer.waiting_time = 0.0
                customer.service_time = service_time
                customer.server_id = server_id
                fel.append((simulation_time_Clock + service_time, DEPARTURE, customers[customer_id]))
            else:
                queue.append(customer)

        elif evt_type == DEPARTURE:
            customer.departure_time = simulation_time_Clock  # set departure time of the customer
            customer.time_in_system = customer.departure_time - customer.arrival_time  # set time in system
            servers[customer.server_id] = None  # release the server
            current_server_released_id = customer.server_id
            if len(queue) > 0:  # prepare the next old customer in queue to come into the server newly idle
                next_idCustomer = queue.pop(0).customer_id  # get out from the queue
                service_time = exponential(mu_rate)
                for i in customers:  # schedule next depature
                    if i.customer_id == next_idCustomer:
                        servers[current_server_released_id] = i.customer_id  # the next customer take the server
                        i.start_service = simulation_time_Clock
                        i.service_time = service_time
                        i.waiting_time = simulation_time_Clock - i.arrival_time
                        i.server_id = current_server_released_id
                        fel.append((simulation_time_Clock + service_time, DEPARTURE, i))
    # load data into a DataFrame object:
    data = {
        "Customer_id": [customer.customer_id for customer in customers if customer.departure_time != None],
        "Arrival": [customer.arrival_time for customer in customers if customer.departure_time != None],
        # create a list of arrival time
        "interarrival": [customer.interArrival_time for customer in customers if customer.departure_time != None],
        "Start_service_time": [customer.start_service for customer in customers if customer.departure_time != None],
        "Service_time": [customer.service_time for customer in customers if customer.departure_time != None],
        "Departure_Time": [customer.departure_time for customer in customers if customer.departure_time != None],
        "Time in systeme": [customer.time_in_system for customer in customers if customer.departure_time != None],
        "Server Id": [customer.server_id for customer in customers if customer.departure_time != None]
    }
    df = pd.DataFrame(data)
    # df['waiting time'] = df['departure'] - df['Service_time'] - df['Arrival'] # wi = di - si - ai create new row
    # df.round()
    df.set_index("Customer_id", inplace=True)  # https://www.geeksforgeeks.org/pandas/python-pandas-dataframe-set_index/
    print(df)
    service_times = [i.service_time for i in customers if i.departure_time != None ]
    somme = 0.0
    for time in service_times:
        somme = somme + time
    busy_time = somme / (simulation_time * k_servers)
    print(f"  busy time in system   : {busy_time:.2f}")
    print(f"  the value of current K is   : {k_servers:.2f}")
    return busy_time

#test
while busy_time <= 0.6 or busy_time >= 0.8 : #find the perfect value of the number for the busy time between 0.6-0.8
    busy_time = simulation(lambda_rate, mu_rate, k_servers, simulation_time)
    k_servers = k_servers + 1
#print(f"  final value of server number is   : {k_servers:.2f}")



