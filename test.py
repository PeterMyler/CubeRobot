import random
import serial  # to communicate with arduino
# import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from cubescrambler import scrambler333  # to get a random scramble
from time import process_time

mc = magiccube.Cube(3)
print(mc)