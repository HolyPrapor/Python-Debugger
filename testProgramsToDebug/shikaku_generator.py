import shikaku
import random
import copy
import math
import argparse


def make_shikaku(height, wight, length, count):
    count += 1
    mid_count = (
        height * wight + height * length + wight * length) * 2 / count
    mid_st = round(math.sqrt(mid_count))
    numbers = [i for i in range(mid_st - 5, mid_st + 5)]
    if count == 1:
        numbers = [i for i in range(1, 31)]
    numbers.append(wight)
    numbers.append(height)
    numbers.append(length)
    numbers.append(length + height)
    numbers.append(length + wight)
    numbers.append(height + wight)
    numbers.append(height + wight + length)
    y_count = 0
    game = shikaku.Field(height, length, wight)
    for (x, y) in game.cells:
        game.find_neighbors(x, y)
    while y_count != count:
        game = shikaku.Field(height, length, wight)
        for i in game.cells:
            game.find_neighbors(i[0], i[1])
        game, y_count = field_coat(game, numbers, count)
        if count == 1:
            break
    solution = copy.deepcopy(game)
    for y in range(game.height):
        for x in range(game.width):
            if (x, y) in game.cells:
                game.cells[(x, y)].state = shikaku.CellState.FREE
                if isinstance(game.cells[(x, y)].num, str):
                    game.cells[(x, y)].num = 0
                else:
                    game.cells[(x, y)].state = shikaku.CellState.BUSY
                if game.cells[(x, y)].num == 1:
                    game.cells[(x, y)].state = shikaku.CellState.BUSY
    return solution, game


def field_coat(game, numbers, counter):
    y_count = 0
    c = 0
    count = 0
    while not game.is_full():
        a = random.choice(numbers)
        b = random.choice(numbers)
        coords = game.get_free_cells()
        for cor in coords:
            x = cor[0]
            y = cor[1]
            neib = game.cells[cor].neighbors
            is_alone = True
            for n in neib.values():
                if n in game.cells and\
                        game.cells[n].state == shikaku.CellState.FREE:
                    is_alone = False
            if is_alone:
                game.cells[(x, y)].set_num(1)
                y_count += 1
        fif = random.randint(0, 1)
        if fif == 0:
            for cor in coords:
                x = cor[0]
                y = cor[1]
                sp = game.place_rect(x, y, a, b)
                rect = []
                if sp:
                    rect = random.choice(sp)
                is_busy = False
                for coord in rect:
                    if game.cells[coord].state != shikaku.CellState.FREE:
                        is_busy = True
                if is_busy:
                    continue
                for coord in rect:
                    game.cells[coord].set_num(str(a * b))
                    game.cells[(x, y)].num = a * b
                if rect:
                    y_count += 1
        else:
            for cor in coords:
                x = cor[0]
                y = cor[1]
                circ = game.place_circ(x, y, a)
                is_alone = False
                if circ:
                    for cord in circ:
                        if game.cells[cord].state == shikaku.CellState.BUSY:
                            is_alone = True
                if is_alone:
                    continue
                if circ and c < 3 and a <= game.start_length:
                    for coord in circ:
                        game.cells[coord].set_num(str(a) + '!')
                        game.cells[(x, y)].num = a
                    c += 1
                    y_count += 1
                    continue
        count += 1
        if count > counter * 300:
            return game, 0
    return game, y_count


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('h', type=int, help="высота")
    parser.add_argument('w', type=int, help='ширина')
    parser.add_argument('l', type=int, help='длина')
    parser.add_argument(
        'count',
        type=int,
        help='количество разрезов(если 0, то выбирается случайно)')
    parser.add_argument('gf', type=str, help='файл для записи условия')
    parser.add_argument('sf', type=str, help='файл для записи решения')
    return parser.parse_args()


def main():
    #args = parse_args()
    h, w, l, count, sf, gf = 2, 2, 2, 1, '/dev/stdout', '/dev/stderr'
    solution, game = make_shikaku(h, w, l, count)
    shikaku.Field.write_in_file(solution, sf)
    shikaku.Field.write_in_file(game, gf)

if __name__ == '__main__':
    main()
