"""
This is our main driver file. It will be responsible for handling user input and displaying the current GameState object.
    """

import pygame as p
import ChessEngine, SmartMoveFinder

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 #for animation later on
IMAGES = {}

"""
Initialize a global dictionary of images. This will be called exactly once in the main because of the amount of memory used.
    """

def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    #Note: we can access an image by saying something like 'IMAGES["wp"]'
    
"""
The main driver for our code. This will handle user input and updating the graphics
"""

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False #flag variable for when a move is made 
    animate = False #flag variable for when we should animate a move
    loadImages()  # only do this once, before the while loop
    running = True
    sqSelected = () # No square is selected initially, keep track of the last click of the user (tuple: (row, col))
    playerClicks = [] # keep track of player clicks (two tuples: [(6,4),(4,4)])
    gameOver = False
    playerOne = True #If a human is playing white then this will be true. If an AI is playing then False.
    playerTwo = False #Same as above but for black

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get(): 
            if e.type == p.QUIT:
                running = False
            
            #Mouse handlers
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos() #(x,y) location of the mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col): # user clicked the same square twice, typically an undo action
                        sqSelected = () #deselect
                        playerClicks = [] #clear player clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected) #append for both 1st and 2nd clicks
                    #was that the user's 2nd click?
                    if len(playerClicks) == 2: #after 2nd click
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board) #starting, ending squares and board
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = () #reset user clicks
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            #Key handlers
            elif e.type == p.KEYDOWN: 
                if e.key == p.K_z: # Undo when 'z' is pressed
                    gs.undoMove()
                    moveMade = True #validMoves = gs.getValidMoves()
                    animate = False
                    gameOver = False
                if e.key == p.K_r: #reset the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
        
        #AI move finder
        if not gameOver and not humanTurn:
            AIMove = SmartMoveFinder.findBestMove(gs, validMoves)
            if AIMove is None:
                AIMove = SmartMoveFinder.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True 
        
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False 

        drawGameState(screen, gs, validMoves, sqSelected)  # Update the screen
        
        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "Black Wins by Checkmate")
            else:
                drawText(screen, "White Wins by Checkmate")
        elif gs.staleMate:
            gameOver = True
            drawText(screen, "Stalemate")
            
        clock.tick(MAX_FPS)
        p.display.flip()

"""
Highlights square selected and moves for piece selected
"""
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"): #sqSelected is a piece that can be moved
            #highlight the selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) #gives you a transparency value (0:transparent & 255:opaque)
            s.fill(p.Color("blue"))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            #highlight moves from that square
            s.fill(p.Color("pink"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


"""
Responsible for all the graphics within the current game state.
"""

def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) #draw the square on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board) # draw pieces on top of the squares 
    

"""
Draw the squares on the board. The top left square is always light.
"""

def drawBoard(screen):
    global colors
    colors = [p.Color("light blue"), p.Color("white")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

"""
Will draw pieces on the board using the current GameState.board 
"""
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": #Not empty square
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE)) #blit() means drawing one surface on another

def animateMove(move, screen, board, clock):
    global colors
    coords = [] #list of coordinates that the animation will move through
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10 #frames to move one square
    frameCount = (abs(dR)) + (abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        #erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        #draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color("Pink"))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color("Red"))
    screen.blit(textObject, textLocation.move(2, 2))

if __name__ == "__main__":
    main()