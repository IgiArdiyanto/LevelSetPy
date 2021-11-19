from .dyn_sys import DynSys
import copy
import cupy as np
from Utilities import *
from ExplicitIntegration.runge_kutta4 import dynamics_RK4

class DubinsCar(DynSys):
    def __init__(self, x, wRange, speed, dRange=None, dims=None):
        """
            Wrapper around Sylvia's Dubins Car Class
            dRange must be a {2X3} vector
            or a {1X3} vector
        """
        self.x = to_column_mat(x)
        # Angle bounds
        if wRange is None:
            self.wRange = np.array([[-1, 1]]).T
        elif numel(wRange) == 2:
            self.wRange = wRange
        else:
            self.wRange = [-wRange, wRange] #np.array([[-wRange, wRange]]).T

        self.speed = 5 if not speed else speed # Constant speed = speed

        # Disturbance
        if dRange is None:
            self.dRange = np.zeros((2, 3))
        elif np.any(dRange.shape)==1:
            # make it 2 x 3 by stacking
            self.dRange = np.vstack([-dRange, dRange])
        else:
            self.dRange = dRange

        # Dimensions that are active
        self.dims = np.arange(3) if dims is None else dims

        pdim = np.where((self.dims==0) | (self.dims==1))
        DynSys.__init__(self, nx=len(self.dims), nu=1,nd=3,
                                x = self.x, xhist=self.x, pdim=pdim
                               )

    def dynamics(self, t, x, u, d=None):
        # Dynamics of the Dubins Car
        #    \dot{x}_1 = v * cos(x_3) + d1
        #    \dot{x}_2 = v * sin(x_3) + d2
        #    \dot{x}_3 = w
        #   Control: u = w;
        if not d:
            d = np.zeros((3,1))
        if iscell(x):
            dx = cell(len(self.dims), 1)
            for i in range(len(self.dims)):
                dx[i] = self.dynamics_helper(x, u, d, self.dims, self.dims[i])
        else:
            dx = np.zeros((self.nx, 1), dtype=np.float64)
            dx[0] = self.speed * np.cos(x[2]) + d[0]
            dx[1] = self.speed * np.sin(x[2]) + d[1]
            dx[2] = u + d[2]

        return dx

    def dynamics_helper(self, x, u, d, dims, dim):
        if dim==0:
            # print('dims: ', dims, 'x: ', [d.shape for d in x])
            dx = self.speed * np.cos(x[2]) + d[0]
        elif dim==1:
            dx = self.speed * np.sin(x[2]) + d[1]
        elif dim==2:
            dx = u + d[2]
        else:
            error('Only dimension 1-3 are defined for dynamics of DubinsCar!')
        return dx

    def get_opt_u(self, t=0, deriv=0, uMode='min', y=0):
        "Returns optimal control law; t, y=None by default"

        if numel(deriv)==1:
            deriv = cell(deriv, 1)
        ## Optimal control
        if uMode=='max':
            uOpt = (deriv[2]>=0)*self.wRange[1] + (deriv[2]<0)*(self.wRange[0]);
        elif uMode=='min':
            uOpt = (deriv[2]>=0)*(self.wRange[0]) + (deriv[2]<0)*self.wRange[1]
            # print(uOpt.shape, 'uOpt')
        else:
            error('Unknown control Mode!')

        return uOpt

    def get_opt_v(self, t=0, deriv=0, dMode='max', y=0):
        """Returns optimal disturbance
        """
        if numel(deriv)==1:
            deriv = cell(deriv, 1)

        vOpt = []

        ## Optimal control
        if dMode=='max':
          for i in range(3):
              if np.any(self.dims == i):
                  vOpt.append((deriv[i]>=0)*self.dRange[1][i] + \
                            (deriv[i]<0)*(self.dRange[0][i]))

        elif dMode=='min':
          for i in range(3):
              if np.any(self.dims[self.dims == i]):
                  vOpt.append((deriv[i]>=0)*self.dRange[0][i] + \
                            (deriv[i]<0)*(self.dRange[1][i]))
        else:
            warn(f'Unknown dMode: {dMode}!')

        return vOpt

    def update_state(self, u, T=0, x0=None, d=[]):
        # Updates state based on control
        #
        # Inp.ts:   obj - current quardotor object
        #           u   - control (defaults to previous control)
        #           T   - duration to hold control
        #           x0  - initial state (defaults to current state if set to [])
        #           d   - disturbance (defaults to [])
        #
        # Outputs:  x1  - final state
        if x0 is None:
            x0 = self.x

        if T == 0:
            return x0

        if u is None:
            return x0

        if np.isnan(u):
            warn(f'u is Nan')
            return x0

        if u.shape[0]<u.shape[1]:
            u = u.T

        if not np.any(d):
            x = dynamics_RK4(self.dynamics, [0, T], x0, u, [])
        else:
            x = dynamics_RK4(self.dynamics, [0, T], x0, u, d)

        x1 = np.asarray(x)

        self.x = x1
        self.u = u

        self.xhist = np.concatenate((x1, self.xhist), 1)
        self.uhist = np.concatenate((u, self.uhist), 1)
