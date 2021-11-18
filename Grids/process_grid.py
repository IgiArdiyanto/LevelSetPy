__all__ = ["processGrid"]

import copy
import cupy as cp
from Utilities.matlab_utils import *
from BoundaryCondition import addGhostPeriodic

def processGrid(gridIn, data=None, sparse_flag=False):
    """
     processGrid: Construct a grid data structure, and check for consistency.

       gridOut = processGrid(gridIn, data)

     Processes all the various types of grid argument allowed.

     Icp.t Parameters:

       gridIn: A scalar, a vector, or a structure.

         Scalar: It is assumed to be the dimension.  See below for default
         settings for other grid fields.

         Vector: It contains the number of grid nodes in each dimension.  See
         below for default settings for other fields.

         Structure: It must contain some subset of the following fields
         (where each vector has length equal to the number of dimensions):

    	      gridIn.dim: Positive integer scalar, dimension of the grid.

    	      gridIn.min: Double vector specifying the lower left corner of the grid.

    	      gridIn.max: Double vector specifying the upper right corner of the grid.

    	      gridIn.N: Positive integer vector specifying the number of grid
    	      nodes in each dimension.

    	      gridIn.dx: Positive double vector specifying the grid spacing in
    	      each dimension.

    	      gridIn.vs: Cell vector, each element is a vector of node locations
    	      for that dimension.

    	      gridIn.xs: Cell vector, each element is an array of node locations
    	      (result of calling ndgrid on vs).

    	      gridIn.bdry: Cell vector of function handles pointing to boundary
    		    condition generating functions for each dimension.

           gridIn.bdryData: Cell vector of data structures for the boundary
    		    condition generating functions.

           gridIn.axis: Vector specifying computational domain bounds in a
           format suitable to pass to the axis() command (only defined for 2D
           and 3D grids, otherwise grid.axis == []).

           gridIn.shape: Vector specifying grid node count in a format suitable
           to pass to the reshape() command (usually grid.N', except for 1D
           grids).

         If any of the following fields are scalars, they are replicated
         gridIn.dim times: min, max, N, dx, bdry, bdryData.

         In general, it is not necessary to supply the fields: vs, xs, axis, shape.

         If one of N or dx is supplied, the other is inferred.
         If both are supplied, consistency is checked.

         Dimensional consistency is checked on all fields.

         Default settings (only used if value is not given or inferred)
    	      min   = zeros(dim, 1)
    	      max   = ones(dim, 1)
    	      N     = 101
    	      bdry  = periodic

       data: Double array.  Optional.  If present, the data array is checked
       for consistency with the grid.

       sparse_flag: Whether to make a sparse or dense grid. Default = False

     Output Parameters:

       gridOut: the full structure described for gridIn above.

     Copyright 2004 Ian M. Mitchell (mitchell@cs.ubc.ca).
     This software is used, copied and distributed under the licensing
       agreement contained in the file LICENSE in the top directory of
       the distribution.


     Ian Mitchell, 1/22/03
      new version  5/13/03 added fields dim, dx, vs, xs, bdry.
      new version  1/13/04 added field bdryData.
      new version  2/09/04 added field shape.
      new version  8/23/12 fixed some floating point problems with N and dx.


     Lekan Molux, Python, 7/26/2021
     ----------------------------------------------------------------------------
    """
    defaultMin = 0;
    defaultMax = 1;
    defaultN = 101;
    defaultBdry = addGhostPeriodic;
    defaultBdryData = [];

    # This is just to avoid attempts to allocate 100 dimensional arrays.
    maxDimension = 5;

    if not isinstance(gridIn, Bundle):
        if len(gridIn) == 1:
            gridOut.dim = gridIn;
        elif(ndims(gridIn) == 2):
            # Should be a vector of node counts.
            if(gridIn.shape[1] != 1):
                error('gridIn vector must be a column vector');
            else:
                gridOut.dim = len(gridIn);
                gridOut.N = gridIn;
        else:
            error('Unknown format for gridIn parameter');
    else:
        gridOut = copy.copy(gridIn);


    # Now we should have a partially complete structure in gridOut.

    if(isfield(gridOut, 'dim')):
        #print('hasDim')
        if(gridOut.dim > maxDimension):
            warn('Grid dimension > {}, may be dangerously large'.format(maxDimension));
        if(gridOut.dim < 0):
            error('Grid dimension must be positive');
    else:
        error('Grid structure must contain dimension');

    # Process grid boundaries.
    if(isfield(gridOut, 'min')):
        if(not isColumnLength(gridOut.min, gridOut.dim)):
            if(isscalar(gridOut.min)):
                gridOut.min = gridOut.min * cp.ones((gridOut.dim, 1));
            else:
                error('min field is not column vector of length dim or a scalar');
    else:
        gridOut.min = defaultMin * cp.ones((gridOut.dim, 1));

    if(isfield(gridOut, 'max')):
        if(not isColumnLength(gridOut.max, gridOut.dim)):
            if(isscalar(gridOut.max)):
                gridOut.max = gridOut.max * cp.ones((gridOut.dim, 1));
            else:
                error('max field is not column vector of length dim or a scalar');
    else:
        gridOut.max = defaultMin * cp.ones((gridOut.dim, 1));

    if(cp.any(gridOut.max <= gridOut.min)):
        error('max bound must be strictly greater than min bound in all dimensions');

    # Check N field if necessary.  If N is missing but dx is present, we will
    # determine N later.
    if(isfield(gridOut, 'N')):
        if(cp.any(gridOut.N <= 0)):
            error('number of grid cells must be strictly positive');
        if(not isColumnLength(gridOut.N, gridOut.dim)):
            if(isscalar(gridOut.N)):
                gridOut.N *= cp.ones((gridOut.dim, 1)).astype(cp.int64);
            else:
                error('N field is not column vector of length dim or a scalar');

    # Check dx field if necessary.  If dx is missing but N is present, infer
    # dx.  If both are present, we will check for consistency later.  If
    # neither are present, use the defaults.
    if isfield(gridOut, 'dx'):
        if(cp.any(gridOut.dx <= 0)):
            error('grid cell size dx must be strictly positive');
        if(not isColumnLength(gridOut.dx, gridOut.dim)):
            if(isscalar(gridOut.dx)):
                gridOut.dx *= cp.ones((gridOut.dim, 1), cp.float64)
        else:
            error('dx field is not column vector of length dim or a scalar');
    elif isfield(gridOut, 'N'):
        # Only N field is present, so infer dx.
        # print('gridOut.max - gridOut.min: ', (gridOut.max - gridOut.min).T)
        # print('gridOut.N: ', gridOut.N.T)
        gridOut.dx = cp.divide(gridOut.max - gridOut.min,  gridOut.N-1)
    else:
        logger.warn('Neither fields dx nor dN is present, so use default N and infer dx')
        gridOut.N = defaultN * ones(gridOut.dim, 1).astype(cp.int64)
        gridOut.dx = cp.divide(gridOut.max - gridOut.min, gridOut.N-1)
    # print('gridOut.max aft dx in PG ', gridOut.max.T)

    if isfield(gridOut, 'vs'):
        if(iscell(gridOut.vs)):
            if(not isColumnLength(gridOut.vs, gridOut.dim)):
                error(f'vs field is not column cell vector of length dim: {gridOut.dim}');
            else:
                for i in range(gridOut.dim):
                    if(not isColumnLength(gridOut.vs[i], gridOut.N[i])):
                        error('vs cell entry is not correctly sized vector');
        else:
            error('vs field is not a cell vector');
    else:
        gridOut.vs = cell(gridOut.dim, 1)
        for i in range(gridOut.dim):
            gridOut.vs[i] = expand(cp.linspace(gridOut.min[i,0], gridOut.max[i,0], num=gridOut.N[i,0]), 1)
    # Now we can check for consistency between dx and N, based on the size of
    # the vectors in vs.  Note that if N is present, it will be a vector.  If
    # N is not yet a field, set it to be consistent with the size of vs.

    if isfield(gridOut, 'N'):
        for i in range(gridOut.dim):
            if(gridOut.N[i] != len(gridOut.vs[i])):
                error(f'Inconsistent grid size in dimension {i}');
    else:
        gridOut.N = zeros(gridOut.dim, 1)

    for i in range(gridOut.dim):
        gridOut.N[i] = len(gridOut.vs[i])

    if(isfield(gridOut, 'xs')):
        if(iscell(gridOut.xs)):
            if(not isColumnLength(gridOut.xs, gridOut.dim)):
                error(f'xs field is not column cell vector of length/dim: {gridOut.dim}');
            else:
                if(gridOut.dim > 1):
                    for i in range(gridOut.dim):
                        if(cp.any(gridOut.xs[i]) != gridOut.N.T):
                            error('xs cell entry is not correctly sized array');
                else:
                    if(len(gridOut.xs[0]) != gridOut.N):
                        error('xs cell entry is not correctly sized array');
        else:
            error('xs field is not a cell vector');
    else:
        gridOut.xs = cp.meshgrid(*gridOut.vs, indexing='ij', sparse=sparse_flag)

    if isfield(gridOut, 'bdry'):
        if(iscell(gridOut.bdry) or isinstance(gridOut.bdry, cp.ndarray)):
            if(not isColumnLength(gridOut.bdry, gridOut.dim)):
                error(f'bdry field is not column cell vector of length dim: {gridOut.dim}');
            else:
                pass
        else:
            if(isscalar(gridOut.bdry)):
                bdry = gridOut.bdry;
                gridOut.bdry = [bdry for _ in range(gridOut.dim)]
            else:
                error('bdry field is not a cell vector or a scalar');
    else:
        gridOut.bdry = cp.zeros((gridOut.dim, 1)).fill(defaultBdry)

    if(isfield(gridOut,'bdryData')):
        if(iscell(gridOut.bdryData)):
            if(not isColumnLength(gridOut.bdryData, gridOut.dim)):
                error(f'bdryData field is not column cell vector of length dim: {gridOut.dim}');
            else:
                logger.warn('Maybe not worth checking that entries are structures')
        else:
            if(isscalar(gridOut.bdryData)):
                bdryData = gridOut.bdryData;
                gridOut.bdryData = [bdryData for i in range(gridOut.dim)]
            else:
                error('bdryData field is not a cell vector or a scalar');
    else:
        gridOut.bdryData = [defaultBdryData for i in range(gridOut.dim)]

    if((gridOut.dim == 2) or (gridOut.dim == 3)):
        if(isfield(gridOut, 'axis')):
            for i in range(gridOut.dim):
                if(gridOut.axis.take(2 * i) != gridOut.min[i]):
                    error('axis and min fields do not agree');
                if(gridOut.axis.take(2 * i) is not gridOut.max[i]):
                    error('axis and max fields do not agree');
        else:
            gridOut.axis = zeros(1, 2 * gridOut.dim);
            for i in range(gridOut.dim):
                gridOut.axis[0, 2*i : 2*i+2] = [ gridOut.min[i], gridOut.max[i] ];
    else:
        gridOut.axis = [];

    Nshape = tuple(gridOut.N.squeeze())
    if(isfield(gridOut, 'shape')):
        if(gridOut.dim == 1):
            if(cp.any(gridOut.shape != (Nshape + (1,)) )):
                error('shape and N fields do not agree');
        else:
            if(cp.any(gridOut.shape != gridOut.N.T)):
                error('shape and N fields do not agree');
    else:
        if(gridOut.dim == 1):
            gridOut.shape = (Nshape + (1,))
        else:
            gridOut.shape = Nshape

    # check data parameter for consistency
    if data:
        if(ndims(data) != len(gridOut.shape)):
            error('data parameter does not agree in dimension with grid');
        if(cp.any(size(data) != gridOut.shape)):
            error('data parameter does not agree in array size with grid');
    # print('gridOut.max after all PG ', gridOut.max.T)

    return  gridOut
