__all__ =[ "splitGrid_sameDim"]

import cupy as cp
from Utilities import *
from Grids import createGrid, getOGPBounds
import copy

def splitGrid_sameDim(g, bounds, padding=None):
    """
     gs = splitGrid_sameDim(g, bounds, padding)
         Splits the grid into smaller grids, each with specified bounds.
         Optionally, padding can be specified so that the grids overlap

     Icp.ts:
         g      - original grid
         bounds - list of bounds of the smaller grids. This should be a g.dim
                  dimensional matrix that specifies the "grid" of bounds.
             For example, suppose the original grid is a [-1, 1]^2 grid in 2D.
             Then, the following bounds would split it into [-1, 0]^2, [0, 1]^2,
             [-1, 0] x [0, 1], and [0, 1] x [-1, 0] grids:
                 bounds = {[-1, 0, 1], [-1, 0, 1]};
         padding - amount of overlap between two adjacent subgrids

     Output:
         gs - subgrids

    Status: Under development. Use Sep Grids for now
     """

    if padding is None:
        padding = cp.zeros((g.dim, 1))

    assert isinstance(bounds, list), 'bounds must be a list or list of lists'
    ## Create a grid for the bounds
    if g.dim > 1:
        bounds_grid = cp.meshgrid(*bounds, sparse=False, indexing='ij');
    else:
        # indexing and sparse flags have no effect in 1D case
        bounds_grid = cp.meshgrid(bounds, indexing='ij')[0]

    ## Create grids based on the bound grid
    temp = size(bounds_grid[0])
    temparr = cp.array((temp))
    gs = cp.zeros(temparr-(temparr>1).astype(cp.int64))

    ii = cell(g.dim, 1)
    gss = []
    for i in range(numel(gs)):
        ii = cp.asarray(cp.unravel_index(i, size(gs), order='F'))
        iip = copy.copy(ii)
        for j in range(g.dim):
            iip[j] += 1
        grid_min = []
        grid_max = []
        # turn'em to indices (tuples) to aid dynamic
        # indexing (see: https://numpy.org/doc/stable/user/basics.indexing.html)
        ii, iip = tuple(ii), tuple(iip)
        for j in range(g.dim):
            grid_min.append(bounds_grid[j][ii])
            grid_max.append(bounds_grid[j][iip])
        grid_min, grid_max = cp.vstack((grid_min)), cp.vstack((grid_max))
        #print(f'grid_min: {grid_min.shape}, grid_max: {grid_max.shape}')
        grid_min, grid_max, N = getOGPBounds(g, grid_min, grid_max, padding);
        gss.append(createGrid(grid_min, grid_max, N, process=True))

    return gss
