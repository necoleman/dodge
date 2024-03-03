from pyglet import shapes
import numpy as np

from abc import ABC, abstractmethod
from typing import List

import logging 

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("dodge")


class CelestialObject:

    # properties

    # location

    # velocity

    def __init__(self, x, y, vx, vy, m):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.m = m


    def update(self, dt, accel_x=0, accel_y=0):
        self.x = self.x + dt * self.vx 
        self.y = self.y + dt * self.vy
        self.vx = self.vx + dt * accel_x
        self.vy = self.vy + dt * accel_y

    def handle_collision(self, vector_to_line_x, vector_to_line_y):
        """Update physics to handle a collision with a given line

        Does the following:
            - Teleport self to the nearest point on the line:
            - Reflect velocity about the line

        NB the teleportation avoids numerical instability

        Args:
            normal_vector_to_line_x: x component of the normal vector from the ship to the line
            normal_vector_to_line_y: y component of the normal vector from the object to the line
        """

        log.debug("Handling collision, vector to collision location: (%s, %s)", vector_to_line_x, vector_to_line_y)
        log.debug("Current location: (%s, %s)", self.x, self.y)
        log.debug("Current velocity: (%s, %s)", self.vx, self.vy)

        self.x = self.x + vector_to_line_x 
        self.y = self.y + vector_to_line_y 

        dist_squared = vector_to_line_x**2 + vector_to_line_y**2

        # component of velocity parallel to line: v_parallel = < v, r > r / |r|^2 
        # component of velocity perp to line: v_perp = v - v_par 

        v_parallel_x = (self.vx * vector_to_line_x + self.vy * vector_to_line_y ) * vector_to_line_x / dist_squared
        v_parallel_y = (self.vx * vector_to_line_x + self.vy * vector_to_line_y ) * vector_to_line_y / dist_squared
        v_perp_x = self.vx - v_parallel_x
        v_perp_y = self.vy - v_parallel_y 

        # on collision, v_par --> v_par and v_perp --> -v_perp
        self.vx = - v_parallel_x + v_perp_x 
        self.vy = - v_parallel_y + v_perp_y

        log.debug("New location: (%s, %s)", self.x, self.y)
        log.debug("New velocity: (%s, %s)", self.vx, self.vy)


class Ship(CelestialObject):

    # lines
    poly: shapes.Polygon
    rotation: float # ship orientation in degrees

    # rocket is firing
    rocket: bool
    plume: shapes.Polygon
    fuel: float

    max_fuel: float
    fuel_gauge_height: float 


    def __init__(self, x, y, vx, vy, fuel_gauge_x, fuel_gauge_min_y, fuel_gauge_max_y, fuel_gauge_width, batch ):

        super().__init__(x, y, vx, vy, m=10)

        self.fuel = 10
        self.max_fuel = 10

        self.poly = shapes.Polygon(
            (self.x, self.y),
            (self.x - 4, self.y - 5),
            (self.x + 8, self.y),
            (self.x - 4, self.y + 5),
            color=(255, 255, 255, 255),
            batch=batch
        )

        self.rocket = False
        self.plume = shapes.Polygon(
                (self.x, self.y),
                (self.x-20, self.y+3),
                (self.x-5, self.y),
                (self.x-20, self.y),
                (self.x-5, self.y),
                (self.x-20, self.y-3),
                color=(255,255,255,255),
                batch=batch
            )
        self.plume.visible = False
        self.rotation = 0

        self.fuel_gauge = shapes.Line(
            x=fuel_gauge_x,
            y=fuel_gauge_min_y,
            x2=fuel_gauge_x,
            y2=fuel_gauge_max_y,
            width=fuel_gauge_width,
            color=(255,255,255,255),
            batch=batch
        )
        self.fuel_gauge_height = fuel_gauge_max_y - fuel_gauge_min_y


    def start_accel(self):
        log.debug("Accelerating")
        self.rocket = True 
        self.plume.visible = True
        self.plume.rotation = self.poly.rotation


    def stop_accel(self):
        log.debug("Ceasing acceleration")
        self.rocket = False
        self.plume.visible = False


    def angle(self, th):
        self.rotation = th
        self.poly.rotation = th
        self.plume.rotation = th


    def update(self, dt, accel_x, accel_y):
        rocket_accel_x = 0
        rocket_accel_y = 0
        if self.rocket and self.fuel > 0:
            rocket_accel_x = 50 * np.cos( np.pi * self.rotation / 180 )
            rocket_accel_y = -50 * np.sin( np.pi * self.rotation / 180 ) # idk why the minus sign, maybe selfrotation is backward?
            log.debug("Rocket acceleration: (%s, %s)", rocket_accel_x, rocket_accel_y)
            self.fuel = max( 0, self.fuel - dt * 0.5 )
            self.fuel_gauge.y2 = self.fuel * self.fuel_gauge_height / self.max_fuel
        full_accel_x = accel_x + rocket_accel_x
        full_accel_y = accel_y + rocket_accel_y
        super().update(dt, accel_x=full_accel_x, accel_y=full_accel_y)
        self.poly.position = self.x, self.y 
        self.plume.position = self.x, self.y


