from math import cos, sin
from tkinter import Tk, Canvas, Frame, Label, Entry, Checkbutton, Button, BooleanVar, StringVar


def bind_tree(widget, event_seq: str, callback):
    widget.bind(event_seq, callback)

    for child in widget.children.values():
        bind_tree(child, event_seq, callback)


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
        if dist != 0:
            n: Vector = axis / dist
            d: float = self.length - dist
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

        # Need to create root before creating tkinter objects
        temp_root = Tk()
        self.canvas: Canvas = Canvas()
        temp_root.destroy()

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
        self.x, self.y = 350, 360
        self.root.geometry(f'{self.x}x{self.y}')
        self.root.resizable(False, False)
        self.root.title('Hinge simulation')

        sim.canvas = Canvas(self.root)
        sim.canvas.grid(sticky='nesw')

        sim.canvas.bind('<Control-Motion>', self.move)

        self.is_running: BooleanVar = BooleanVar()
        self.is_running.set(True)
        acb = Checkbutton(
            self.root,
            bd=5,
            indicatoron=False,
            text='Animation',
            variable=self.is_running
        )
        acb["command"] = lambda cb=acb: acb.focus_set()
        acb.grid(sticky='ew')

        self.trace_enabled: BooleanVar = BooleanVar()
        Checkbutton(
            self.root,
            bd=5,
            indicatoron=False,
            text='Trace',
            variable=self.trace_enabled
        ).grid(sticky='ew')

        # Selection stuff
        self.prev_id: int = 0
        self.prev_color: str = '#fff'
        sim.canvas.bind('<1>', self.update_id)

        self.menu: Frame = Frame(
            self.root,
            bd=5,
            relief='ridge'
        )

        menu_list: list = []
        self.info: dict = {}

        left = Label(
            self.menu,
            text='ID'
        )
        self.info["id"] = StringVar()
        self.info["id"].set(0)
        r = Label(
            self.menu,
            textvariable=self.info["id"]
        )
        menu_list.append((left, r))

        left = Label(
            self.menu,
            text='X'
        )
        self.info["x"] = StringVar()
        r = Entry(
            self.menu,
            width=5,
            textvariable=self.info["x"]
        )
        menu_list.append((left, r))

        left = Label(
            self.menu,
            text='Y'
        )
        self.info["y"] = StringVar()
        r = Entry(
            self.menu,
            width=5,
            textvariable=self.info["y"]
        )
        menu_list.append((left, r))

        left = Label(
            self.menu,
            text='Fixed'
        )
        self.info["fixed"] = BooleanVar()
        r = Checkbutton(
            self.menu,
            variable=self.info["fixed"]
        )
        menu_list.append((left, r))

        left = Label(
            self.menu,
            text='X axis'
        )
        self.info["x_axis"] = StringVar()
        r = Entry(
            self.menu,
            width=5,
            textvariable=self.info["x_axis"]
        )
        menu_list.append((left, r))

        left = Label(
            self.menu,
            text='Y axis'
        )
        self.info["y_axis"] = StringVar()
        r = Entry(
            self.menu,
            width=5,
            textvariable=self.info["y_axis"]
        )
        menu_list.append((left, r))

        for i, (r, left) in enumerate(menu_list):
            r.grid(row=i, column=0)
            left.grid(row=i, column=1)
            self.menu.rowconfigure(i, weight=1)

        Button(
            self.menu,
            text='Apply',
            command=self.configure
        ).grid(columnspan=2)
        # Adjusting menu width
        Label(
            self.menu,
            width=12,
            height=0
        ).grid(columnspan=2,
               sticky='s')

        self.menu.grid(row=0, column=1,
                       rowspan=3,
                       sticky='ns')
        self.root.update()
        self.menu_width: int = self.menu.winfo_width()
        self.menu.grid_forget()

        bind_tree(self.menu, '<Any-Button>', lambda e: self.is_running.set(False))
        bind_tree(self.menu, '<Any-Key>', lambda e: self.is_running.set(False))

    def summon_menu(self):
        self.menu.grid(row=0, column=1,
                       rowspan=3,
                       sticky='ns')
        self.root.geometry(f'{self.x + self.menu_width}x{self.y}')

    def hide_menu(self):
        self.root.geometry(f'{self.x}x{self.y}')
        self.menu.grid_forget()

    def update_id(self, event):
        if self.prev_id in self.sim.hinges:
            self.sim.canvas.itemconfig(
                self.prev_id,
                outline=self.prev_color
            )
            self.hide_menu()

        try:
            id_: int = self.sim.canvas.find_enclosed(event.x - 25, event.y - 25, event.x + 25, event.y + 25)[0]
        except IndexError:
            self.info["id"].set('0')
            self.update_pos()
            return None

        if id_ in self.sim.hinges:
            self.info["id"].set(id_)
            self.update_pos()
            self.update_info()
            self.summon_menu()

            self.prev_id = id_
            self.prev_color = self.sim.canvas.itemcget(id_, 'outline')

            self.sim.canvas.itemconfig(id_, outline='#0ff')
        else:
            self.info["id"].set('0')
            self.update_pos()

    def update_pos(self):
        hin_id: int = int(self.info["id"].get())
        if hin_id in self.sim.hinges:
            x, y = [
                round(i) for i in self.sim.hinges[hin_id].position.values
            ]
            self.info["x"].set(x)
            self.info["y"].set(y)

    def update_info(self):
        hin_id: int = int(self.info["id"].get())
        if hin_id in self.sim.hinges:
            h: Hinge = self.sim.hinges[hin_id]
            self.info["id"].set(hin_id)
            self.info["fixed"].set(h.is_fixed)
            self.info["x_axis"].set(f'{h.x_axis}')
            self.info["y_axis"].set(f'{h.y_axis}')

    def move(self, event) -> None:
        hin_id: int = int(self.info["id"].get())
        if hin_id in self.sim.hinges and not self.sim.hinges[hin_id].is_fixed:
            self.sim.hinges[hin_id].position = Vector(
                [event.x, event.y]
            )
            self.sim.update()
            self.update_pos()

    def configure(self, *_):
        self.is_running.set(False)

        hinge: Hinge = self.sim.hinges[int(self.info["id"].get())]
        hinge_info: dict = {
            "x": round(hinge.position[0]),
            "y": round(hinge.position[1]),
            "x_axis": hinge.x_axis,
            "y_axis": hinge.y_axis
        }

        info: dict = self.info.copy()
        del info["fixed"]

        for k, v in info.items():
            content: str = v.get()

            if 'n' in content and k in ("x_axis", "y_axis"):
                self.info[k].set("None")
                hinge_info[k] = None
            elif content.isdigit():
                hinge_info[k] = int(content)
            else:
                self.info[k].set(hinge_info[k])

        hinge.position = Vector(
            [
                hinge_info["x"],
                hinge_info["y"]
            ]
        )
        hinge.is_fixed = self.info["fixed"].get()
        hinge.x_axis = hinge_info["x_axis"]
        hinge.y_axis = hinge_info["y_axis"]

    def mainloop(self):
        i = 0

        ids = []
        id1 = tuple(self.sim.hinges)[2]
        id2 = tuple(self.sim.hinges)[5]
        self.sim.canvas.itemconfig(id1, outline='red')
        self.sim.canvas.itemconfig(id2, outline='red')

        while True:
            self.root.update()
            self.root.update_idletasks()

            if self.is_running.get():
                self.update_pos()
                self.sim.hinges[id1].position[0] = 160 + 55 * sin(i)
                self.sim.hinges[id1].position[1] = 100 + 10 * sin(2 * i)

                self.sim.hinges[id2].position[0] = 60 + 50 * cos(i + 5)
                self.sim.hinges[id2].position[1] = 210 + 50 * sin(i + 5)

                i += 0.001

                if self.trace_enabled.get():
                    if round(i * 1000) % 300 == 0:
                        for h in self.sim.hinges.values():
                            if not h.is_fixed:
                                ids.append(
                                    self.sim.canvas.create_rectangle(
                                        h.position.values * 2
                                    )
                                )

                    if len(ids) > 25:
                        self.sim.canvas.delete(ids.pop(0))
                elif ids:
                    for id_ in ids:
                        self.sim.canvas.delete(id_)
                    ids.clear()

            self.sim.update()
            self.sim.draw()


so = Simulation()
root = Root(so, 60)

hin_1 = Hinge(
    Vector([60, 100]),
    is_fixed=True
)
hin_2 = Hinge(
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
        (hin_1, hin_2)
    ),
    Link(
        100,
        (hin_2, hin3)
    ),
    Link(
        100,
        (hin3, hin4)
    )
]

hin_1 = Hinge(
    Vector([60, 210]),
    is_fixed=True
)
hin_2 = Hinge(
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
            (hin_1, hin_2)
        ),
        Link(
            100,
            (hin_2, hin3)
        )
    ]
)

for link_ in links:
    so.add_link(link_)

root.mainloop()
