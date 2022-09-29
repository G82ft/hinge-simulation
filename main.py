"""Made by Leonid (https://github.com/G4m3_80ft)
"""
from math import cos, sin
from tkinter import (Tk, Canvas, Frame, Label, Entry, Checkbutton, Radiobutton, Button,
                     IntVar, BooleanVar, StringVar)


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

    def __round__(self, n_digits: int = None):
        return Vector(
            [
                round(i, n_digits) for i in self.values
            ]
        )

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

    def __str__(self):
        return f'Hinge({self.position.values}) at {hex(id(self))}'

    def __repr__(self):
        return f'{self}'

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

    def __eq__(self, other):
        return self.hinges == other.hinges

    def update(self) -> None:
        hin1, hin2 = self.hinges
        axis: Vector = hin1.position - hin2.position
        dist: float = axis.length
        if dist != 0:
            n: Vector = axis / dist
            d: float = self.length - dist
            if not hin1.is_fixed:
                # noinspection PyTypeChecker
                self.hinges[0].position = round(self.hinges[0].position + n * d, 1)
            if not hin2.is_fixed:
                # noinspection PyTypeChecker
                self.hinges[1].position = round(self.hinges[1].position - n * d, 1)

    def get_coords(self) -> list:
        return self.hinges[0].position.values + self.hinges[1].position.values


class Simulation:
    def __init__(self):
        self.hinges: dict[int: Hinge] = {}
        self.links_d: dict = {}
        self.links: list = []
        self.links_id: list = []

        # Need to create root before creating tkinter objects
        temp_root = Tk()
        self.canvas: Canvas = Canvas()
        temp_root.destroy()

    def update(self) -> None:
        for L in self.links_d.values():
            L.update()

        for h in self.hinges.values():
            h.update()

        return None

    def draw(self) -> None:
        for id_, link in self.links_d.items():
            self.canvas.coords(id_, link.get_coords())

        for id_, hinge in self.hinges.items():
            self.canvas.moveto(id_, *hinge.screen_position[:2])

        return None

    def add_hinge(self, hin: Hinge) -> None:
        if hin not in self.hinges.values():
            self.hinges[
                self.canvas.create_oval(*hin.screen_position, outline='black')
            ] = hin

    def remove_hinge(self, hin_id: int):
        if hin_id in self.hinges:
            hinge = self.hinges[hin_id]

            del self.hinges[hin_id]
            self.canvas.delete(hin_id)

            for id_, link in self.links_d.copy().items():
                if hinge in link.hinges:
                    del self.links_d[id_]
                    self.canvas.delete(id_)

    def add_link(self, link: Link) -> None:
        if link not in self.links_d.values():
            for hin in link.hinges:
                self.add_hinge(hin)

            self.links_d[
                self.canvas.create_line(link.get_coords(), width=1)
            ] = link


