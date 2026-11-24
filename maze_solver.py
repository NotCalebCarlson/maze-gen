from flags import flag, process_flags, program_flags
from random import random
import pygame

MINIMUM_PATH_LENGTH = 50

PROBABILITIES = [
    ("Forward", 10),
    ("Left", 2),
    ("Right", 2),
    ("Tee Right", 0.1),
    ("Tee Left", 0.1),
    ("Tee", 0.1),
    ("Cross", 0.1),
    ("Dead", 0.1)
]

class MazeCell:
    """ A class representing a single cell in the maze.
    """
    def __init__(self, coord):
        self.path_length = None
        self.type = None
        self.coord = coord
        self.wall_ref = None

    def __str__(self):
        match self.type:
            case "Wall":
                return "#"#str(self.wall_ref.id % 10)
            case "Hall":
                return " "
            case "Start":
                return "S"
            case "End":
                return "E"
            case "Trace":
                return "."
            case None:
                return "`"
            case _:
                return "?"


class MazeWall:
    """ A simple class representing a continuous wall in the maze.
    """
    reference_IDs = [0,]

    def __init__(self, coordinates = None, is_master = False):
        MazeWall.reference_IDs.append(MazeWall.reference_IDs[-1] + 1)
        self.id = MazeWall.reference_IDs[-1]
        self.is_master = is_master
        if not coordinates:
            self.sibling_cells = []
            return
        self.sibling_cells = [coordinates,]

    def __eq__(self, other):
        if isinstance(other, MazeWall):
            return self.id == other.id
        else:
            return self.id == other

    def merge(self, other, maze_state):
        """ Merges this wall with another wall while updating the references of the old wall.
        Args:
            other: The old wall.
            maze_state: The state of the maze.
        """
        if self == other:
            raise Exception("Wall was merged into self.")
        if other.is_master and self.is_master:
            raise Exception("LR Wall was merged into itself.")
            return -1
        if other.is_master:
            self.is_master = True
        for coordinate in other.sibling_cells:
            self.sibling_cells.append(coordinate)
            cell = maze_state[coordinate[0]][coordinate[1]]
            cell.wall_ref = self


def create_choice_priorities():
    """ This function will create a pseudo random prioritized list based on
    the relative probability paramaters set in the simulation. 
    """
    priority_list = []
    remaining_choices = PROBABILITIES[:]
    for _ in range(8):
        spread = sum([choice[1] for choice in remaining_choices])
        pick = random() * spread
        pointer = 0
        choice = remaining_choices[pointer]
        sum_choices = choice[1]
        while sum_choices < pick:
            pointer += 1
            choice = remaining_choices[pointer]
            sum_choices += choice[1]
        priority_list.append(choice[0])
        remaining_choices.pop(pointer)
    return priority_list


def print_maze(maze):
    """Prints a string representation of a maze to the console.
    """
    width = len(maze)
    height = len(maze[0])

    for y in range(height):
        for x in range(width):
            print(maze[x][y], end = " ")
        print("")


def get_window(x, y, maze_state):
    """This function will return a window cutout of the maze state centered at x, y.

    Args:
        x: The x center of the window
        y: The y center of the window
        maze_state: The state of the maze

    Returns:
        A 3*3 list cut-out of the maze_state
    """
    return [maze_state[x_slice][y-1:y+2] for x_slice in range(x-1,x+2)]


def rotate_window(window, rotation_count):
    """ Rotates a 3*3 list clockwise a specified number of times.

    Args:
        window: The 3*3 list to be rotated.
        rotation_count: The number of times to be rotated.
    """
    if rotation_count == 0:
        return window
    new_window = [[section[-i] for section in window] for i in range(1, 4)]
    return rotate_window(new_window, rotation_count - 1)


