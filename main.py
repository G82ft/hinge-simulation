from math import cos, sin
from tkinter import Tk, Canvas, Checkbutton, BooleanVar


class Vector:
    def __init__(self, values: list):
        self._values: list = list(values)

    def __str__(self):
        return 'Vector({}, {})'.format(*self.values)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        return self.values.__getitem__(index)

    def __setitem__(self, index, value):
        return self._values.__setitem__(index, value)

    def __iter__(self):
        return self._values.__iter__()

    def __mul__(self, other):
        result = self.copy()

        if not isinstance(other, (int, float)):
            raise TypeError

        for i in range(2):
            result[i] *= other

        return result

    def __truediv__(self, other):
        result = self.copy()

        if not isinstance(other, (int, float)):
            raise TypeError

        for i in range(2):
            result[i] /= other

        return result

    def __pow__(self, power):
        result = self.copy()

        if not isinstance(power, (int, float)):
            raise TypeError

        for i in range(2):
            result[i] **= power

        return result

    def __add__(self, other):
        result = self.copy()

        if not isinstance(other, Vector):
            raise TypeError

        for i in range(2):
            result[i] += other.values[i]

        return result

    def __sub__(self, other):
        result = self.copy()

        if not isinstance(other, Vector):
            raise TypeError

        for i in range(2):
            result[i] -= other.values[i]

        return result

    def __eq__(self, other):
        if not isinstance(other, Vector):
            raise TypeError

        return self.values == other.values

    def copy(self):
        return Vector(self.values.copy())

    @property
    def values(self):
        return self._values.copy()

    @property
    def length(self):
        f, s = self.values
        return (f ** 2 + s ** 2) ** 0.5


class Hinge:
    def __init__(self,
                 position: Vector,
                 x_axis: float | None = None, y_axis: float | None = None,
                 is_fixed: bool = False):
        self.position: Vector = position
        self.is_fixed: bool = is_fixed

        self.x_axis: float = x_axis
        self.y_axis: float = y_axis

        if self.x_axis is not None and self.y_axis is not None:
            self.is_fixed: bool = True
            self.position = Vector([self.x_axis, self.y_axis])

    def update(self) -> None:
        if self.is_fixed:
            return None

        if self.x_axis is not None:
            self.position[0] = self.x_axis
        if self.y_axis is not None:
            self.position[1] = self.y_axis

    @property
    def center(self) -> list:
        return (self.position - Vector([5, 5])).values

    @property
    def screen_position(self) -> list:
        size: Vector = Vector(
            [5, 5]
        )
        rt: Vector = self.position - size
        lb: Vector = self.position + size
        return rt.values + lb.values


class Link:
    def __init__(self, length: float, hinges: tuple[Hinge, Hinge]):
        self.length: float = length
        self.hinges: tuple[Hinge, Hinge] = hinges

    def update(self) -> None:
        hin1, hin2 = self.hinges
        axis: Vector = hin1.position - hin2.position
        dist: float = axis.length
        n: Vector = axis / dist
        d: float = (self.length - dist) / 2
        if not hin1.is_fixed:
            self.hinges[0].position += n * d
        if not hin2.is_fixed:
            self.hinges[1].position -= n * d

    def get_coords(self) -> list:
        return self.hinges[0].position.values + self.hinges[1].position.values


class Simulation:
    def __init__(self):
        self.hinges: dict[int: Hinge] = {}
        self.links: list = []
        self.links_id: list = []

        self.canvas: Canvas = None

    def update(self) -> None:
        for L in self.links:
            L.update()

        for h in self.hinges.values():
            h.update()

        return None

    def draw(self) -> None:
        for l_id in self.links_id:
            self.canvas.delete(l_id)

        self.links_id.clear()

        for L in self.links:
            self.links_id.append(self.canvas.create_line(*L.get_coords(), width=1))
            self.canvas.tag_lower(self.links_id[-1], tuple(self.hinges)[0])

        for id_, hinge in self.hinges.items():
            self.canvas.moveto(id_, *hinge.screen_position[:2])
            self.canvas.tag_raise(id_, self.links_id[-1])

        return None

    def add_hinge(self, hin: Hinge) -> None:
        if hin not in self.hinges.values():
            self.hinges[
                self.canvas.create_oval(*hin.screen_position, outline='black')
            ] = hin

    def add_link(self, link: Link) -> None:
        if link not in self.links:
            for hin in link.hinges:
                self.add_hinge(hin)

            self.links.append(link)


