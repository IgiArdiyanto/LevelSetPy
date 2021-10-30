__author__ 		= "Lekan Molu"
__copyright__ 	= "2021, Hamilton-Jacobi Analysis in Python"
__license__ 	= "Molux Licence"
__maintainer__ 	= "Lekan Molu"
__email__ 		= "patlekno@icloud.com"
__status__ 		= "Testing"

import copy
import matplotlib
import numpy as np
from os.path import join
from datetime import datetime

from Utilities import *
from ValueFuncs import *
from Hamiltonians import *
from Visualization import *
from SpatialDerivative import *
from ExplicitIntegration import *

from Visualization.value_viz import ValueVisualizer
import matplotlib.pyplot as plt

def HJIPDE_solve(data0, tau, schemeData, compMethod, extraArgs):
	"""
	 data, tau, extraOuts = \
	   HJIPDE_solve(data0, tau, schemeData, minWith, extraargs)
		 Solves HJIPDE with initial conditions data0, at times tau, and with
		 parameters schemeData and extraArgs

		Note: Real action starts on line 693

	 ----- How to use this function -----

	 Inputs:
	   data0           - initial value function
	   tau             - list of computation times
	   schemeData      - problem parameters passed into the Hamiltonian func
						   .grid: grid (required!)
						   .accuracy: accuracy of derivatives
	   compMethod      - Informs which optimization we're doing
						   - 'set' or 'none' to compute reachable set
							 (not tube)
						   - 'zero' or 'minWithZero' to min Hamiltonian with
							  zero
						   - 'minVOverTime' to do min with previous data
						   - 'maxVOverTime' to do max with previous data
						   - 'minVWithL' or 'minVWithTarget' to do min with
							  targets
						   - 'maxVWithL' or 'maxVWithTarget' to do max with
							  targets
						   - 'minVWithV0' to do min with original data
							 (default)
						   - 'maxVWithV0' to do max with original data
	   extraArgs       - this structure can be used to leverage other
						   additional functionalities within this function.
						   Its subfields are:
		 .obstacleFunction:    (matrix) a function describing a single
							   obstacle or a list of obstacles with time
							   stamps tau (obstacles must have same time stamp
							   as the solution)
		 .targetFunction:      (matrix) the function l(x) that describes a
							   stationary goal/unsafe set or a list of targets
							   with time stamps tau (targets must have same
							   time stamp as the solution). This functionality
							   is mainly useful when the targets are
							   time-varying, in case of variational inequality
							   for example; data0 can be used to specify the
							   target otherwise. This is also useful when
							   warm-starting with a value function (data0)
							   that is not equal to the target/cost function
							   (l(x))
		 .keepLast:            (bool) Only keep data from latest time stamp
							   and delete previous datas
		 .quiet:               (bool) Don't spit out stuff in command window
		 .lowMemory:           (bool) use methods to save on memory
		 .fipOutput:           (bool) flip time stamps of output
		 .stopInit:            (vector) stop the computation once the
							   reachable set includes the initial state
		 .stopSetInclude:      (matrix) stops computation when reachable set
							   includes this set
		 .stopSetIntersect:    (matrix) stops computation when reachable set
							   intersects this set
		 .stopLevel:           (double) level of the stopSet to check the
							   inclusion for. Default level is zero.
		 .stopConverge:        (bool) set to True to stop the computation when
							   it converges
		 .convergeThreshold:   Max change in each iteration allowed when
							   checking convergence
		 .ignoreBoundary:      Ignores the boundary of the grid when
							   calculating convergence
		 .discountFactor:      (double) amount by which you'd like to discount
							   the value function. Used for ensuring
							   convergence. Remember to move your targets
							   function (l(x)) and initial value function
							   (data0) down so they are below 0 everywhere.
							   you can raise above 0 by the same amount at the
							   end.
		 .discountMode:        Options are 'Kene' or 'Jaime'.  Defaults to
							   'Jaime'. Math is in Kene's minimum discounted
							   rewards paper and Jaime's "bridging
							   hamilton-jacobi safety analysis and
							   reinforcement learning" paper
		 .discountAnneal:      (string) if you want to anneal your discount
							   factor over time so it converges to the right
							   solution, use this.
								   - 'soft' moves it slowly towards 1 each
									 time convergence happens
								   - 'hard' sets it to 1 once convergence
									  happens
								   - 1 sets it to 'hard'
		 .SDModFunc, .SDModParams:
			 Function for modifying scheme data every time step given by tau.
			 Currently this is only used to switch between using optimal control at
			 every grid point and using maximal control for the SPP project when
			 computing FRS using centralized controller

		 .saveFilename, .saveFrequency:
			 file name under which temporary data is saved at some frequency in
			 terms of the number of time steps

		 .compRegion:          unused for now (meant to limit computation
							   region)
		 .addGaussianNoiseStandardDeviation:
			   adds random noise

		 .makeVideo:           (bool) whether or not to create a video
		 .videoFilename:       (string) filename of video
		 .frameRate:           (int) framerate of video
		 .visualize:           either fill in struct or set to 1 for generic
							   visualization
							   .plotData:          (struct) information
												   required to plot the data:
												   .plotDims: dims to plot
												   .projpt: projection points.
															Can be vector or
															cell. e.g.
															{pi,'min'} means
															project at pi for
															first dimension,
															take minimum
															(union) for second
															dimension
							   .sliceLevel:        (double) level set of
												   reachable set to visualize
												   (default is 0)
							   .holdOn:            (bool) leave whatever was
													already on the figure?
							   .lineWidth:         (int) width of lines
							   .viewAngle:         (vector) [az,el] angles for
												   viewing plot
							   .camlightPosition:  (vector) location of light
												   source
							   .viewGrid:          (bool) view grid
							   .viewAxis:          (vector) size of axis
							   .xTitle:            (string) x axis title
							   .yTitle:            (string) y axis title
							   .zTitle:            (string) z axis title
							   .dtTime             How often you want to
												   update time stamp on title
												   of plot
							   .fontSize:          (int) font size of figure
							   .deleteLastPlot:    (bool) set to True to
												   delete previous plot
												   before displaying next one
							   .figNum:            (int) for plotting a
												   specific figure number
							   .figFilename:       (string) provide this to
												   save the figures (requires
												   export_fig package)
							   .initialValueSet:   (bool) view initial value
												   set
							   .initialValueFunction: (bool) view initial
												   value function
							   .valueSet:          (bool) view value set
							   .valueFunction:     (bool) view value function
							   .obstacleSet:       (bool) view obstacle set
							   .obstacleFunction:  (bool) view obstacle
												   function
							   .targetSet:         (bool) view target set
							   .targetFunction:    (bool) view target function
							   .plotColorVS0:      color of initial value set
							   .plotColorVF0:      color of initial value
												   function
							   .plotAlphaVF0:      transparency of initial
												   value function
							   .plotColorVS:       color of value set
							   .plotColorVF:       color of value function
							   .plotAlphaVF:       transparency of initial
												   value function
							   .plotColorOS:       color of obstacle set
							   .plotColorOF:       color of obstacle function
							   .plotAlphaOF:       transparency of obstacle
												   function
							   .plotColorTS:       color of target set
							   .plotColorTF:       color of target function
							   .plotAlphaTF:       transparency of target
												   function

	 Outputs:
	   data - solution corresponding to grid g and time vector tau
	   tau  - list of computation times (redundant)
	   extraOuts - This structure can be used to pass on extra outputs, for
				   example:
		  .stoptau: time at which the reachable set contains the initial
					state; tau and data vectors only contain the data till
					stoptau time.

		  .hVS0:   These are all figure handles for the appropriate
		  .hVF0	set/function
		  .hTS
		  .hTF
		  .hOS
		  .hOF
		  .hVS
		  .hVF


	 -------Updated 11/14/18 by Sylvia Herbert (sylvia.lee.herbert@gmail.com)

	 Python July 29, 2021 (Lekan Molu)
	"""

	## Default parameters
	if numel(tau) < 2:
		error('Time vector must have at least two elements!')

	if not compMethod: compMethod = 'minVOverTime'

	if not extraArgs: extraArgs = Bundle(dict())

	extraOuts = Bundle(dict())
	quiet = False;
	lowMemory = False;
	keepLast = False;
	flipOutput = False;

	small = 1e-4;
	g = schemeData.grid;
	gDim = g.dim;

	## Backwards compatible
	if isfield(extraArgs, 'low_memory'):
		extraArgs.lowMemory = copy.deepcopy(extraArgs.low_memory)

	if isfield(extraArgs, 'flip_output'):
		extraArgs.flipOutput = extraArgs.flip_output

	if isfield(extraArgs, 'stopSet'):
		extraArgs.stopSetInclude = extraArgs.stopSet

	if isfield(extraArgs, 'quiet') and extraArgs.quiet:
		info('Solving HJI PDEs in quiet mode')
		quiet = True;

	# Low memory mode
	if isfield(extraArgs, 'lowMemory') and extraArgs.lowMemory:
		info('HJIPDE_solve running in low memory mode')
		lowMemory = True;

		# Save the output in reverse order
		if (extraArgs.flipOutput) and (extraArgs.flipOutput):
			flipOutput = True;

	# Only keep latest data (saves memory)
	if isfield(extraArgs, 'flipOutput') and extraArgs.keepLast:
		keepLast = True;

	#---Extract the information about obstacles--------------------------------
	obsMode = 'none';

	if isfield(extraArgs, 'obstacleFunction'):
		obstacles = extraArgs.obstacleFunction;

		# are obstacles moving or not?
		if obstacles.ndim == gDim:
			obsMode = 'static';
			obstacle_i = obstacles;
		elif obstacles.ndim == gDim + 1:
			obsMode = 'time-varying';
			obstacle_i = obstacles[0, ...];
		else:
			error('Inconsistent obstacle dimensions!')

		"""
			We always take the max between the data and the obstacles
			note that obstacles are negated.  That's because if you define the
			obstacles using something like ShapeSphere, it sets it up as a
			target. To make it an obstacle we just negate that.
		"""
		data0 = np.maximum(data0, -obstacle_i)

	#---Extract the information about targets----------------------------------
	targMode = 'none'

	if isfield(extraArgs, 'targetFunction'):
		targets = extraArgs.targetFunction
		# is target function moving or not?
		if targets.ndim == gDim:
			targMode = 'static'
			target_i = targets;
		elif targets.ndim == gDim + 1:
			targMode = 'time-varying'
			target_i = targets[0, ...]
		else:
			error('Inconsistent target dimensions!')

	#---Stopping Conditions----------------------------------------------------
	if isfield(extraArgs, 'stopInit'):
		if not isvector(extraArgs.stopInit) or gDim!=len(extraArgs.stopInit):
			error('stopInit must be a vector of length g.dim!')

	if isfield(extraArgs,'stopSetInclude') or isfield(extraArgs,'stopSetIntersect'):
		if isfield(extraArgs,'stopSetInclude'):
			stopSet = extraArgs.stopSetInclude
		else:
			stopSet = extraArgs.stopSetIntersect;

		if stopSet.ndim != gDim or np.any(size(stopSet) != g.N.T):
			error('Inconsistent stopSet dimensions!')

		# Extract set of indices at which stopSet is negative
		setInds = stopSet[stopSet < 0]

		# Check validity of stopLevel if needed
		if isfield(extraArgs, 'stopLevel'):
			stopLevel = extraArgs.stopLevel;
		else:
			stopLevel = 0;

	# Visualization
	if (isfield(extraArgs, 'visualize') and
		isbundle(extraArgs.visualize)):
		timeCount = 0
		#---Projection Parameters----------------------------------------------

		# Extract the information about plotData
		plotDims, projpt = ones(gDim, 1), []
		if isfield(extraArgs.visualize, 'plotData'):
			plotDims = extraArgs.visualize.plotData.plotDims;
			# Points to project other dimensions at.
			projpt = extraArgs.visualize.plotData.projpt;

		# Number of dimensions to be plotted and to be projected
		pDims = np.count_nonzero(plotDims)
		projDims = len(projpt)

		# Basic Checks
		if (pDims > 4):
			error('Currently plotting up to 3D is supported!');

		#---Defaults-----------------------------------------------------------
		if isfield(extraArgs, 'obstacleFunction') and isfield(extraArgs, 'visualize'):
			if not isfield(extraArgs.visualize, 'obstacleSet'):
				extraArgs.visualize.obstacleSet = 1

		if isfield(extraArgs, 'targetFunction') and isfield(extraArgs, 'visualize'):
			if not isfield(extraArgs.visualize, 'targetSet'):
				extraArgs.visualize.targetSet = 1;

		# Number of dimensions to be plotted and to be projected
		pDims = np.count_nonzero(plotDims);
		if isnumeric(projpt):
			projDims = len(projpt);
		else:
			projDims = gDim - pDims;

		# Set level set slice
		if isfield(extraArgs.visualize, 'sliceLevel'):
			sliceLevel = extraArgs.visualize.sliceLevel;
		else:
			sliceLevel = 0;

		"Back up copy ops"
		gPlot = copy.deepcopy(g)
		dataPlot = copy.deepcopy(data0)
		if isfield(extraArgs, 'obstacleFunction'):
			obsPlot = copy.deepcopy(obstacle_i)
		if isfield(extraArgs, 'targetFunction'):
			targPlot = copy.deepcopy(target_i)

		if (projDims == 0):
			"Project"
			debug(f"projDims = {projDims}; whence not projecting.")
		elif iscell(projpt):
			"""
				if projpt is a cell, project each dimensions separately. This
				allows us to take the union/intersection through some dimensions
				and to project at a particular slice through other dimensions.
			"""
			idx = np.nonzero(plotDims==0)
			plotDimsTemp = np.ones(len(plotDims))
			for ii in range(len(idx[0])-1, 0, -1):
				plotDimsTemp[idx[ii]] = 0;
				if extraArgs.obstacleFunction:
					_, obsPlot = proj(gPlot, obsPlot, np.logical_not(plotDimsTemp), projpt[ii]);

				if extraArgs.targetFunction:
					_, targPlot = proj(gPlot, targPlot, np.logical_not(plotDimsTemp), projpt[ii])

				gPlot, dataPlot = proj(gPlot, dataPlot, np.logical_not(plotDimsTemp), projpt[ii])
				plotDimsTemp = ones(1,gPlot.dim);
		else:
			# should we use copy ops here?
			gPlot, dataPlot = proj(g, data0, np.logical_not(plotDims), projpt);

			if extraArgs.obstacleFunction:
				_, obsPlot = proj(g, obstacle_i, np.logical_not(plotDims), projpt);

			if extraArgs.targetFunction:
				_, targPlot = proj(g, target_i, np.logical_not(plotDims), projpt);

		"Set visualization defaults -- Put this in main?"
		params = Bundle(
				{"sliceDim": gPlot.dim,
				 'disp': True,
				 'labelsize': 16,
				 'linewidth': 2,
				 'init_conditions': False,
				 'pause_time': extraArgs.pause_time,
				 'level': 0, # which level set to visualize
				 'winsize': extraArgs.visualize.winsize,
				 'fontdict': Bundle({'fontsize':16, 'fontweight':'bold'}),
				 "savedict": Bundle({"save": False,
				 "savename": extraArgs.visualize.savename,
				 "savepath": extraArgs.visualize.savedir}),
				 })

		# plot once we hit an initial condition, if set
		if isfield(extraArgs, 'stopInit'):
			params.value = extraArgs.stopInit(plotDims.astype(bool))
			lev_viz = ValueVisualizer(params=params)
			extraArgs.visualize.is_initialized = True

		#---Visualize Initial Value Set----------------------------------------
		if isfield(extraArgs.visualize, 'initialValueSet') and extraArgs.visualize.initialValueSet:
			# put plot on ax1
			params.value_data = dataPlot
			params.grid_bundle = gPlot
			if gPlot.dim>3:
				'we take six snapshots of the value function on the last dim of each snapshot'
				num_plots = 6
			else:
				'one for inintial value set, one for surface plot, last for traj evolution'
				num_plots=2
			lev_viz = ValueVisualizer(params=params)

		## Visualize Target Function/Set
		if isfield(extraArgs.visualize, 'targetSet')  and extraArgs.visualize.targetSet:
			raise NotImplementedError('Target Set Visualizer is not yet Implemented.')

		#---Visualize Target Function------------------------------------------
		if isfield(extraArgs.visualize, 'targetFunction') and extraArgs.visualize.targetFunction:
			raise NotImplementedError('Target Function Visualizer is not yet Implemented.')

		#---Visualize Obstacle Set---------------------------------------------
		if isfield(extraArgs.visualize, 'obstacleSet') and extraArgs.visualize.obstacleSet:
			raise NotImplementedError('Obstacle Set Visualizer is not yet Implemented.')

		#---Visualize Obstacle Function----------------------------------------
		if  isfield(extraArgs.visualize, 'obstacleFunction') and extraArgs.visualize.obstacleFunction:
			raise NotImplementedError('Obstacle Function Visualizer is not yet Implemented.')

		#---Visualize Value Set------------------------------------------------
		if isfield(extraArgs.visualize, 'valueSet') and extraArgs.visualize.valueSet:
			if 'lev_viz' in locals():
				# print('Using already created value function plotter')
				lev_viz.levelset_viz(gPlot, dataPlot, ec='k', fc='cyan')
			else:
				lev_viz = ValueVisualizer(params=params)
				lev_viz.levelset_viz(gPlot, dataPlot, ec='k', fc='cyan')

		# time.sleep(400)
		#---Visualize Value Function-------------------------------------------
		if isfield(extraArgs.visualize, 'valueFunction') and  extraArgs.visualize.valueFunction:
			raise NotImplementedError('Value Function Visualizer is not yet Implemented.')

	## Extract dynamical system if needed
	if isfield(schemeData, 'dynSys'):
		schemeData.hamFunc = genericHam;
		schemeData.partialFunc = genericPartial;

	stopConverge = False;
	if isfield(extraArgs, 'stopConverge'):
		stopConverge = extraArgs.stopConverge;
		if isfield(extraArgs, 'convergeThreshold'):
			convergeThreshold = extraArgs.convergeThreshold;
		else:
			convergeThreshold = 1e-5;

	## SchemeFunc and SchemeData
	schemeFunc = termLaxFriedrichs;
	# Extract accuracy parameter o/w set default accuracy
	accuracy = 'veryHigh'
	if isfield(schemeData, 'accuracy'):
		accuracy = schemeData.accuracy;

	## Numerical approximation functions
	dissType = 'global';
	schemeData.dissFunc, integratorFunc, schemeData.derivFunc = getNumericalFuncs(dissType, accuracy);

	# if we're doing minWithZero or zero as the comp method, actually implement
	# correctly using level set toolbox
	if compMethod=='minWithZero' or compMethod=='zero':
		schemeFunc = termRestrictUpdate;
		schemeData.innerFunc = termLaxFriedrichs;
		schemeData.innerData = schemeData;
		schemeData.positive = 0;

	## Time integration
	ode_cfl_opts = Bundle({'factorCFL': 0.8, 'singleStep': 'on'})
	integratorOptions = odeCFLset(ode_cfl_opts)
	startTime = cputime();

	## Stochastic additive terms
	if isfield(extraArgs, 'addGaussianNoiseStandardDeviation'):
		# We are taking all the previous scheme terms and adding noise to it
		# Save all the previous terms as the deterministic component in detFunc
		detFunc = copy.deepcopy(schemeFunc)
		detData = copy.deepcopy(schemeData)
		# The full computation scheme will include this added term so clear
		# out the schemeFunc so we can pack everything back in later with the
		# new stuff
		del schemeFunc, schemeData;

		# Create the Hessian term corresponding to white noise diffusion
		stochasticFunc = termTraceHessian;
		stochasticData = Bundle(dict(grid = g,
				L = extraArgs.addGaussianNoiseStandardDeviation.T,
				R = extraArgs.addGaussianNoiseStandardDeviation,
				hessianFunc = hessianSecond))

		# Add the (saved) deterministic terms and the (new) stochastic term
		# together into the complete scheme
		schemeFunc = termSum;
		schemeData.innerFunc = [ detFunc, stochasticFunc ]
		schemeData.innerData = [ detData, stochasticData ]

	## Initialize PDE solution
	data0size = size(data0)

	if data0.ndim == gDim:
		# New computation
		if keepLast:
			data = copy.copy(data0);
		elif lowMemory:
			data = data0.astype(np.float32)
		else:
			data = np.zeros((data0size[0:gDim] +(len(tau), )), dtype=np.float64);
			data[0, ...] = data0;

		istart = 1;
	elif data0.ndim == gDim + 1:
		# Continue an old computation
		if keepLast:
			data = data0[data0size[-1], ...]
		elif lowMemory:
			data = data0[data0size[-1], ...].astype(np.float32)
		else:
			data = np.zeros((data0size[:gDim].shape+(len(tau),)), dtype=np.float64)
			data[:data0size[-1], ...] = data0;


		# Start at custom starting index if specified
		if isfield(extraArgs, 'istart'):
			istart = extraArgs.istart;
		else:
			istart = data0size[-1]+1;

	else:
		error('Inconsistent initial condition dimension!')

	if isfield(extraArgs,'ignoreBoundary') and extraArgs.ignoreBoundary:
		_, dataTrimmed = truncateGrid(g, data0, g.min+4*g.dx, g.max-4*g.dx);

	for i in range(istart, len(tau)):
		if not extraArgs.quiet:
			info(f'tau[{i}]: {tau[i]}')

		## Variable schemeData
		if isfield(extraArgs, 'SDModFunc'):
			if isfield(extraArgs, 'SDModParams'):
				paramsIn = extraArgs.SDModParams;
			else:
				paramsIn = [];

			schemeData = extraArgs.SDModFunc(schemeData, i, tau, data, obstacles, paramsIn);

		if keepLast:
			y0 = data
		elif lowMemory:
			if flipOutput:
				y0 = data[0,...]
			else:
				y0 = data[size(data, g.dim+1), ...]
		else:
			y0 = data[i-1, ...]

		y = expand(y0.flatten(order=DEFAULT_ORDER), 1)


		tNow = tau[i-1]

		## Main integration loop to get to the next tau(i)
		while tNow < tau[i] - small:
			# Save previous data if needed
			if compMethod =='minVOverTime' or compMethod =='maxVOverTime':
				yLast = y;
			if not quiet:
				info(f'Computing {tNow}, {tau[i]}')
			"""
				Solve hamiltonian and apply to value function (y) to get updated
				value function # integrator function is an odeCFL function
				integratorFunc is @OdeCFL3, derivFunc is upwindFirstWENO5,
				dissipator=artificialDissipationGLF, schemeFunc is termLaxFriedrichs
			"""
			tNow, y, _ = integratorFunc(schemeFunc, [tNow, tau[i]], y, integratorOptions, schemeData)

			if np.any(np.isnan(y)):
				error(f'Nans encountered in the integrated result of HJI PDE data')

			## Here's where we do the min/max for BRTS or nothing for BRSs.  Note that
			#  if we're doing discounting there are two methods: Kene's and Jaime's.
			#  Kene requires that we do the compmethod inside of the discounting.
			#  Jaime's does not.  Thus why the if statements are a little funky.

			# 1. If not discounting at all OR not discounting using Kene's
			#    method, do normal compMethod first
			# print('compMethod: ', compMethod)
			if not isfield(extraArgs, 'discountMode') or not strcmp(extraArgs.discountMode, 'Kene'):
				#   compMethod
				# - 'set' or 'none' to compute reachable set (not tube)
				# - 'zero' or 'minWithZero' to min Hamiltonian with zero
				# - 'minVOverTime' to do min with previous data
				# - 'maxVOverTime' to do max with previous data
				# - 'minVWithL' or 'minVWithTarget' to do min with targets
				# - 'maxVWithL' or 'maxVWithTarget' to do max with targets
				# - 'minVWithV0' to do min with original data (default)
				# - 'maxVWithV0' to do max with original data

				if strcmp(compMethod, 'zero') or strcmp(compMethod, 'set') or compMethod is None:
					# note: compMethod 'zero' is handled at the beginning of
					# the code. compMethod 'set' and 'none' require no
					# computation.
					pass
				elif strcmp(compMethod, 'minVOverTime'):  #Min over Time
					# print(f'y minOverTime: {y.shape}, {yLast.shape}')
					y = np.minimum(y, yLast)
					# print(f'y minOverTime aft: {y}, {yLast.shape}')
				elif strcmp(compMethod, 'maxVOverTime'):
					y = np.maximum(y, yLast)
				elif strcmp(compMethod, 'minVWithV0'): #Min with data0
					y = np.minimum(y,data0)
				elif strcmp(compMethod, 'maxVWithV0'):
					y = np.maximum(y,data0)
				elif strcmp(compMethod, 'maxVWithL')  or strcmp(compMethod, 'maxVwithL') or strcmp(compMethod, 'maxVWithTarget'):
					if not isfield(extraArgs, 'targetFunction'):
						error('Need to define target function l(x)!')
					if targets.ndim == gDim:
						y = np.maximum(y, targets)
					else:
						target_i = targets[i, ...]
						y = np.maximum(y, target_i)
				elif strcmp(compMethod, 'minVWithL') or  strcmp(compMethod, 'minVwithL') or  strcmp(compMethod, 'minVWithTarget'):
					if not isfield(extraArgs, 'targetFunction'):
						error('Need to define target function l(x)!')

					if targets.ndim == gDim:
						y = np.minimum(y, targets)
					else:
						target_i = targets[i,...]
						y = np.minimum(y, target_i)
				else:
					error('Check which compMethod you are using')

				# 2. If doing discounting but not using Kene's method, default
				#    to Jaime's method from ICRA 2019 paper
				if isfield(extraArgs, 'discountFactor') and  extraArgs.discountFactor and (not eisfield(extraArgs, 'discountMode') or strcmp(extraArgs.discountMode,'Kene')):
					y *=extraArgs.discountFactor

					if isfield(extraArgs, 'targetFunction'):
						y +=(1-extraArgs.discountFactor)*extraArgs.targets.flatten(order=DEFAULT_ORDER);
					else:
						y +=(1-extraArgs.discountFactor)*data0.flatten(order=DEFAULT_ORDER);

				# 3. If we are doing Kene's discounting from minimum discounted
				#    rewards paper, do that now and do compmethod with it
			elif isfield(extraArgs, 'discountFactor') and extraArgs.discountFactor and isfield(extraArgs, 'discountMode') and strcmp(extraArgs.discountMode,'Kene'):

				if not isfield(extraArgs, 'targetFunction'):
					error('Need to define target function l(x)!')

				# move everything below 0
				maxVal = np.max(np.abs(extraArgs.targetFunction));
				ytemp = y - maxVal;
				targettemp = extraArgs.targetFunction - maxVal;

				# Discount
				ytemp *= extraArgs.discountFactor;

				if strcmp(compMethod, 'minVWithL')  or strcmp(compMethod, 'minVwithL')  or strcmp(compMethod, 'minVWithTarget'):
					ytemp = omin(ytemp, targettemp)

				elif strcmp(compMethod, 'maxVWithL') or strcmp(compMethod, 'maxVwithL')  or strcmp(compMethod, 'maxVWithTarget'):
					# Take max
					ytemp = omax(ytemp, targettemp);
				else:
					error('check your compMethod!')

				# restore height
				y = ytemp + maxVal;
			else:
				error('check your discountFactor and discountMode')

			# "Mask" using obstacles
			if  isfield(extraArgs, 'obstacleFunction'):
				if strcmp(obsMode, 'time-varying'):
					obstacle_i = obstacles[i,...]
				y = omax(y, -obstacle_i)

			# Update target function
			if isfield(extraArgs, 'targetFunction'):
				if strcmp(targMode, 'time-varying'):
					target_i = targets[i,...]

		# Reshape value function
		data_i = y.reshape(g.shape, order=DEFAULT_ORDER)
		if keepLast:
			data = data_i
		elif lowMemory:
			if flipOutput:
				data = np.concatenate((y.reshape(g.shape, order=DEFAULT_ORDER), data), g.dim+1)
			else:
				data = np.concatenate((data, y.reshape(g.shape, order=DEFAULT_ORDER)), g.dim+1)
		else:
			data[i,...] = data_i


		# If we're stopping once converged, print how much change there was in
		# the last iteration
		if stopConverge:
			if  isfield(extraArgs,'ignoreBoundary')  and extraArgs.ignoreBoundary:
				_ , dataNew = truncateGrid(g, data_i, g.min+4*g.dx, g.max-4*g.dx);
				change = np.max(np.abs(dataNew.flatten()-dataTrimmed.flatten()));
				dataTrimmed = dataNew;
				if not quiet:
					info(f'Max change since last iteration: {change}')
			else:
				# check this
				change = np.max(np.abs(y - expand(y0.flatten(order=DEFAULT_ORDER), 1)));
				if not quiet:
					info(f'Max change since last iteration: {change}')

		## If commanded, stop the reachable set computation once it contains
		# the initial state.
		if isfield(extraArgs, 'stopInit'):
			initValue = eval_u(g, data_i, extraArgs.stopInit)
			if not np.isnan(initValue) and initValue <= 0:
				extraOuts.stoptau = tau[i]
				tau = tau[:i+1]

				if not lowMemory and not keepLast:
					data = data[i+1:size(data, gDim+1), ...]
				break

		## Stop computation if reachable set contains a "stopSet"
		if 'stopSet' in locals() or  'stopSet' in globals():
			dataInds = np.nonzero(data_i <= stopLevel);

			if isfield(extraArgs, 'stopSetInclude'):
				stopSetFun = np.all;
			else:
				stopSetFun = np.any;


			if stopSetFun(np.isin(setInds, dataInds)):
				extraOuts.stoptau = tau[i];
				tau[i+1:] = [];

				if not lowMemory and not keepLast:
					data[i+1:size(data, gDim+1), ...] = [];

				break

		## Stop computation if we've converged
		if stopConverge and change < convergeThreshold:

			if isfield(extraArgs, 'discountFactor') and  extraArgs.discountFactor and  isfield(extraArgs, 'discountAnneal') and extraArgs.discountFactor != 1:

				if strcmp(extraArgs.discountAnneal, 'soft'):
					extraArgs.discountFactor = 1-((1-extraArgs.discountFactor)/2);

					if np.abs(1-extraArgs.discountFactor) < .00005:
						extraArgs.discountFactor = 1;

					info(f'Discount factor: {extraArgs.discountFactor}')
				elif strcmp(extraArgs.discountAnneal, 'hard') or extraArgs.discountAnneal==1:
					extraArgs.discountFactor = 1;
					info(f'Discount factor: {extraArgs.discountFactor}')

			else:
				extraOuts.stoptau = tau[i];
				tau[i+1:] = [];

				if not lowMemory and not keepLast:
					data[i+1:size(data, gDim+1), ...] = [];

				break

		# If commanded, visualize the level set.
		if (isfield(extraArgs, 'visualize')  and isbundle(extraArgs.visualize)):
			timeCount += 1
			pDims = np.count_nonzero(plotDims)
			projDims = len(projpt) if isnumeric(projpt) else (gDim - pDims)

			# Basic Checks
			if(len(plotDims) != gDim or projDims != (gDim - pDims)):
				error('Mismatch between plot and grid dimensions!');

			#---Perform Projections--------------------------------------------
			if projDims == 0:
				gPlot, dataPlot = copy.copy(g), copy.copy(data_i)
				if strcmp(obsMode, 'time-varying'):
					obsPlot = copy.copy(obstacle_i)
				if strcmp(targMode, 'time-varying'):
					targPlot = copy.copy(target_i)
			else:
				# if projpt is a cell, project each dimensions separately. This
				# allows us to take the union/intersection through some dimensions
				# and to project at a particular slice through other dimensions.
				if iscell(projpt) and len(projpt)>1:
					idx = np.nonzero(plotDims==0)[0]
					plotDimsTemp = np.ones((plotDims))
					gPlot, dataPlot = copy.copy(g), copy.copy(data_i)

					if strcmp(obsMode, 'time-varying'):
						obsPlot = copy.copy(obstacle_i)
					if strcmp(targMode, 'time-varying'):
						targPlot = copy.copy(target_i)

					for ii in range(len(idx)-1, 0, -1):
						plotDimsTemp[idx[ii]] = 0

						if strcmp(obsMode, 'time-varying'):
							_ , obsPlot = proj(gPlot, obsPlot, np.logical_not(plotDimsTemp), projpt[ii])

						if strcmp(targMode, 'time-varying'):
							_ , targPlot = proj(gPlot, targPlot, np.logical_not(plotDimsTemp), projpt[ii])

						gPlot, dataPlot = proj(gPlot, dataPlot, np.logical_not(plotDimsTemp), projpt[ii])
						plotDimsTemp = ones(1,gPlot.dim)
				else:
					print('plotDims ', plotDims)
					gPlot, dataPlot = proj(g, data_i, np.logical_not(plotDims).astype(np.int64), projpt);

					if strcmp(obsMode, 'time-varying'):
						_ , obsPlot = proj(g, obstacle_i, np.logical_not(plotDims).astype(np.int64), projpt);

					if strcmp(targMode, 'time-varying'):
						_ , targPlot = proj(g, obstacle_i, np.logical_not(plotDims).astype(np.int64), projpt);

			## Visualize Target Function/Set
			if strcmp(targMode, 'time-varying') and isfield(extraArgs.visualize, 'targetSet') and isbundle(extraArgs.visualize.targetSet):
				# visSetIm( targPlot, gPlot, extraArgs.visualize.plotColorTS, sliceLevel, eAT_visSetIm);
				raise NotImplementedError("Target Set Visualizer not Implemented.")

			#---Visualize Target Function------------------------------------------
			if  strcmp(targMode, 'time-varying')  and isfield(extraArgs.visualize, 'targetSet')  and extraArgs.visualize.targetFunction:

				# Visualize function
				visFuncIm(gPlot,targPlot, extraArgs.visualize.plotColorTF, extraArgs.visualize.plotAlphaTF);

			## Visualize Obstacle Function/Set

			#---Visualize Obstacle Set-----------------------------------------
			if strcmp(obsMode, 'time-varying') \
					and isfield(extraArgs.visualize, 'obstacleSet') \
					and extraArgs.visualize.obstacleSet:

				# Visualize obstacle set (hOS)
				visSetIm(obsPlot, gPlot, \
					extraArgs.visualize.plotColorOS, sliceLevel, eAO_visSetIm);

				if isfield(extraArgs.visualize,'plotAlphaOS'):
					extraOuts.hOS.FaceAlpha = extraArgs.visualize.plotAlphaOS;

			#---Visualize Obstacle Function------------------------------------
			if  strcmp(obsMode, 'time-varying') \
					and extraArgs.visualize.obstacleFunction:

				# Visualize function
				extraOuts.hOF= visFuncIm(gPlot,-obsPlot,\
					extraArgs.visualize.plotColorOF,\
					extraArgs.visualize.plotAlphaOF);

			## Visualize Value Function/Set
			#---Visualize Value Set Heat Map-----------------------------------
			if isfield(extraArgs.visualize, 'valueSetHeatMap') and extraArgs.visualize.valueSetHeatMap:
				extraOuts.hVSHeat = plt.imshow(np.vstack((gPlot.vs[0],gPlot.vs[1])),cmap=dataPlot,\
					vmin=clims[0], vmax=clims[-1]);
				#colorbar

			#---Visualize Value Set--------------------------------------------
			if isfield(extraArgs.visualize, 'valueSet') and extraArgs.visualize.valueSet:

				visSetIm(gPlot, dataPlot, \
					extraArgs.visualize.plotColorVS, sliceLevel, eAT_visSetIm);


			if isfield(extraArgs.visualize,'plotAlphaVS'):
				extraOuts.hVS.FaceAlpha = extraArgs.visualize.plotAlphaVS;

			#---Visualize Value Function---------------------------------------
			if isfield(extraArgs.visualize, 'valueFunction') and \
					extraArgs.visualize.valueFunction:
				# Visualize Target function (hTF)
				extraOuts.hVF= visFuncIm(gPlot,dataPlot, extraArgs.visualize.plotColorVF, extraArgs.visualize.plotAlphaVF);


			# #---Update Title---------------------------------------------------
			# if not isfield(extraArgs.visualize, 'dtTime') and not isfield(extraArgs.visualize, 'convergeTitle'):
			#     title(f't = {tNow}')
			# elif isfield(extraArgs.visualize, 'dtTime') and np.floor(\
			#         extraArgs.visualize.dtTime/((tau()-tau(1))/length(tau)))  == timeCount :
			#
			#     title(['t = ' num2str(tNow,'#4.2f') ' s'])
			#     timeCount = 0;
			# elif isfield(extraArgs,'stopConverge') and  extraArgs.stopConverge and
			#         extraArgs.,convergeTitle') and
			#         extraArgs.visualize.convergeTitle
			#     title(['t = ' num2str(tNow, '#4.2f') \
			#         ' s, max change = ' num2str(change,'#4.4f')])
			# else
			#     title(['t = ' num2str(tNow,'#4.2f') ' s'])
			#
			# drawnow;
			#
			#
			# #---Save Video, Figure---------------------------------------------
			# if extraArgs.makeVideo and extraArgs.makeVideo
			#     current_frame = getframe(gcf); #gca does just the plot
			#     writeVideo(vout,current_frame);
			#
			#
			# if extraArgs.,figFilename')
			#     export_fig(sprintf('#s#d', \
			#         extraArgs.visualize.figFilename, i), '-png')


		# ## Save the results if needed
		# if extraArgs.saveFilename
		#     if mod(i, extraArgs.saveFrequency) == 0
		#         ilast = i;
		#         save(extraArgs.saveFilename, 'data', 'tau', 'ilast', '-v7.3')


	# ## Finish up
	# if extraArgs.discountFactor and extraArgs.discountFactor
	#     extraOuts.discountFactor = extraArgs.discountFactor;


	# Time = cputime;
	# if not quiet
	#     print('Total execution time #g seconds ', Time - startTime);
	#
	#
	# if extraArgs.makeVideo and extraArgs.makeVideo
	#     vout.close

	return data, tau, extraOuts


def getNumericalFuncs(dissType='global', accuracy='medium'):
	# Dissipation
	if (dissType == 'global'):
		dissFunc = artificialDissipationGLF
	elif (dissType == 'local'):
		dissFunc = artificialDissipationLLF
	elif (dissType == 'locallocal'):
		dissFunc = artificialDissipationLLLF
	else:
		error('Unknown dissipation function #s'.format(dissType))

	# Accuracy
	if accuracy is 'low':
		derivFunc = upwindFirstFirst
		integratorFunc = odeCFL1
	elif accuracy is 'medium':
		derivFunc = upwindFirstENO2
		integratorFunc = odeCFL2
	elif accuracy is 'high':
		derivFunc = upwindFirstENO3
		integratorFunc = odeCFL3
	elif accuracy is 'veryHigh':
		derivFunc = upwindFirstWENO5
		integratorFunc = odeCFL3
	else:
		error(f'Unknown accuracy level {accuracy}')

	return dissFunc, integratorFunc, derivFunc
