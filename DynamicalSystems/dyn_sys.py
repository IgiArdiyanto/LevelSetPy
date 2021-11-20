""" This file defines the base dynamical systems class. """
from LevelSetPy.Utilities import cell

class DynSys(object):
    def __init__(self, nx=None, nu=None, nd=None, x=None, u=None,
                        xhist=None, uhist=None, pdim=None, vdim=None,
                        hdim=None, hpxpy=None, hpxpyhist = None,
                        hvxvy=None, hvxvyhist=None, data=None):
        self.nx = nx          # Number of state dimensions
        self.nu = nu          # Number of control inp.ts
        self.nd = nd          # Number of disturbance dimensions

        self.x = x           # State
        self.u = u           # Recent control signal

        self.xhist = xhist       # History of state
        self.uhist = uhist       # History of control

        self.pdim = pdim       # position dimensions
        self.vdim = vdim       # velocity dimensions
        self.hdim = hdim       # heading dimensions

        self.hpxpy = hpxpy          # Position
        self.hpxpyhist = hpxpyhist      # Position history
        self.hvxvy   = hvxvy        # Velocity
        self.hvxvyhist = hvxvyhist      # Velocity history

        # Data (any data that one may want to store for convenience)
        self.data = data