def can_go_forward(window):
    """ Returns True if the growing hallway can go forwards
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[1][0].type == "Wall":
        return False

    if window[2][1].type != "Wall" and \
        ((window[2][2].wall_ref == window[2][0].wall_ref) or \
        (window[2][2].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False

    if window[0][1].type != "Wall" and \
        ((window[0][2].wall_ref == window[0][0].wall_ref) or \
        (window[0][2].wall_ref.is_master + window[0][0].wall_ref.is_master == 2)):
        return False
    
    return True


def can_go_right(window):
    """ Returns True if the growing hallway can go right
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[2][1].type == "Wall":
        return False

    if window[1][0].type != "Wall" and \
        ((window[0][0].wall_ref == window[2][0].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False

    if window[0][1].type != "Wall" and \
        ((window[0][2].wall_ref == window[0][0].wall_ref) or \
        (window[0][2].wall_ref.is_master + window[0][0].wall_ref.is_master == 2)):
        return False

    if (window[0][1].type != "Wall" or window[1][0].type != "Wall") and (window[0][2].wall_ref == window[2][0].wall_ref or \
        window[0][2].wall_ref.is_master + window[2][0].wall_ref.is_master == 2):
        return False
    
    return True


def can_go_left(window):
    """ Returns True if the growing hallway can go left
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[0][1].type == "Wall":
        return False

    if window[1][0].type != "Wall" and \
        ((window[0][0].wall_ref == window[2][0].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False

    if window[2][1].type != "Wall" and \
        ((window[2][2].wall_ref == window[2][0].wall_ref) or \
        (window[2][2].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False

    if (window[1][0].type != "Wall" or window[2][1].type != "Wall") and (window[0][0].wall_ref == window[2][2].wall_ref or \
        window[0][0].wall_ref.is_master + window[2][2].wall_ref.is_master == 2):
        return False
    
    return True


def can_go_tee_right(window):
    """ Returns True if the growing hallway can tee right
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[1][0].type == "Wall" or window[2][1].type == "Wall":
        return False

    if window[0][1].type != "Wall" and \
        ((window[0][0].wall_ref == window[0][2].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[0][2].wall_ref.is_master == 2)):
        return False
    
    return True

def can_go_tee_left(window):
    """ Returns True if the growing hallway can tee left
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[1][0].type == "Wall" or window[0][1].type == "Wall":
        return False

    if window[2][1].type != "Wall" and \
        ((window[2][0].wall_ref == window[2][2].wall_ref) or \
        (window[2][0].wall_ref.is_master + window[2][2].wall_ref.is_master == 2)):
        return False
    
    return True

def can_go_tee(window):
    """ Returns True if the growing hallway can tee
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[0][1].type == "Wall" or window[2][1].type == "Wall":
        return False

    if window[1][0].type != "Wall" and \
        ((window[0][0].wall_ref == window[2][0].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False
    
    return True

def can_go_cross(window):
    """ Returns True if the growing hallway can cross
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[1][0].type == "Wall" or window[0][1].type == "Wall" or window[2][1].type == "Wall":
        return False
    
    return True


def can_go_dead(window):
    """ Returns True if the growing hallway can dead-end
    Args:
        window: The window of the maze.
    Returns:
        True or False if the specified action is possible.
    """

    if window[0][1].type != "Wall" and \
        ((window[0][0].wall_ref == window[0][2].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[0][2].wall_ref.is_master == 2)):
        return False

    if window[1][0].type != "Wall" and \
        ((window[0][0].wall_ref == window[2][0].wall_ref) or \
        (window[0][0].wall_ref.is_master + window[2][0].wall_ref.is_master == 2)):
        return False

    if window[2][1].type != "Wall" and \
        ((window[2][0].wall_ref == window[2][2].wall_ref) or \
        (window[2][0].wall_ref.is_master + window[2][2].wall_ref.is_master == 2)):
        return False

    if (window[0][1].type != "Wall" or window[1][0].type != "Wall" or window[2][1].type != "Wall") and (window[0][2].wall_ref == window[2][2].wall_ref or \
        window[0][2].wall_ref.is_master + window[2][2].wall_ref.is_master + window[0][0].wall_ref.is_master + window[2][0].wall_ref.is_master >= 2):
        return False
    
    return True

def get_rotation(center, edge):
    """ Returns the number of clockwise rotations needed to point the edge 'up' from the center.
    Args:
        center: The center coordinate
        edge: The edge coordinate
    Returns:
        A number between 0 and 3 (inclusive) indicating how many times the edge would need to be rotated in order to point 'up'
    """
    x_diff = edge[0] - center[0]
    y_diff = edge[1] - center[1]

    if y_diff == 1:
        return 2
    if x_diff == -1:
        return 1
    if x_diff == 1:
        return 3
    if y_diff == -1:
        return 0
    raise Exception("Unable to determine required rotation of edge")

@flag("-g", [int, int])
def generate(width, height):
    """
    This callback function will generate a maze with a specified width and height.
    The minimum width is 3 and the minimum height is 5.
    Even dimensions will be shifted up one.

    Args:
        width: The width of the maze.
        height: The height of the maze.
    """

    width = max(3, width - ((width % 2) - 1))
    height = max(5, height - ((height % 2) - 1))

    maze_state = [[MazeCell((x, y)) for y in range(height)] for x in range(width)]
    maze_walls = [MazeWall(is_master=True), MazeWall(is_master=True)]

    maze_state[1][1].type = "Start"
    maze_state[1][1].path_length = 1
    maze_state[-2][-2].type = "End"
    maze_state[-2][-2].path_length = 1

    for i in range(width):
        maze_state[i][0].type = "Wall"
        maze_state[i][0].wall_ref = maze_walls[1]
        maze_walls[1].sibling_cells.append((i, 0))
        maze_state[i][-1].type = "Wall"
        maze_state[i][-1].wall_ref = maze_walls[0]
        maze_walls[0].sibling_cells.append((i, height - 1))

    for i in range(height - 2):
        maze_state[0][i + 1].type = "Wall"
        maze_state[0][i + 1].wall_ref = maze_walls[0]
        maze_walls[0].sibling_cells.append((0, i + 1))
        maze_state[-1][i + 1].type = "Wall"
        maze_state[-1][i + 1].wall_ref = maze_walls[1]
        maze_walls[1].sibling_cells.append((width - 1, i + 1))

    for y in range((height - 3) // 2):
        y = y * 2 + 2
        for x in range((width - 3) // 2):
            x = x * 2 + 2
            maze_walls.append(MazeWall((x, y)))
            maze_state[x][y].type = "Wall"
            maze_state[x][y].wall_ref = maze_walls[-1]

    growing_halls = [(1, 1, 3), (width - 2, height - 2, 1)]
    encased_cells = []

    while len(growing_halls) > 0:
        window_coordinates = growing_halls.pop(0)
        window = get_window(window_coordinates[0], window_coordinates[1], maze_state)
        window = rotate_window(window, window_coordinates[2])

        if window[1][1].type == "Hall":
            continue
        else:
            if window[1][1].type not in ["Start", "End"]:
                window[1][1].type = "Hall"

        priorities = create_choice_priorities()

        if not can_go_forward(window):
            priorities.remove("Forward")
        if not can_go_right(window):
            priorities.remove("Right")
        if not can_go_left(window):
            priorities.remove("Left")
        if not can_go_tee_right(window):
            priorities.remove("Tee Right")
        if not can_go_tee_left(window):
            priorities.remove("Tee Left")
        if not can_go_tee(window):
            priorities.remove("Tee")
        if not can_go_cross(window):
            priorities.remove("Cross")
        if not can_go_dead(window):
            priorities.remove("Dead")

        current_path_length = window[1][1].path_length

        if current_path_length < MINIMUM_PATH_LENGTH:
            if "Forward" in priorities or "Right" in priorities or "Left" in priorities:
                for choice in ["Tee Right", "Tee Left", "Tee", "Cross", "Dead"]:
                    try:
                        priorities.remove(choice)
                    except:
                        pass
        
        if len(priorities) == 0:
            encased_cells.append(window[1][1].coord)
            print("FOUND ENCASED")
            continue

        choice = priorities[0]
        continuations = []

        match choice:
            case "Forward":
                if window[0][1].type != "Wall":
                    window[0][1].type = "Wall"
                    window[0][1].wall_ref = MazeWall(window[0][1].coord)
                    window[0][0].wall_ref.merge(window[0][1].wall_ref, maze_state)
                    window[0][2].wall_ref.merge(window[0][1].wall_ref, maze_state)
                if window[2][1].type != "Wall":
                    window[2][1].type = "Wall"
                    window[2][1].wall_ref = MazeWall(window[2][1].coord)
                    window[2][0].wall_ref.merge(window[2][1].wall_ref, maze_state)
                    window[2][2].wall_ref.merge(window[2][1].wall_ref, maze_state)
                
                continuations = ["Forward"]
                window[1][0].path_length = current_path_length + 1
                window[1][0].type = "Hall"

            case "Right":
                if window[0][1].type != "Wall":
                    window[0][1].type = "Wall"
                    window[0][1].wall_ref = MazeWall(window[0][1].coord)
                    window[0][0].wall_ref.merge(window[0][1].wall_ref, maze_state)
                    window[0][2].wall_ref.merge(window[0][1].wall_ref, maze_state)
                if window[1][0].type != "Wall":
                    window[1][0].type = "Wall"
                    window[1][0].wall_ref = MazeWall(window[1][0].coord)
                    window[0][0].wall_ref.merge(window[1][0].wall_ref, maze_state)
                    window[1][0].wall_ref.merge(window[2][0].wall_ref, maze_state)
                continuations = ["Right"]
                window[2][1].path_length = current_path_length + 1
                window[2][1].type = "Hall"

            case "Left":
                if window[2][1].type != "Wall":
                    window[2][1].type = "Wall"
                    window[2][1].wall_ref = MazeWall(window[2][1].coord)
                    window[2][0].wall_ref.merge(window[2][1].wall_ref, maze_state)
                    window[2][1].wall_ref.merge(window[2][2].wall_ref, maze_state)
                if window[1][0].type != "Wall":
                    window[1][0].type = "Wall"
                    window[1][0].wall_ref = MazeWall(window[1][0].coord)
                    window[0][0].wall_ref.merge(window[1][0].wall_ref, maze_state)
                    window[1][0].wall_ref.merge(window[2][0].wall_ref, maze_state)
                continuations = ["Left"]
                window[0][1].path_length = current_path_length + 1
                window[0][1].type = "Hall"

            case "Tee Right":
                if window[0][1].type != "Wall":
                    window[0][1].type = "Wall"
                    window[0][1].wall_ref = MazeWall(window[0][1].coord)
                    window[0][0].wall_ref.merge(window[0][1].wall_ref, maze_state)
                    window[0][2].wall_ref.merge(window[0][1].wall_ref, maze_state)
                continuations = ["Right", "Forward"]
                window[1][0].path_length = 0
                window[2][1].path_length = 0
                window[1][0].type = "Hall"
                window[2][1].type = "Hall"

            case "Tee Left":
                if window[2][1].type != "Wall":
                    window[2][1].type = "Wall"
                    window[2][1].wall_ref = MazeWall(window[2][1].coord)
                    window[2][0].wall_ref.merge(window[2][1].wall_ref, maze_state)
                    window[2][1].wall_ref.merge(window[2][2].wall_ref, maze_state)
                continuations = ["Left", "Forward"]
                window[1][0].path_length = 0
                window[0][1].path_length = 0
                window[1][0].type = "Hall"
                window[0][1].type = "Hall"

            case "Tee":
                if window[1][0].type != "Wall":
                    window[1][0].type = "Wall"
                    window[1][0].wall_ref = MazeWall(window[1][0].coord)
                    window[0][0].wall_ref.merge(window[1][0].wall_ref, maze_state)
                    window[1][0].wall_ref.merge(window[2][0].wall_ref, maze_state)
                continuations = ["Left", "Right"]
                window[0][1].path_length = 0
                window[2][1].path_length = 0
                window[0][1].type = "Hall"
                window[2][1].type = "Hall"

            case "Cross":
                continuations = ["Right", "Left", "Forward"]
                window[1][0].path_length = 0
                window[0][1].path_length = 0
                window[2][1].path_length = 0
                window[1][0].type = "Hall"
                window[0][1].type = "Hall"
                window[2][1].type = "Hall"

            case "Dead":
                if window[2][1].type != "Wall":
                    window[2][1].type = "Wall"
                    window[2][1].wall_ref = MazeWall(window[2][1].coord)
                    window[2][0].wall_ref.merge(window[2][1].wall_ref, maze_state)
                    window[2][1].wall_ref.merge(window[2][2].wall_ref, maze_state)

                if window[0][1].type != "Wall":
                    window[0][1].type = "Wall"
                    window[0][1].wall_ref = MazeWall(window[0][1].coord)
                    window[0][0].wall_ref.merge(window[0][1].wall_ref, maze_state)
                    window[0][1].wall_ref.merge(window[0][2].wall_ref, maze_state)

                if window[1][0].type != "Wall":
                    window[1][0].type = "Wall"
                    window[1][0].wall_ref = MazeWall(window[1][0].coord)
                    window[0][0].wall_ref.merge(window[1][0].wall_ref, maze_state)
                    window[1][0].wall_ref.merge(window[2][0].wall_ref, maze_state)

            case _:
                raise Exception("No matching choices were found.")

        for continuation in continuations:
            match continuation:
                case "Forward":
                    next_path_length = window[1][0].path_length + 1
                    next_x = window[1][0].coord[0] - (window[1][1].coord[0] - window[1][0].coord[0])
                    next_y = window[1][0].coord[1] - (window[1][1].coord[1] - window[1][0].coord[1])
                    maze_state[next_x][next_y].path_length = next_path_length
                    rotation = get_rotation(window[1][1].coord, window[1][0].coord)
                    growing_halls.append((next_x, next_y, rotation))
                case "Right":
                    next_path_length = window[2][1].path_length + 1
                    next_x = window[2][1].coord[0] - (window[1][1].coord[0] - window[2][1].coord[0])
                    next_y = window[2][1].coord[1] - (window[1][1].coord[1] - window[2][1].coord[1])
                    maze_state[next_x][next_y].path_length = next_path_length
                    rotation = get_rotation(window[1][1].coord, window[2][1].coord)
                    growing_halls.append((next_x, next_y, rotation))
                case "Left":
                    next_path_length = window[0][1].path_length + 1
                    next_x = window[0][1].coord[0] - (window[1][1].coord[0] - window[0][1].coord[0])
                    next_y = window[0][1].coord[1] - (window[1][1].coord[1] - window[0][1].coord[1])
                    maze_state[next_x][next_y].path_length = next_path_length
                    rotation = get_rotation(window[1][1].coord, window[0][1].coord)
                    growing_halls.append((next_x, next_y, rotation))
                case _:
                    raise Exception("No matching continuation was found.")
        
    print_maze(maze_state)
    return maze_state

if __name__ == "__main__":
    process_flags()

    maze = generate(801, 801)

    # Based off of quickstart code from pygame.org
    pygame.init()
    screen = pygame.display.set_mode((1000, 1000))
    #surface = pygame.display.get_surface()
    clock = pygame.time.Clock()
    running = True

    screen.fill("white")
    pygame.display.flip()

    wall_width = 1
    hall_width = 2

    rect_width = wall_width
    rect_height = wall_width

    offset = 10

    x_ = offset
    y_ = offset

    for y in range(len(maze[0])):
        if y % 2 == 0:
            rect_height = wall_width
        else:
            rect_height = hall_width
        for x in range(len(maze)):
            if x % 2 == 0:
                rect_width = wall_width
            else:
                rect_width = hall_width

            if maze[x][y].type == "Wall":
                screen.fill("black", pygame.Rect(x_, y_, rect_width, rect_height))
            x_ += rect_width
        x_ = offset
        y_ += rect_height
    
    pygame.display.flip()
    while running == True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
        clock.tick(60)

    pygame.quit()

        