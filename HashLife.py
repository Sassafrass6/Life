from Tkinter import *
import numpy as np
import hashlib
import tkFont
import time


#### Patterns ####

# ----- Blinker -----
blinkerPattern = np.zeros((3,3), dtype=bool)
blinkerPattern[1,:3] = True
# -------------------

# ---- Die Hard ----
dieHardPattern = np.zeros((8,3), dtype=bool)
dieHardPattern[0:2,1] = True
dieHardPattern[1,2] = dieHardPattern[6][0] = True
dieHardPattern[5:8,2] = True
# ------------------

# ----- Glider -----
gliderPattern = np.zeros((3,3), dtype=bool)
gliderPattern[0:3,2] = True
gliderPattern[1][0] = gliderPattern[2][1] = True 
# ------------------

# --- I-Beam Pattern ---
iBeamPattern = np.zeros((3,12), dtype=bool)
ibs = [0, 3, 8, 11]
for i in ibs:
	iBeamPattern[0:4, ibs] = True
iBeamPattern[1,1:3] = True
iBeamPattern[1,9:11] = True
iBeamPattern[0:4,5:7] = True
# ----------------------

# ------ Pulsar -------
pulsarPattern = np.zeros((13,13), dtype=bool)
ps = [0, 5, 7, 12]
for i in ps:
	pulsarPattern[2:5, i] = pulsarPattern[8:11, i] = True
	pulsarPattern[i, 2:5] = pulsarPattern[i, 8:11] = True
# ---------------------

# ----- Spaceship -----
spaceshipPattern = np.zeros((4,5), dtype=bool)
spaceshipPattern[0][0] = spaceshipPattern[0][3] = spaceshipPattern[2][0] = True
spaceshipPattern[3,1:5] = spaceshipPattern[1:3,4] = True
# ---------------------

##################


class Life():

	def __init__ ( self, wHeight=400, wWidth=400, bWidth=25, pow2=4 ):

		self.gridSize = 2**pow2
		
		self.windowHeight = wHeight
		self.windowWidth = wWidth
		self.xpad = (wWidth - self.gridSize*bWidth)/2
		self.ypad = (wHeight - self.gridSize*bWidth)/2
		self.boxWidth = bWidth
		
		# Simulation starts paused
		self.running = False

		# Duration between frame updates
		self.speed = 100

		# Flag determining weather the frame should be drawn
		self.uframe = False
		if self.uframe:
			self.ypad = wHeight / 10
		
		# Stores references to cells drawn in the window
		self.cells = [[None for _ in np.arange(self.gridSize)] for _ in np.arange(self.gridSize)]
		
		# Hash map for precomputed patterns
		self.lifePatterns = {}

		# 2D Matrices holding the current state and the temporary next state
		self.life = np.zeros((self.gridSize, self.gridSize), dtype=bool)
		self.tlife = np.zeros_like(self.life)
		
		# 2D Matrix denoting cells that need to be redrawn
		self.ulife = np.ones_like(self.life)
		
		self.setup_tkinter_window()

		# Draw the game board
		if self.uframe:
			self.draw_frame()
		self.draw_border()
		self.draw_grid(1, self.gridSize-1, 1, self.gridSize-1)

		# OPTIONAL:  Add patterns to empty grid
#		self.draw_pattern(blinkerPattern, 1, 1)
#		self.draw_pattern(dieHardPattern, 30, 30)
#		self.draw_pattern(gliderPattern, 1, 1)
#		self.draw_pattern(iBeamPattern, 15, 10)
#    self.draw_pattern(pulsarPattern, 13, 16)
#		self.draw_pattern(spaceshipPattern, 1, 1)

		# Game loop
		while True:
			try:
				if self.running:
					ttime = time.time()
					self.update_grid((0, 0), pow2)
					print time.time() - ttime
				self.canvas.after(self.speed)
				self.canvas.update()
			except TclError:
				return