class Root:
    def __init__(self, sim: Simulation, fps: float):
        self.sim: Simulation = sim
        self.fps: float = fps

        self.root: Tk = Tk()
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.x, self.y = 350, 360
        self.root.geometry(f'{self.x}x{self.y}')
        self.root.resizable(False, False)
        self.root.title('Hinge simulation')

        sim.canvas = Canvas(self.root)
        sim.canvas.grid(row=1, column=0, sticky='nesw')

        # GUI
        # Toolbar
        toolbar: Frame = Frame(
            self.root,
            bd=1,
            relief='ridge'
        )
        toolbar.grid(row=0, column=0,
                     columnspan=2,
                     sticky='ew')
        self.tool_id: IntVar = IntVar()

        Radiobutton(
            toolbar,
            text='Select',
            indicatoron=False,
            variable=self.tool_id,
            value=0
        ).grid(row=0, column=0)
        Radiobutton(
            toolbar,
            text='Hinge',
            indicatoron=False,
            variable=self.tool_id,
            value=1
        ).grid(row=0, column=1)
        Radiobutton(
            toolbar,
            text='Link',
            indicatoron=False,
            variable=self.tool_id,
            value=2
        ).grid(row=0, column=2)

        # Bottom check buttons
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

        # Right menu setup
        self.prev_info: list = [0, '#fff']
        self.right_menu: Frame = Frame(
            self.root,
            bd=5,
            relief='ridge'
        )

        right_menu_list: list = []
        self.info: dict = {}

        left = Label(
            self.right_menu,
            text='ID'
        )
        self.info["id"] = StringVar()
        self.info["id"].set(0)
        r = Label(
            self.right_menu,
            textvariable=self.info["id"]
        )
        right_menu_list.append((left, r))

        left = Label(
            self.right_menu,
            text='X'
        )
        self.info["x"] = StringVar()
        r = Entry(
            self.right_menu,
            width=5,
            textvariable=self.info["x"]
        )
        right_menu_list.append((left, r))

        left = Label(
            self.right_menu,
            text='Y'
        )
        self.info["y"] = StringVar()
        r = Entry(
            self.right_menu,
            width=5,
            textvariable=self.info["y"]
        )
        right_menu_list.append((left, r))

        left = Label(
            self.right_menu,
            text='Fixed'
        )
        self.info["fixed"] = BooleanVar()
        r = Checkbutton(
            self.right_menu,
            variable=self.info["fixed"]
        )
        right_menu_list.append((left, r))

        left = Label(
            self.right_menu,
            text='X axis'
        )
        self.info["x_axis"] = StringVar()
        r = Entry(
            self.right_menu,
            width=5,
            textvariable=self.info["x_axis"]
        )
        right_menu_list.append((left, r))

        left = Label(
            self.right_menu,
            text='Y axis'
        )
        self.info["y_axis"] = StringVar()
        r = Entry(
            self.right_menu,
            width=5,
            textvariable=self.info["y_axis"]
        )
        right_menu_list.append((left, r))

        for i, (r, left) in enumerate(right_menu_list):
            r.grid(row=i, column=0)
            left.grid(row=i, column=1)
            self.right_menu.rowconfigure(i, weight=1)

        Button(
            self.right_menu,
            text='Apply',
            command=self.configure
        ).grid(columnspan=2)
        # Adjusting menu width
        Label(
            self.right_menu,
            width=12,
            height=0
        ).grid(columnspan=2,
               sticky='s')

        self.right_menu.grid(row=1, column=1,
                             rowspan=3,
                             sticky='ns')
        self.root.update()
        self.menu_width: int = self.right_menu.winfo_width()
        self.right_menu.grid_forget()

        # Bindings
        self.root.bind_all('<space>', lambda e: self.is_running.set(not self.is_running.get()))
        self.root.bind_all('<Control-space>', lambda e: self.trace_enabled.set(not self.trace_enabled.get()))
        self.root.bind_all('<KeyRelease-Delete>', self.delete, add='+')
        self.root.bind_all('<KeyRelease-BackSpace>', self.delete)

        sim.canvas.bind('<ButtonRelease-1>', self.handle_click)
        sim.canvas.bind('<Control-Motion>', self.move)

        bind_tree(self.right_menu, '<Any-Button>', lambda e: self.is_running.set(False))
        bind_tree(self.right_menu, '<Any-Key>', lambda e: self.is_running.set(False))

    def summon_menu(self) -> None:
        self.right_menu.grid(row=1, column=1,
                             rowspan=3,
                             sticky='ns')
        self.root.geometry(f'{self.x + self.menu_width}x{self.y}')

        return None

    def hide_menu(self) -> None:
        self.root.geometry(f'{self.x}x{self.y}')
        self.right_menu.grid_forget()

    def handle_click(self, event) -> None:
        match self.tool_id.get():
            case 0:
                self.select(event)
            case 1:
                self.create_hinge(event)
            case 2:
                self.link_hinges(event)
            case _:
                return None

    def find_hinge(self, event) -> int:
        hin_id: int = 0
        for hin_id in self.sim.canvas.find_enclosed(event.x - 25, event.y - 25, event.x + 25, event.y + 25)[::-1]:
            if hin_id in self.sim.hinges:
                break

        return hin_id

    def select(self, event) -> None:
        if self.prev_info[0] in self.sim.hinges:
            self.sim.canvas.itemconfig(
                self.prev_info[0],
                outline=self.prev_info[1]
            )
            self.hide_menu()

        hin_id: int = self.find_hinge(event)
        if hin_id == 0:
            self.info["id"].set('0')
            return None

        self.info["id"].set(hin_id)
        self.update_pos()
        self.update_info()
        self.summon_menu()

        self.prev_info = [hin_id, self.sim.canvas.itemcget(hin_id, 'outline')]

        self.sim.canvas.itemconfig(hin_id, outline='#0ff')

    def create_hinge(self, event) -> None:
        hinge: Hinge = Hinge(Vector([event.x, event.y]))
        self.sim.add_hinge(hinge)
        self.sim.draw()
        self.select(event)

        return None

    def link_hinges(self, event) -> None:
        if self.prev_info[0] not in self.sim.hinges:
            return None

        hin_id: int = self.find_hinge(event)
        if hin_id == 0:
            return None

        hin1: Hinge = self.sim.hinges[self.prev_info[0]]
        hin2: Hinge = self.sim.hinges[hin_id]

        self.sim.add_link(
            Link(
                abs((hin1.position - hin2.position).length),
                (hin1, hin2)
            )
        )

    def update_pos(self) -> None:
        hin_id: int = int(self.info["id"].get())
        if hin_id in self.sim.hinges:
            x, y = [
                round(i) for i in self.sim.hinges[hin_id].position.values
            ]
            self.info["x"].set(x)
            self.info["y"].set(y)

    def update_info(self) -> None:
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

    def delete(self, event) -> None:
        if isinstance(event.widget, Entry):
            return None

        hin_id: int = int(self.info["id"].get())
        if hin_id in self.sim.hinges:
            self.sim.remove_hinge(hin_id)
        self.hide_menu()

    def configure(self, *_) -> None:
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

    def mainloop(self) -> None:
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


if __name__ == '__main__':
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
