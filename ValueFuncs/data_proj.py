__author__ 		= "Lekan Molu"
__copyright__ 	= "2021, Hamilton-Jacobi Analysis in Python"
__license__ 	= "Molux Licence"
__maintainer__ 	= "Lekan Molu"
__email__ 		= "patlekno@icloud.com"
__status__ 		= "Testing"

import numpy as np
from Utilities import *
from ValueFuncs import *
from Grids import processGrid
from BoundaryCondition import addGhostPeriodic
from scipy.interpolate import RegularGridInterpolator
import logging

logger = logging.getLogger(__name__)

def proj(g, data, dimsToRemove, xs=None, NOut=None, process=True):
    """
        [gOut, dataOut] = proj(g, data, dims, xs, NOut)
        Projects data corresponding to the grid g in g.dim dimensions, removing
        dimensions specified in dims. If a point is specified, a slice of the
        full-dimensional data at the point xs is taken.
        Inputs:
        g            - grid corresponding to input data
        data         - input data
        dimsToRemove - vector of len g.dim specifying dimensions to project
                    For example, if g.dim = 4, then dims = [0 0 1 1] would
                    project the last two dimensions
                    xs           - Type of projection (defaults to 'min')
                    'min':    takes the union across the projected dimensions
                    'max':    takes the intersection across the projected dimensions
                    a vector: takes a slice of the data at the point xs
                    NOut    - number of grid points in output grid (defaults to the same
                    number of grid points of the original grid in the unprojected
                    dimensions)
                    process            - specifies whether to call processGrid to generate
                            grid points
                            Outputs:
                            gOut    - grid corresponding to projected data
                            dataOut - projected data
    """
    # print(f'dimsToRemove: {dimsToRemove} {dimsToRemove.shape}')
    # Input checking
    if isinstance(dimsToRemove, list):
        dimsToRemove = np.asarray(dimsToRemove)
    if len(dimsToRemove) != g.dim:
        logger.fatal('Dimensions are inconsistent!')

    if np.count_nonzero(np.logical_not(dimsToRemove)) == g.dim:
        logger.warning('Input and output dimensions are the same!')
        return g, data

    # By default, do a projection
    if not xs:
        xs = 'min'

    # If a slice is requested, make sure the specified point has the correct
    # dimension
    if isnumeric(xs) and len(xs) != np.count_nonzero(dimsToRemove):
        logger.fatal('Dimension of xs and dims do not match!')

    if NOut is None:
        NOut = g.N[np.logical_not(dimsToRemove)]
        if NOut.ndim < 2:
            NOut = expand(NOut, 1)

    dataDims = data.ndim
    if np.any(data) and np.logical_not(dataDims == g.dim or dataDims == g.dim+1) \
        and not isinstance(data, list):
        logger.fatal('Inconsistent input data dimensions!')

    # Project data
    if dataDims == g.dim:
        gOut, dataOut = projSingle(g, data, dimsToRemove, xs, NOut, process)
    else:
        gOut, _  = projSingle(g, np.array([]), dimsToRemove, xs, NOut, process)

    # Project data
    numTimeSteps = len(data) if iscell(data) else data.shape[dataDims-1]
    dataOut      = cell(numTimeSteps) #np.zeros( NOut.T.shape + (numTimeSteps,) )

    for i in range(numTimeSteps):
        if iscell(data):
            _, dataOut[i] = projSingle(g, data[i], dimsToRemove, xs, NOut, process)
        else:
            _, dataOut[i] = projSingle(g, data[i, ...], dimsToRemove, xs, NOut, process)

    dataOut = dataOut.T

    return gOut, dataOut