class Root:
    def __init__(self, sim: Simulation, fps: float):
        self.sim: Simulation = sim
        self.fps: float = fps

        self.root: Tk = Tk()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.geometry('350x360')
        self.root.resizable(False, False)
        self.root.title('Hinge simulation')

        sim.canvas = Canvas(self.root)
        sim.canvas.grid(sticky='nesw')

        sim.canvas.bind('<Control-Motion>', self.move)

        self.text_id = sim.canvas.create_text(10, 10, text='0')
        sim.canvas.bind('<Motion>', self.update_id)

        self.is_running: BooleanVar = BooleanVar()
        self.is_running.set(True)
        Checkbutton(
            self.root,
            bd=5,
            indicatoron=False,
            text='Animation',
            variable=self.is_running
        ).grid(sticky='ew')

        self.trace_enabled: BooleanVar = BooleanVar()
        Checkbutton(
            self.root,
            bd=5,
            indicatoron=False,
            text='Trace',
            variable=self.trace_enabled
        ).grid(sticky='ew')

    def move(self, event) -> None:
        hin_id: int = int(self.sim.canvas.itemcget(self.text_id, 'text'))
        if hin_id in self.sim.hinges and not self.sim.hinges[hin_id].is_fixed:
            self.sim.hinges[hin_id].position = Vector(
                [event.x, event.y]
            )

    def update_id(self, event):
        id_: int = self.sim.canvas.find_closest(event.x, event.y)[0]
        if id_ in self.sim.hinges.keys():
            self.sim.canvas.itemconfig(self.text_id, text=id_)

    def mainloop(self):
        i = 0

        ids = []

        self.sim.canvas.itemconfig(4, outline='red')
        self.sim.canvas.itemconfig(7, outline='red')

        while True:
            self.root.update()
            self.root.update_idletasks()

            if self.is_running.get():
                self.sim.hinges[4].position[0] = 160 + 55 * sin(0.001 * i)
                self.sim.hinges[4].position[1] = 100 + 10 * sin(0.002 * i)

                self.sim.hinges[7].position[0] = 60 + 50 * cos(0.001 * i + 5)
                self.sim.hinges[7].position[1] = 210 + 50 * sin(0.001 * i + 5)

                i += 1

                if self.trace_enabled.get():
                    if i % 300 == 0:
                        for h in self.sim.hinges.values():
                            ids.append(
                                self.sim.canvas.create_oval(
                                    h.position.values * 2
                                )
                            )
                if len(ids) > 25 or (not self.trace_enabled.get() and ids):
                    self.sim.canvas.delete(ids.pop(0))

            self.sim.draw()
            self.sim.update()


sim = Simulation()
root = Root(sim, 60)

hin1 = Hinge(
    Vector([60, 100]),
    is_fixed=True
)
hin2 = Hinge(
    Vector([60, 50])
)
hin3 = Hinge(
    Vector([160, 50])
)
hin4 = Hinge(
    Vector([210, 100]),
    y_axis=100
)

links = [
    Link(
        50,
        (hin1, hin2)
    ),
    Link(
        100,
        (hin2, hin3)
    ),
    Link(
        100,
        (hin3, hin4)
    )
]

hin1 = Hinge(
    Vector([60, 210]),
    is_fixed=True
)
hin2 = Hinge(
    Vector([60, 160])
)
hin3 = Hinge(
    Vector([210, 210]),
    y_axis=210
)

links.extend(
    [
        Link(
            50,
            (hin1, hin2)
        ),
        Link(
            100,
            (hin2, hin3)
        )
    ]
)

for link in links:
    sim.add_link(link)

root.mainloop()
