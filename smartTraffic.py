# smartTraffic.py
# Cyclists simulation
#
# author: Chu Luo
# date 2018, 06, 08

import numpy as np

import gpxpy
import gpxpy.gpx

class Road():
    # initialization function
    # constructed from GPS trace gpx file
    def __init__(self, end_point):
        # attributes
        # initial position is starting point
        self.end_point = end_point


class Cyclist():
    # initialization function
    def __init__(self, ID, speed, position, destination):
        # attributes
        self.ID = ID
        self.speed = speed
        # initial position is starting point
        # GPS is sampled per second
        self.position = position
        self.destination = destination
        self.travel_time = 0
        self.waiting_time = 0
        self.arrived = 0



class Traffic_Light():
    # initialization function
    def __init__(self, ID, position, state, timer):
        self.ID = ID
        self.position = position
        # state p stop = red, v cyclist go = green
        self.state = state
        # timer to count down, when 0 change
        self.timer = timer
        self.period = timer
        self.initiated = False
        self.transition = 0


    def change(self):
        if self.state == 'v':
            self.state = 'p'
        else:
            self.state = 'v'
        self.timer = self.period
        self.transition = self.transition + 1


class Simulator():
    # initialization function
    def __init__(self, ID, cyclist_number, light_number, policy, geof, interval, period):
        self.ID = ID
        self.road_length = 0
        self.cyclist_number = cyclist_number
        self.light_number = light_number
        self.geof = geof
        self.interval = interval
        self.policy =policy

        self.cyclist_list = []
        self.cyclist_list_by_speed = []
        self.light_list = []
        self.light_list_by_position = []
        self.arrived_cyclist = []

        self.period = period

        self.served = 0

    def run(self):
        # create a ROAD from GPX

        # user input 1: gpx file name

        file_name = 'gps.gpx'

        road_length = 0

        with open(file_name, 'r', encoding='UTF-8') as gpx_file:

            gpx = gpxpy.parse(gpx_file)

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        road_length = road_length + 1

        print("road length = ", road_length)
        self.road_length = road_length



        # normal distribution of speed with mean 1, variation = 0.16 (square sigma)

        # user input 2: sigma (optional)

        parameter_sigma = 0.4

        np.random.seed(seed=2)

        distribution1 = np.random.normal(1, parameter_sigma, self.cyclist_number * 2)

        cyclist_count = 0

        for i in distribution1:

            if cyclist_count < self.cyclist_number:

                if i>0.1:

                    cyclist_temp = Cyclist(cyclist_count, i, 0, self.road_length)

                    self.cyclist_list.append(cyclist_temp)

                    cyclist_count = cyclist_count + 1

            if self.cyclist_number == cyclist_count:
                break

        """
        for i in self.cyclist_list:
            print("---cyclist_list---")
            print(i.ID)
            print(i.speed)
            print(i.position)
        """

        # sort cyclist
        cyclist_list_by_speed = list(self.cyclist_list)

        cyclist_list_by_speed = sorted(cyclist_list_by_speed, key=lambda cyclist: cyclist.speed)

        """
        for i in cyclist_list_by_speed:
            print("---cyclist_list_by_speed---")
            print(i.ID)
            print(i.speed)
        """

        self.cyclist_list_by_speed = list(cyclist_list_by_speed)

        # create TRAFFIC LIGHTS

        # user input: period, how many seconds to change color
        period = self.period


        distribution1 = np.random.choice(self.road_length, self.road_length, replace=False)

        light_count = 0

        for i in distribution1:

            if self.road_length> i > self.geof:

                locus = int(round(i))

                # if not (int(round(i)) in self.light_list):

                # flag to add light to this locus
                flag = True

                # if two lights are far enough (geofences dont overlap)
                for j in self.light_list:

                    if abs(locus - j.position) < self.interval:

                        flag = False

                if flag:
                    light_temp = Traffic_Light(light_count, locus, 'p', period )

                    self.light_list.append(light_temp)

                    light_count = light_count + 1

            if self.light_number == light_count:
                break

        for i in self.light_list:
            print("---Traffic_Light---")
            print(i.ID)
            print(i.position)
            print(i.state)

        # sort traffic light
        light_list_by_position = list(self.light_list)

        light_list_by_position = sorted(light_list_by_position, key=lambda light: light.position)

        for i in light_list_by_position:
            print("---Traffic_Light_By_Position---")
            print(i.ID)
            print(i.position)
            print(i.state)

        self.light_list_by_position = list(light_list_by_position)


        # start moving loop
        #

        global_time = 0

        while len(self.arrived_cyclist)<self.cyclist_number:



            # input traffic light control

            # move each of cyclists
            # count metrics

            for i in self.cyclist_list_by_speed:

                if i.arrived == 1:
                    continue

                # find next light
                next_light = None
                flag_no_next_light = True
                for j in self.light_list_by_position:
                    if i.position < j.position:
                        next_light = j
                        flag_no_next_light = False
                        break

                if flag_no_next_light:
                    # not light
                    i.position = i.position + i.speed
                    # add travel time
                    i.travel_time = i.travel_time + 1

                # check next light, if not in range, move
                elif i.position + i.speed <= next_light.position:
                    # not in range, move
                    i.position = i.position + i.speed
                    # add travel time
                    i.travel_time = i.travel_time + 1
                else:
                    # in range, check color

                    if next_light.state == 'v':
                        i.position = i.position + i.speed
                        # add travel time
                        i.travel_time = i.travel_time + 1
                        # if cross a light, add one for total served
                        self.served = self.served + 1
                    else:
                        i.waiting_time = i.waiting_time + 1

                if i.position >= self.road_length:
                    i.arrived = 1
                    self.arrived_cyclist.append(i)

            # control light using policy

            # for each light

            for i in self.light_list_by_position:

                # 1st time, it is red forever, until policy
                if i.initiated == False:
                    # check policy

                    if self.policy == 1:

                        for j in self.cyclist_list_by_speed:

                            # j in i geof 1st slot
                            if  i.position - (self.geof * 2 /3 ) >= j.position >= i.position - self.geof:

                                i.initiated = True
                                i.change()

                    if self.policy == 2:

                        for j in self.cyclist_list_by_speed:

                            # j in i geof 1st slot
                            if i.position - (self.geof * 1 / 3) >= j.position >= i.position - (self.geof * 2 /3 ):
                                i.initiated = True
                                i.change()

                    if self.policy == 3:

                        for j in self.cyclist_list_by_speed:

                            # j in i geof 1st slot
                            if i.position  >= j.position >= i.position - (self.geof * 1 /3 ):
                                i.initiated = True
                                i.change()

                else:
                    #  15s loops of red-green
                    if i.timer == 0:
                        i.change()
                    else:
                        i.timer = i.timer - 1


            global_time = global_time + 1

            #print('clock = ', global_time)

        # count metrics

        travel_time = 0
        waiting_time = 0

        for i in self.cyclist_list_by_speed:
            travel_time = travel_time + i.travel_time
            waiting_time = waiting_time + i.waiting_time

        avg_waiting_time = waiting_time/self.cyclist_number
        print('WAT = ', avg_waiting_time)

        avg_speed = self.road_length * self.cyclist_number / (waiting_time + travel_time)
        print('AS = ', avg_speed)

        transitions = 0
        for i in self.light_list_by_position:
            transitions = transitions + i.transition

        NCS = self.served / transitions
        print('NCS = ', NCS)

        print('NTL = ', transitions)

        print('NTL is the sum of all lights')







# (ID, cyclist number, light number, policy number, geofence, interval, period)

# interval is min distance between lights

# period is how many seconds the light change between green and red

simulation1 = Simulator(1, 500, 10, 1, 15, 60, 15)
simulation1.run()


