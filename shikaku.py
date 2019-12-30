import enum


class CellState(enum.Enum):
    FREE = 0
    BUSY = 1


class Direction(enum.Enum):
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3


class Cell:
    def __init__(self):
        self.neighbors = {}
        self.state = CellState.FREE
        self.num = 0
        self.is_change = False

    def set_neighbor(self, direction, x, y):
        if direction not in self.neighbors:
            self.neighbors[direction] = (x, y)

    def set_num(self, n):
        self.num = n
        self.state = CellState.BUSY


class Field:
    def __init__(self, height, length, width):
        self.cells = {}
        self.start_height = height
        self.start_length = length
        self.start_width = width
        self.height = height + length * 2
        self.width = width * 2 + length * 2
        low_border = self.start_length - 1
        high_border = self.start_length + self.start_height
        for x in range(self.width):
            for y in range(self.height):
                if low_border < y < high_border or x < self.start_width:
                    self.cells[(x, y)] = Cell()

    def __str__(self):
        res = ''
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.cells:
                    res += "%-5s" % (str(self.cells[(x, y)].num))
            res += "\n"
        return res

    def is_full(self):
        for coord in self.cells:
            if self.cells[coord].num == 0:
                return False
        return True

    def find_neighbors(self, x, y):
        width = self.start_width
        length = self.start_length
        height = self.start_height
        right = Direction.RIGHT
        left = Direction.LEFT
        top = Direction.TOP
        bottom = Direction.BOTTOM
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) > 0 and (x + dx, y + dy) in self.cells:
                    if dx == 1 and dy == 0:
                        self.cells[(x, y)].set_neighbor(right, x + dx, y + dy)
                    if dx == -1 and dy == 0:
                        self.cells[(x, y)].set_neighbor(left, x + dx, y + dy)
                    if dx == 0 and dy == 1:
                        self.cells[(x, y)].set_neighbor(top, x + dx, y + dy)
                    if dx == 0 and dy == -1:
                        self.cells[(x, y)].set_neighbor(bottom, x + dx, y + dy)
        if y == length and x >= width:
            if width <= x < width + length:
                x2 = width - 1
                y2 = length - 1 - (x - width)
                self.cells[(x, y)].set_neighbor(bottom, x2, y2)
                self.cells[(x2, y2)].set_neighbor(right, x, y)
            if width + length <= x < 2 * width + length:
                x2 = width - 1 - (x - width - length)
                self.cells[(x, y)].set_neighbor(bottom, x2, 0)
                self.cells[(x2, 0)].set_neighbor(bottom, x, y)
            if x >= 2 * width + length:
                y2 = x - width * 2 - length
                self.cells[(x, y)].set_neighbor(bottom, 0, y2)
                self.cells[(0, y2)].set_neighbor(left, x, y)
        if y == length + height - 1 and x >= width:
            if width <= x < width + length:
                x2 = width - 1
                y2 = length + height + (x - width)
                self.cells[(x, y)].set_neighbor(top, x2, y2)
                self.cells[(x2, y2)].set_neighbor(right, x, y)
            if width + length <= x < 2 * width + length:
                x2 = 2 * width - 1 - (x - length)
                y2 = 2 * length + height - 1
                self.cells[(x, y)].set_neighbor(top, x2, y2)
                self.cells[(x2, y2)].set_neighbor(top, x, y)
            if x >= 2 * width + length:
                y2 = 4 * length + height - 1 - (x - width)
                self.cells[(x, y)].set_neighbor(top, 0, y2)
                self.cells[(0, y2)].set_neighbor(left, x, y)
        if x == 2 * width + 2 * length - 1:
            self.cells[(x, y)].set_neighbor(right, 0, y)
        if x == 0:
            x2 = 2 * width + 2 * length - 1
            self.cells[(x, y)].set_neighbor(left, x2, y)

    def direction_changer(
            self, x1, y1, x2, y2, old_dir=None):  # x1, y1 -> x2, y2
        changer = {}
        w = self.start_width
        length = self.start_length
        height = self.start_height
        if old_dir:
            changer = old_dir
        else:
            changer[Direction.TOP] = Direction.TOP
            changer[Direction.BOTTOM] = Direction.BOTTOM
            changer[Direction.RIGHT] = Direction.RIGHT
            changer[Direction.LEFT] = Direction.LEFT
        if y1 == length + height - 1 and x1 >= w and y2 >= length + height:
            if w <= x1 < w + length:
                changer[Direction.TOP] = Direction.LEFT
                changer[Direction.BOTTOM] = Direction.RIGHT
                changer[Direction.RIGHT] = Direction.TOP
                changer[Direction.LEFT] = Direction.BOTTOM
                return changer
            if w + length <= x1 < 2 * w + length:
                changer[Direction.TOP] = Direction.BOTTOM
                changer[Direction.BOTTOM] = Direction.TOP
                changer[Direction.RIGHT] = Direction.LEFT
                changer[Direction.LEFT] = Direction.RIGHT
                return changer
            if x1 >= 2 * w + length:
                changer[Direction.TOP] = Direction.RIGHT
                changer[Direction.BOTTOM] = Direction.LEFT
                changer[Direction.RIGHT] = Direction.BOTTOM
                changer[Direction.LEFT] = Direction.TOP
                return changer
        if y1 == length and x1 >= w and y2 < length:
            if w <= x1 < w + length:
                changer[Direction.TOP] = Direction.RIGHT
                changer[Direction.BOTTOM] = Direction.LEFT
                changer[Direction.RIGHT] = Direction.BOTTOM
                changer[Direction.LEFT] = Direction.TOP
                return changer
            if w + length <= x1 < 2 * w + length:
                changer[Direction.TOP] = Direction.BOTTOM
                changer[Direction.BOTTOM] = Direction.TOP
                changer[Direction.RIGHT] = Direction.LEFT
                changer[Direction.LEFT] = Direction.RIGHT
                return changer
            if x1 >= 2 * w + length:
                changer[Direction.TOP] = Direction.LEFT
                changer[Direction.BOTTOM] = Direction.RIGHT
                changer[Direction.RIGHT] = Direction.TOP
                changer[Direction.LEFT] = Direction.BOTTOM
                return changer
        if x1 == w - 1 and y1 >= length + height and w <= x2 < w + length:
            changer[Direction.LEFT] = Direction.TOP
            changer[Direction.RIGHT] = Direction.BOTTOM
            changer[Direction.TOP] = Direction.RIGHT
            changer[Direction.BOTTOM] = Direction.LEFT
            return changer
        if y1 == 2 * length + height - 1 and w + length <= x2 < 2 * w + length:
            changer[Direction.BOTTOM] = Direction.TOP
            changer[Direction.TOP] = Direction.BOTTOM
            changer[Direction.LEFT] = Direction.RIGHT
            changer[Direction.RIGHT] = Direction.LEFT
            return changer
        if x1 == 0 and y1 >= length + height and x2 >= 2 * w + length:
            changer[Direction.RIGHT] = Direction.TOP
            changer[Direction.LEFT] = Direction.BOTTOM
            changer[Direction.BOTTOM] = Direction.RIGHT
            changer[Direction.TOP] = Direction.LEFT
            return changer
        if y1 < length and x1 == w - 1 and w <= x2 < w + length:
            changer[Direction.RIGHT] = Direction.TOP
            changer[Direction.LEFT] = Direction.BOTTOM
            changer[Direction.BOTTOM] = Direction.RIGHT
            changer[Direction.TOP] = Direction.LEFT
            return changer
        if y1 == 0 and w + length <= x2 < 2 * w + length:
            changer[Direction.BOTTOM] = Direction.TOP
            changer[Direction.TOP] = Direction.BOTTOM
            changer[Direction.LEFT] = Direction.RIGHT
            changer[Direction.RIGHT] = Direction.LEFT
            return changer
        if y1 < length and x1 == 0 and x2 >= 2 * w + length:
            changer[Direction.LEFT] = Direction.TOP
            changer[Direction.RIGHT] = Direction.BOTTOM
            changer[Direction.TOP] = Direction.RIGHT
            changer[Direction.BOTTOM] = Direction.LEFT
            return changer
        return changer

    def place_circ(self, x, y, l):
        first_dir = None
        second_dir = None
        circ = []
        if l == 1:
            return circ
        wi = self.start_width
        he = self.start_height
        le = self.start_length
        if x == 0 or x == wi or x == wi + le or x == 2 * wi + le:
            first_dir = Direction.LEFT
        if x == wi - 1 or x == wi + le - 1 or (
                x == 2 * wi + le - 1 or x == 2 * wi + 2 * le - 1):
            first_dir = Direction.RIGHT
        if y == 2 * le + he - 1 or y == le + he - 1 or y == le - 1:
            second_dir = Direction.TOP
        if y == 0 or y == le or y == le + he:
            second_dir = Direction.BOTTOM
        if first_dir is None or second_dir is None:
            return
        directions = self.direction_changer(1, 1, 1, 1)
        directions2 = self.direction_changer(1, 1, 1, 1)
        x1 = x
        y1 = y
        x2 = x
        y2 = y
        for i in range(l):
            if directions[first_dir] in self.cells[(x1, y1)].neighbors:
                next_ = self.cells[(x1, y1)].neighbors[directions[first_dir]]
                if (next_[0], next_[1]) in self.cells:
                    circ.append(next_)
                else:
                    circ.clear()
                    break
                directions = self.direction_changer(
                    x1, y1, next_[0], next_[1], directions)
                x1 = next_[0]
                y1 = next_[1]
            if directions2[second_dir] in self.cells[(x2, y2)].neighbors:
                next_ = self.cells[(x2, y2)].neighbors[directions2[second_dir]]
                if (next_[0], next_[1]) in self.cells:
                    circ.append(next_)
                else:
                    circ.clear()
                    break
                directions2 = self.direction_changer(
                    x2, y2, next_[0], next_[1], directions2)
                x2 = next_[0]
                y2 = next_[1]
        if circ:
            circ.append((x, y))
        return circ

    def place_dir_rect(self, x, y, w, l, first_dir, second_dir, third_dir):
        rect = []
        directions = self.direction_changer(1, 1, 1, 1)
        x1 = x
        y1 = y
        p = 0
        for i in range(w):
            for j in range(l - 1):
                dir = first_dir if p % 2 == 0 else second_dir
                if directions[dir] in self.cells[(x1, y1)].neighbors:
                    next = self.cells[(x1, y1)].neighbors[directions[dir]]
                    if (next[0], next[1]) in self.cells:
                        rect.append(next)
                    else:
                        rect.clear()
                        break
                    directions = self.direction_changer(
                        x1, y1, next[0], next[1], directions)
                    x1 = next[0]
                    y1 = next[1]
                else:
                    rect.clear()
                    break
            if not rect:
                break
            else:
                if third_dir in self.cells[(x1, y1)].neighbors:
                    next = self.cells[(x1, y1)].neighbors[
                        directions[third_dir]]
                    if (next[0], next[1]) in self.cells:
                        rect.append(next)
                    else:
                        rect.clear()
                        break
                    directions = self.direction_changer(
                        x1, y1, next[0], next[1], directions)
                    x1 = next[0]
                    y1 = next[1]
                else:
                    rect.clear()
                    break
            p += 1
        if rect:
            rect.pop()
            rect.insert(0, (x, y))
            if len(rect) != w * l:
                rect.clear()
        return list(set(rect))

    def place_rect(self, x, y, w, l):
        top = Direction.TOP
        bottom = Direction.BOTTOM
        left = Direction.LEFT
        right = Direction.RIGHT
        rects = [
            self.place_dir_rect(x, y, w, l, top, bottom, right),
            self.place_dir_rect(x, y, w, l, top, bottom, left),
            self.place_dir_rect(x, y, w, l, right, left, top),
            self.place_dir_rect(x, y, w, l, right, left, bottom),
            self.place_dir_rect(x, y, w, l, bottom, top, right),
            self.place_dir_rect(x, y, w, l, bottom, top, left),
            self.place_dir_rect(x, y, w, l, left, right, top),
            self.place_dir_rect(x, y, w, l, left, right, bottom)]
        true_rects = list(filter(None, rects))
        uni_rects = []
        for rect in true_rects:
            f = False
            for rect1 in uni_rects:
                if set(rect) == set(rect1):
                    f = True
            if not f and len(rect) == w * l:
                uni_rects.append(rect)
        return uni_rects

    def get_free_cells(self):
        res = []
        for coord in self.cells:
            if self.cells[coord].state == CellState.FREE:
                res.append(coord)
        return res

    @staticmethod
    def write_in_file(game, filename):
        with open(filename, "w") as file:
            file.write(str(game.start_height) + " ")
            file.write(str(game.start_width) + " ")
            file.write(str(game.start_length) + " ")
            file.write("\n")
            res = str(game)
            file.write(res)