def projSingle(g, data, dims, xs, NOut, process):
    """
     [gOut, dataOut] = proj(g, data, dims, xs, NOut)
       Projects data corresponding to the grid g in g.dim dimensions, removing
       dimensions specified in dims. If a point is specified, a slice of the
       full-dimensional data at the point xs is taken.

     Inputs:
       g       - grid corresponding to input data
       data    - input data
       dims    - vector of len g.dim specifying dimensions to project
                     For example, if g.dim = 4, then dims = [0 0 1 1] would
                     project the last two dimensions
       xs      - Type of projection (defaults to 'min')
           'min':    takes the union across the projected dimensions
           'max':    takes the intersection across the projected dimensions
           a vector: takes a slice of the data at the point xs
       NOut    - number of grid points in output grid (defaults to the same
                 number of grid points of the original grid in the unprojected
                 dimensions)
       process            - specifies whether to call processGrid to generate
                            grid points

     Outputs:
       gOut    - grid corresponding to projected data
       dataOut - projected data

     Original by Sylvia;
     Python by Lekan July 29. 2021
    """

    # Create ouptut grid by keeping dimensions that we are not collapsing
    if not np.any(g):
        if not xs.isalpha() or not strcmp(xs, 'max') and not strcmp(xs, 'min'):
            error('Must perform min or max projection when not specifying grid!')
    else:
        dims = dims.astype(bool)
        dim = np.count_nonzero(np.logical_not(dims))
        gOut = Bundle(dict(dim = dim,))
        ming = g.min[np.logical_not(dims)]
        maxg = g.max[np.logical_not(dims)]
        bdrg = np.asarray(g.bdry)[np.logical_not(dims)]
        # print('bdrg: ', bdrg)
        gOut.min = ming if ming.ndim==2 else expand(ming, 1)
        gOut.max = maxg if maxg.ndim==2 else expand(maxg, 1)
        gOut.bdry = bdrg if bdrg.ndim==2 else expand(bdrg, 1)

        if numel(NOut) == 1:
            gOut.N = NOut*ones(gOut.dim, 1).astype(np.int64)
        else:
            gOut.N = NOut


        # Process the grid to populate the remaining fields if necessary
        if process:
            gOut = processGrid(gOut)

        # Only compute the grid if value function is not requested
        if not np.any(data) or not data.size:
            return gOut, None

    # 'min' or 'max'
    if isinstance(xs, str): #xs.isalpha():
        dimsToProj = np.nonzero(dims)[0]

        for i in range(len(dimsToProj)-1, 0, -1):
            # print('dara: ', data.shape, dimsToProj, xs)
            if strcmp(xs,'min'):
                dataOut = np.amin(data, axis=dimsToProj[i])
            elif strcmp(xs, 'max'):
                dataOut = np.amax(data, axis=dimsToProj[i])
            else:
                error('xs must be a vector, ''min'', or ''max''!')

        return gOut, dataOut

    # Take a slice
    g, data = augmentPeriodicData(g, data)

    eval_pt = cell(g.dim)
    xsi = 0
    for i in range(g.dim):
        if dims[i]:
            # If this dimension is periodic, wrap the input point to the correct period
            if isfield(g, 'bdry') and id(g.bdry[i])==id(addGhostPeriodic):
                period = max(g.vs[i]) - min(g.vs[i])
                while xs[xsi] > max(g.vs[i]):
                    xs[xsi] -= period
                while xs[xsi] < min(g.vs[i]):
                    xs[xsi] += period
            eval_pt[i] = xs[xsi]
            xsi += 1
        else:
            eval_pt[i] = g.vs[i]

    # https://stackoverflow.com/questions/21836067/interpolate-3d-volume-with-numpy-and-or-scipy
    data_coords = [x.squeeze() for x in g.vs]
    fn = RegularGridInterpolator(data_coords, data)
    eval_pt = [x.squeeze() for x in eval_pt if isinstance(x, np.ndarray)] + [np.array([x]) for x in eval_pt if not isinstance(x, np.ndarray)]

    eshape = tuple([x.shape for x in eval_pt])
    if len(eshape) != data.ndim:
        eval_pt = np.tile(eval_pt, [*(data.shape[:-1]), 1])
    temp = fn(eval_pt)
    dataOut = copy.copy(temp)

    temp = g.vs[np.logical_not(dims)]

    dataOut = np.interp(temp, dataOut, gOut.xs[:])

    return gOut, dataOut