class Planet(CelestialObject):

    # poly
    radius: float 

    def __init__(self, x, y, m, r, batch):
        super().__init__(x=x, y=y, vx=0, vy=0, m=m)
        self.radius = r
        
        self.circle = shapes.Circle(
            x=self.x,
            y=self.y,
            radius=self.radius,
            color=(255,255,255,255),
            batch=batch
        )

    def collision(self, x, y):
        """Check whether a collision has occurred
        """
        displ_x = (x - self.x)
        displ_y = (y - self.y)
        dist = np.sqrt( displ_x**2 + displ_y**2 )
        return dist < self.radius

    def vector_to_collision_from(self, x, y):
        """Vector from (x,y) to the point of collision at the planet surface
        """
        displ_x = (self.x - x)
        displ_y = (self.y - y)
        dist = np.sqrt( displ_x**2 + displ_y**2 )
        vector_to_line_x = (dist - self.radius) * displ_x / dist
        vector_to_line_y = (dist - self.radius) * displ_y / dist
        return vector_to_line_x, vector_to_line_y

    def gravity_at(self, x, y, G=1):
        displ_x = (x - self.x)
        displ_y = (y - self.y)
        dist_squared = (x - self.x)**2 + (y - self.y)**2
        accel_x = - displ_x * G * self.m / dist_squared**(3/2)
        accel_y = - displ_y * G * self.m / dist_squared**(3/2)
        return accel_x, accel_y


class GameState:
    """Everything
    """

    planets: List[CelestialObject]
    ship: Ship

    # where the mouse is
    point_to_x: float 
    point_to_y: float 

    # physics
    G = 1000

    # gui
    max_x: int 
    max_y: int

    # number of collisions
    num_collisions = 0

    def __init__(self, max_x, max_y, batch, num_planets=1):
        self.ship = Ship(x=250, 
                        y=500,
                        vx=0, 
                        vy=0, 
                        fuel_gauge_x=max_x*0.9, 
                        fuel_gauge_max_y=max_y*0.9,
                        fuel_gauge_min_y=max_y*0.1, 
                        fuel_gauge_width=10,
                        batch=batch)
        self.planets = [ Planet(x=500, y=600, m=100, r=20, batch=batch) ]
        # while len(self.planets) < num_planets:
        #     self.add_planet(batch)
        self.point_to_x = 0
        self.point_to_y = 0
        self.max_x = max_x 
        self.max_y = max_y

    def add_planet(self, batch):
        """Add a planet that is not too close to any existing one
        """
        # random x
        # random y
        # random m
        # random r

        return 

    def check_for_collisions(self):
        obj = self.ship
        if obj.x > self.max_x:
            log.debug("Collided with wall at location (%s, %s)", obj.x, obj.y)
            obj.handle_collision(vector_to_line_x=(self.max_x-obj.x), vector_to_line_y=0)
        if obj.x < 0:
            log.debug("Collided with wall at location (%s, %s)", obj.x, obj.y)
            obj.handle_collision(vector_to_line_x=-obj.x, vector_to_line_y=0)
        if obj.y > self.max_y:
            log.debug("Collided with wall at location (%s, %s)", obj.x, obj.y)
            obj.handle_collision(vector_to_line_x=0, vector_to_line_y=(self.max_y-obj.y))
        if obj.y < 0:
            log.debug("Collided with wall at location (%s, %s)", obj.x, obj.y)
            obj.handle_collision(vector_to_line_x=0, vector_to_line_y=-obj.y)

        for planet in self.planets:
            if planet.collision(obj.x, obj.y):
                self.num_collisions += 1
                vector_to_line_x, vector_to_line_y = planet.vector_to_collision_from(obj.x, obj.y)
                obj.handle_collision(vector_to_line_x, vector_to_line_y)


    def accel_on_ship(self):
        accel_x = 0
        accel_y = 0
        for planet in self.planets:
            a_x, a_y = planet.gravity_at(self.ship.x, self.ship.y, G=self.G)
            accel_x += a_x
            accel_y += a_y
        # log.debug("Accel on ship: (%s, %s)", accel_x, accel_y)
        return accel_x, accel_y


    def point_to(self, x, y):
        self.point_to_x = x 
        self.point_to_y = y


    def ship_orientation_update(self):
        deltay = self.point_to_y - self.ship.y
        deltax = self.point_to_x - self.ship.x
        angle_to_mouse = 180 * np.arctan2( deltax, deltay ) / np.pi - 90
        self.ship.angle(angle_to_mouse)


    def update(self, dt):
        self.ship_orientation_update()
        self.check_for_collisions()
        accel_x, accel_y = self.accel_on_ship()
        self.ship.update(dt, accel_x=accel_x, accel_y=accel_y)

