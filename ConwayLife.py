from Tkinter import *
import tkFont
import time
import numpy as np


#### Patterns ####

# --- Glider ---
gliderPattern = np.zeros((3,3), dtype=bool)
gliderPattern[0:3,2] = True
gliderPattern[1][0] = gliderPattern[2][1] = True 
# --------------

# -- Spaceship --
spaceshipPattern = np.zeros((4,5), dtype=bool)
spaceshipPattern[0][0] = spaceshipPattern[0][3] = spaceshipPattern[2][0] = True
spaceshipPattern[3,1:5] = spaceshipPattern[1:3,4] = True
# ---------------

# --- Blinker ---
blinkerPattern = np.zeros((3,3), dtype=bool)
blinkerPattern[1,:3] = True
# ---------------

##################


class Life():

  def __init__ ( self, wHeight=400, wWidth=400, bWidth=25, nX=0, nY=0 ):
    self.windowHeight = wHeight
    self.windowWidth = wWidth
    self.xpad = wWidth / 40
    self.ypad = wHeight / 40
    self.boxWidth = bWidth

    # Fill window with cells if nX and nY are not specified
    if nX == 0 or nY == 0:
      self.gridSizeX = (self.windowWidth - self.xpad)/self.boxWidth
      self.gridSizeY = (self.windowHeight - self.ypad)/self.boxWidth
    else:
      self.gridSizeX = nX
      self.gridSizeY = nY
    
    # Simulation starts paused
    self.running = False

    # Duration between frame updates
    self.speed = 100

    # Flag determining weather the frame should be drawn
    self.uframe = False
    if self.uframe:
      self.ypad = wHeight / 10
    
    # Stores references to cells drawn in the window
    self.cells = [[None for _ in np.arange(self.gridSizeY)] for _ in np.arange(self.gridSizeX)]

    # 2D Matrices holding the current state and the temporary next state
    self.life = np.zeros((self.gridSizeX, self.gridSizeY), dtype=bool)
    self.tlife = np.zeros_like(self.life)
    
    # 2D Matrix denoting cells that need to be redrawn
    self.ulife = np.ones_like(self.life)
    
    self.tlife[:,:] = self.life[:,:]
    
    self.setup_tkinter_window()

    # Draw the game board
    if self.uframe:
      self.draw_frame()
    self.draw_border()
    self.draw_grid(1, self.gridSizeX-1, 1, self.gridSizeY-1)

    # OPTIONAL:  Add patterns to empty grid
    self.draw_pattern(spaceshipPattern, 1, 1)
    self.draw_pattern(gliderPattern, 8, 1)
    self.draw_pattern(gliderPattern, 14, 1)
    self.draw_pattern(gliderPattern, 20, 1)

    # Game loop
    while True:
      try:
        if self.running:
          self.update_grid()
        self.canvas.after(self.speed)
        self.canvas.update()
      except TclError:
        return   


  #### Game Logic ####

  # Calculates the number of live cells around the cell at x, y and updates according to Conway's rules
  def update_cell ( self, x, y ):
    
    liveNeighbors = np.sum(self.life[x-1:x+2,y-1:y+2])-self.life[x][y]
    
    if self.life[x][y]:
      if liveNeighbors < 2:
        self.tlife[x][y] = False
        self.ulife[x][y] = True
      elif liveNeighbors > 3:
        self.tlife[x][y] = False
        self.ulife[x][y] = True
    else:
      if liveNeighbors == 3:
        self.tlife[x][y] = True
        self.ulife[x][y] = True

  # Iterates across board and updates the cells for the next generation
  def update_grid ( self ):
    # A 3x3 block is checked for dead cells to skip cells that cannot evolve in the current generation.
    # whiteBack - Only dead cells in row behind current position
    # whiteCur - Only dead cells in current row
    # whiteFront - Only dead cells in front of current position
    for i in np.arange(1, self.gridSizeX-1, 1):
      whiteBack = True
      whiteCur = False
      if not self.life[i-1:i+2,1].any():
        whiteCur = True

      for j in np.arange(1, self.gridSizeY-1, 1):
        if not self.life[i-1:i+2,j+1].any():
          whiteFront = True
        else:
          whiteFront = False

        if self.running and not (whiteBack and whiteCur and whiteFront):
          self.update_cell(i, j)

        if self.ulife[i][j]:
          self.ulife[i][j] = False
          self.draw_cell(i, j)

        # Current row becomes Back row
        # Front row becomes Current row
        whiteBack = whiteCur
        whiteCur = whiteFront

    # Update game board with new states
    self.life[:,:] = self.tlife[:,:]


  #### Drawing Functions ####

  # Draw single cell
  def draw_cell ( self, i, j ):
    x = self.xpad + i*self.boxWidth
    y = self.ypad + j*self.boxWidth

    fillColor = None
    if self.tlife[i][j]:
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

  # Draw a pattern
  # pat - 2D Numpy array of bools specifying pattern
  # x - Column of the pattern's upper left corner
  # y - Row of pattern's the upper left corner
  def draw_pattern ( self, pat, x, y ):
    xmax = x + pat.shape[0]
    ymax = y + pat.shape[1]

    if x < 1 or y < 1 or xmax > self.gridSizeX-1 or ymax > self.gridSizeY-1:
      print('Pattern out of bounds')
      return

    else:
      self.life[x:xmax, y:ymax] = pat[:,:]
      self.tlife[x:xmax, y:ymax] = pat[:,:]
      self.ulife[x:xmax, y:ymax] = True
      self.draw_grid(x, xmax, y, ymax)

  # Draw the bordering cells, which are always dead.
  def draw_border ( self ):
    for i in np.arange(self.gridSizeX):
      self.draw_cell(i, 0)
      self.draw_cell(i, self.gridSizeY-1)
    for i in np.arange(1, self.gridSizeY-1, 1):
      self.draw_cell(0, i)
      self.draw_cell(self.gridSizeX-1, i)

  # Draw a red border around the board and display text at the top
  def draw_frame ( self ):
    self.uframe = False
    self.canvas.delete(self.tlifeBorder)
    self.canvas.delete(self.titleText)
    self.canvas.delete(self.speedText)
    
    twid = self.xpad+self.boxWidth*self.gridSizeX+1
    yo10 = self.ypad/10.
    xm1 = self.xpad-1
    self.topBorder = self.canvas.create_rectangle(xm1, self.ypad-1, twid, self.ypad+self.boxWidth*self.gridSizeY+1, outline='red')

    self.tlifeBorder = self.canvas.create_rectangle(xm1, yo10, self.windowWidth-self.xpad+1, self.ypad-yo10, outline='red', fill='white')
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
    if x < self.gridSizeX-1 and y < self.gridSizeY-1 and x > 0 and y > 0:
      self.tlife[x][y] = self.life[x][y] = not self.life[x][y]
      self.ulife[x][y] = True
      self.draw_cell(x, y)
      self.canvas.update()
  
  # 'c' - Remove all life from the game grid
  def no_life ( self, event ):
    self.tlife = np.zeros_like(self.tlife)
    self.life[:,:] = self.tlife[:,:]
    self.ulife = np.ones_like(self.tlife)
    self.draw_grid(0, self.gridSizeX, 0, self.gridSizeY)

  # 'r' - Create life randomly on the board. 50/50 : dead/alive
  def random_life ( self, event ):
    for i in np.arange(1, self.gridSizeX-1, 1):
      for j in np.arange(1, self.gridSizeY-1, 1):
        if np.round(np.random.rand()) == 1:
          self.tlife[i][j] = True
        else:
          self.tlife[i][j] = False
    self.life[:,:] = self.tlife[:,:]
    self.ulife = np.ones_like(self.tlife)
    self.draw_grid(0, self.gridSizeX, 0, self.gridSizeY)
    
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
game = Life(wWidth=800, wHeight=900)#, bWidth=24, nX=32, nY=32)
