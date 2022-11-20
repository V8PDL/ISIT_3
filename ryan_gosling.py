from PIL import Image, ImageDraw
from random import random, choice 
from typing import TypeVar, List
from os import makedirs, path, system, listdir, sep
from json import load
from imageio.v2 import get_writer, imread
from time import time

Cell = TypeVar('Cell')
Matrix = TypeVar('Matrix')

class Matrix:

    happy_cells:List[Cell] = list()
    unhappy_cells:List[Cell] = list()
    empty_cells:List[Cell] = list()
    all_cells:List[Cell] = list()
    white_rate:float
    black_rate:float
    colors_dict:dict = dict()
    size:int
    plot_size:float
    iterations_count:int
    snapshots_frequency:int
    step:float
    happiness_cup:int
    cells_path:str
    temp_folder:str
    gif_path:str
    write_text_logs:bool
    write_diffs:bool
    seconds_for_frame:float

    def __init__(self, config):
        if config is not None:
            self.white_rate = config['white_rate']
            self.black_rate = config['black_rate']
            [self.colors_dict.update({k: tuple(v)}) for k, v in config['colors_dict'].items()]
            self.size = config['array_size']
            self.plot_size = config['plot_size']
            self.happiness_cup = config['happiness_cup']
            self.iterations_count = config['iterations_count']
            self.snapshots_frequency = config['snapshots_frequency']
            self.gif_path = config['gif_path']
            self.temp_folder = config['temp_folder']
            self.cells_path = config['cells_path']
            self.write_text_logs = config['write_text_logs']
            self.write_diffs = config['write_diffs']
            self.seconds_for_frame = config['seconds_for_frame']
            self.step = self.plot_size / self.size

        [self.all_cells.append(self.Cell(self, position)) for position in range(0, self.size * self.size)]
        self.unhappy_cells = [cell for cell in self.all_cells if not cell.is_happy]
        self.happy_cells = [cell for cell in self.all_cells if cell.is_happy]
        self.empty_cells = [cell for cell in self.all_cells if cell.color == "empty"]

    class Cell:

        matrix:Matrix
        color:str
        position:int
        position_x:int
        position_y:int

        def __init__(self, matrix: Matrix, position: int, value:str = None):
            self.matrix = matrix
            if value is None:
                color = random()
            else:
                color = value

            if color < matrix.white_rate:
                self.color = "white"
            elif color < matrix.white_rate + matrix.black_rate:
                self.color = "black"
            else:
                self.color = "empty"

            self.position = position
            self.position_x = int(position / matrix.size)
            self.position_y = position % matrix.size

            if self.color != "empty":
                self.is_happy = False
                matrix.unhappy_cells.append(self)
            else:
                self.is_happy = True
                matrix.happy_cells.append(self)

        def state_happiness(self) -> bool:
            if self.color == "empty":
                return True
            new_is_happy = sum([self.color == neighbour.color for neighbour in self.get_neighbours()]) >= self.matrix.happiness_cup
            if new_is_happy != self.is_happy and self.is_happy:
                self.matrix.happy_cells.remove(self)
                self.matrix.unhappy_cells.append(self)
            elif new_is_happy != self.is_happy:
                self.matrix.happy_cells.append(self)
                self.matrix.unhappy_cells.remove(self)
            self.is_happy = new_is_happy
            return self.is_happy

        def get_neighbours(self) -> List[Cell]:
            return [self.matrix.get_cell_by_xy(self.position_x + 1, self.position_y + 1),
                    self.matrix.get_cell_by_xy(self.position_x + 1, self.position_y),
                    self.matrix.get_cell_by_xy(self.position_x + 1, self.position_y - 1),
                    self.matrix.get_cell_by_xy(self.position_x, self.position_y + 1),
                    self.matrix.get_cell_by_xy(self.position_x, self.position_y - 1),
                    self.matrix.get_cell_by_xy(self.position_x - 1, self.position_y + 1),
                    self.matrix.get_cell_by_xy(self.position_x - 1, self.position_y),
                    self.matrix.get_cell_by_xy(self.position_x - 1, self.position_y - 1)]

        def exchange_places(self):
            if len(self.matrix.empty_cells) < 1:
                return
            empty_cell = choice(self.matrix.empty_cells)
            if self.matrix.write_diffs:
                with open(f"{self.matrix.temp_folder}{sep}{self.matrix.cells_path}", "a") as cells_file:
                    cells_file.write(f"Cell {self.to_string()} moved to {empty_cell.to_string()}. Neighbours:\n")
                    [cells_file.write(f"\t{cell.to_string()}\n") for cell in self.get_neighbours()]
            (self.color, self.is_happy, empty_cell.color) = (empty_cell.color, True, self.color)
            self.matrix.empty_cells.remove(empty_cell)
            self.matrix.empty_cells.append(self)
            self.matrix.happy_cells.append(self)
            self.matrix.unhappy_cells.remove(self)
            [neighbour.state_happiness() for neighbour in self.get_neighbours()]
            empty_cell.state_happiness()
            [neighbour.state_happiness() for neighbour in empty_cell.get_neighbours()]

        def to_string(self) -> str:
            return f"[{self.position}]{self.position_x}:{self.position_y} = {self.color} ({self.is_happy})"

    def get_cell_by_xy(self, x: int, y: int) -> Cell:
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return self.Cell(matrix, 0, 1)
        return self.all_cells[x * self.size + y]

    def get_image(self) -> Image:
        image = Image.new("RGBA", (self.plot_size, self.plot_size), self.colors_dict["empty"])
        draw = ImageDraw.Draw(image)
        [draw.rectangle(
            [cell.position_x * self.step, cell.position_y * self.step, (cell.position_x + 1) * self.step, (cell.position_y + 1) * self.step],
            fill=self.colors_dict[cell.color])
        for cell in self.all_cells]
        return image

    def save_image(self, iteration:int = 0):
        self.get_image().save(f"{self.temp_folder}{sep}{iteration}.png", "png", save_all=True)

    def iterate(self, iteration: int = 0) -> bool:
        if len(self.unhappy_cells) == 0:
            print("Everyone is happy")
            self.save_image(iteration)
            return False
        choice(self.unhappy_cells).exchange_places()
        if iteration % self.snapshots_frequency == 0:
            if iteration % int(self.iterations_count / 100) == 0:
                print(f"{int(iteration / self.iterations_count * 100)}% is done")
            self.save_image(iteration)
            if self.write_text_logs:
                cells_to_text = str.join(";", [cell.to_string() for cell in self.all_cells])
                with open(f"{self.temp_folder}{sep}{self.cells_path}", "a") as cells_file:
                    cells_file.write(f"\nMatrix on iteration {iteration}:\n{cells_to_text}\n")
        return True

    def make_gif(self):
        images = sorted([image_path for image_path in listdir(self.temp_folder) if image_path.endswith(".png")], key=lambda i: int(i[:-4]))
        with get_writer(self.gif_path, mode="I", duration=self.seconds_for_frame) as writer:
            [writer.append_data(imread(f"{self.temp_folder}{sep}{image}")) for image in images]

    def to_string(self) -> str:
        return str.join(";", [cell.to_string() for cell in self.all_cells])

if __name__ == "__main__":

    with open("config.json") as config_file:
        config = load(config_file)
        generate_images = config['generate_images']
        generate_gif = config['generate_gif']

    if generate_images:
        print("Start generating images")
        images_start_time = time()
        matrix = Matrix(config)
        [cell.state_happiness() for cell in matrix.all_cells]
        if path.exists(matrix.temp_folder):
            system(f"rd /s /q \"{matrix.temp_folder}\"")
        makedirs(matrix.temp_folder)
        if matrix.write_text_logs:
            with open(f"{matrix.temp_folder}{sep}{matrix.cells_path}", "a") as cells_file:
                cells_file.write(f"Starting matrix:\n{matrix.to_string()}\n")
        for iteration in range(0, matrix.iterations_count):
            if not matrix.iterate(iteration):
                break
        images_end_time = time()
        print(f"Images generated. It took {images_end_time - images_start_time:1.9f}")

    if generate_gif:
        print('Start converting images to gif')
        gif_start_time = time()
        matrix.make_gif()
        gif_end_time = time()
        print(f"Gif created. It took {gif_end_time - gif_start_time:1.9f}")

    print("Job is done.")