#### Game Logic ####

	# Solves a 4x4 grid and determines the new state of the inner 2x2 grid
	def solve_grid ( self, xmin, xmax, ymin, ymax ):
		newlife = np.zeros((2, 2), dtype=bool)
		
		# For each of the 4 cells interior to the 4x4 grid apply Conway's 4 rules
		for x in np.arange(xmin+1, xmax-1, 1):
			for y in np.arange(ymin+1, ymax-1, 1):
				
				liveNeighbors = np.sum(self.life[x-1:x+2,y-1:y+2])-self.tlife[x][y]
							
				if self.life[x][y]:
					if liveNeighbors < 2 or liveNeighbors > 3:
						newlife[x-xmin-1][y-ymin-1] = False
					else:
						newlife[x-xmin-1][y-ymin-1] = True
				else:
					if liveNeighbors == 3:
						newlife[x-xmin-1][y-ymin-1] = True
					else:
						newlife[x-xmin-1][y-ymin-1] = False
		# Return the 2x2 interior grid
		return newlife[:,:]
		
	# Return a unique string identifier representing the state of the board
	def hash_life ( self, life ):
		hView = life[:, :].tostring()
		return hashlib.sha1(hView).hexdigest()

	# Update the life grid recursively
	def update_grid ( self, startXY, pow2 ):
		# Size of this layer
		size = 2**pow2
		
		# Hash ID of this layer
		hid = self.hash_life(self.life[startXY[0]:startXY[0]+size, startXY[1]:startXY[1]+size])
		
		# If ID already exists copy the pattern onto the temporary grid
		if hid in self.lifePatterns:
			self.tlife[startXY[0]+1:startXY[0]+size-1, startXY[1]+1:startXY[1]+size-1] = self.lifePatterns[hid][:,:]
			
			# If this is the top layer redraw any modified cells
			if size == self.gridSize:
				self.draw_modified_cells()
			return
		
		# The hash ID does not already exist
		else:
			# 4 is the smallest size block which fully determines the next state of an interior box.
			# Save the solved 4x4 grid into the hash map and set self.tlife to reflect the next generation.
			if size == 4:
				self.lifePatterns[hid] = self.solve_grid(startXY[0], startXY[0]+size, startXY[1], startXY[1]+size)
				self.tlife[startXY[0]+1:startXY[0]+size-1, startXY[1]+1:startXY[1]+size-1] = self.lifePatterns[hid][:,:]
				return
			
			# If the block size is greater than 4, break it into 9 inner boxes,
			#  each with side_length = fourths = pow2-1 = size/2 and overlapping the previous by 1 box.
			fourths = size/4
			offset = 2**(pow2-3)
			# Iterate over the boxes
			for i in np.arange(0, 3*fourths, fourths):
				for j in np.arange(0, 3*fourths, fourths):
					msize = 2**(pow2-1)
					mhid = self.hash_life(self.life[startXY[0]+i:startXY[0]+i+msize, startXY[1]+j:startXY[1]+j+msize])
					
					# If the hash pattern exists copy the pattern to self.tlife
					if mhid in self.lifePatterns:
						self.tlife[startXY[0]+i+1:startXY[0]+i+msize-1, startXY[1]+j+1:startXY[1]+j+msize-1] = self.lifePatterns[mhid][:,:]
					# Otherwise compute the pattern recursively and store it in the hash map
					else:
						self.update_grid((startXY[0]+i, startXY[1]+j), pow2-1)
						self.lifePatterns[mhid] = np.empty((msize-2, msize-2), dtype=bool)
						self.lifePatterns[mhid][:,:] = self.tlife[startXY[0]+i+1:startXY[0]+i+msize-1, startXY[1]+j+1:startXY[1]+j+msize-1]

			# If this is the top layer, hash the computed pattern and redraw any modified cells
			if size == self.gridSize:
				self.lifePatterns[hid] = np.empty((size-2, size-2), dtype=bool)
				self.lifePatterns[hid][:,:] = self.tlife[1:size-1,1:size-1]
				self.draw_modified_cells()


	#### Drawing Functions ####

	# Draw single cell
	def draw_cell ( self, i, j ):
		if self.ulife[i][j]:
			self.ulife[i][j] = False
			
			x = self.xpad + i*self.boxWidth
			y = self.ypad + j*self.boxWidth
			
			fillColor = None
			if self.life[i][j]:
				fillColor = 'black'
			else:
				fillColor = 'white'

			self.canvas.delete(self.cells[i][j])
			self.cells[i][j] = self.canvas.create_rectangle(x, y, x+self.boxWidth, y+self.boxWidth, fill=fillColor)

	# Draw a portion of the grid
	def draw_grid ( self, xmin, xmax, ymin, ymax ):
		for i in np.arange(xmin, xmax, 1):
			for j in np.arange(ymin, ymax, 1):
				self.draw_cell(i, j)
		self.canvas.update()
	
	# Draw cells that have an xor value of 1 between self.life and self.tlife
	#  then update self.life to reflect changes from the previous iteration.
	def draw_modified_cells ( self ):
		self.ulife[:,:] = np.logical_xor(self.life[:,:], self.tlife[:,:])
		self.life[:,:] = self.tlife[:,:]
		self.draw_grid(0, self.gridSize, 0, self.gridSize)

	# Draw a pattern
	# pat - 2D Numpy array of bools specifying pattern
	# x - Column of the pattern's upper left corner
	# y - Row of pattern's the upper left corner
	def draw_pattern ( self, pat, x, y ):
		xmax = x + pat.shape[0]
		ymax = y + pat.shape[1]

		if x < 1 or y < 1 or xmax > self.gridSize-1 or ymax > self.gridSize-1:
			print('Pattern out of bounds')
			return

		else:
			self.life[x:xmax, y:ymax] = pat[:,:]
			self.tlife[x:xmax, y:ymax] = pat[:,:]
			self.ulife[x:xmax, y:ymax] = True
			self.draw_grid(x, xmax, y, ymax)

	# Draw the bordering cells, which are always dead.
	def draw_border ( self ):
		for i in np.arange(self.gridSize):
			self.draw_cell(i, 0)
			self.draw_cell(i, self.gridSize-1)
		for i in np.arange(1, self.gridSize-1, 1):
			self.draw_cell(0, i)
			self.draw_cell(self.gridSize-1, i)

	# Draw a red border around the board and display text at the top
	def draw_frame ( self ):
		self.uframe = False
		self.canvas.delete(self.lifeBorder)
		self.canvas.delete(self.titleText)
		self.canvas.delete(self.speedText)
		
		twid = self.xpad+self.boxWidth*self.gridSize+1
		yo10 = self.ypad/10.
		xm1 = self.xpad-1
		self.topBorder = self.canvas.create_rectangle(xm1, self.ypad-1, twid, self.ypad+self.boxWidth*self.gridSize+1, outline='red')

		self.lifeBorder = self.canvas.create_rectangle(xm1, yo10, self.windowWidth-self.xpad+1, self.ypad-yo10, outline='red', fill='white')
		self.titleText = self.canvas.create_text(self.windowWidth/3., 5.*yo10, text='Conway\'s Game of Life', font=self.font1)
		self.speedText = self.canvas.create_text(5*self.windowWidth/6., 5.*yo10, text='Speed = %.3f'%(1./self.speed), font=self.font2)

	# Build application window, canvas, and create keybindings
	def setup_tkinter_window ( self ):
		self.root = Tk()
		self.root.wm_title("Conway's Life")
		self.font1 = tkFont.Font(family='Helvetica', size=20, weight='bold')
		self.font2 = tkFont.Font(family='Helvetica', size=14)
		self.topBorder = None
		self.tlifeBorder = None
		self.titleText = None
		self.speedText = None

		self.canvas = Canvas(self.root, width=self.windowWidth, height=self.windowHeight)
		self.canvas.pack()

		# Bind keys to functions
		self.canvas.bind_all('<p>', self.pause)
		self.canvas.bind_all('<r>', self.random_life)
		self.canvas.bind_all('<c>', self.no_life)
		self.canvas.bind_all('<q>', self.quit_key)
		self.canvas.bind_all('<Up>', self.speed_up)
		self.canvas.bind_all('<Down>', self.speed_down)
		self.canvas.bind_all('<Button-1>', self.click)



	#### Keybound Functions ####
	
	# - Click - Toggle a cell if it is clicked on
	def click ( self, event ):
		x = int(np.floor((event.x-self.xpad)/self.boxWidth))
		y = int(np.floor((event.y-self.ypad)/self.boxWidth))
		if x < self.gridSize-1 and y < self.gridSize-1 and x > 0 and y > 0:
			self.tlife[x][y] = self.life[x][y] = not self.life[x][y]
			self.ulife[x][y] = True
			self.draw_cell(x, y)
			self.canvas.update()
	
	# 'c' - Remove all life from the game grid
	def no_life ( self, event ):
		self.tlife = np.zeros_like(self.tlife)
		self.life[:,:] = self.tlife[:,:]
		self.ulife = np.ones_like(self.tlife)
		self.draw_grid(0, self.gridSize, 0, self.gridSize)

	# 'r' - Create life randomly on the board. 50/50 : dead/alive
	def random_life ( self, event ):
		for i in np.arange(1, self.gridSize-1, 1):
			for j in np.arange(1, self.gridSize-1, 1):
				if np.round(np.random.rand()) == 1:
					self.tlife[i][j] = True
				else:
					self.tlife[i][j] = False
		self.life[:,:] = self.tlife[:,:]
		self.ulife = np.ones_like(self.tlife)
		self.draw_grid(0, self.gridSize, 0, self.gridSize)
		
	# - Up Arrow - Speed up the simulation
	def speed_up ( self, event ):
		self.uframe = False
		if self.speed > 100:
			self.speed -= 100
		elif self.speed > 10:
			self.speed -= 10
		if self.uframe:
			self.draw_frame()

	# - Down Arrow - Slow down the simulation
	def speed_down ( self, event ):
		self.uframe = False
		if self.speed < 100:
			self.speed += 10
		elif self.speed < 1200:
			self.speed += 100
			if self.uframe:
				self.draw_frame()

	def pause ( self, event ):
		self.running = not self.running
	def quit ( self ):
		self.root.destroy()
	def quit_key ( self, event ):
		self.quit()
 
# Instatiate game
game = Life(wWidth=800, wHeight=800, bWidth=12, pow2=6)
