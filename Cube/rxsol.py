
import time
import random
import json
import os
from functools import reduce
from enum import IntEnum

# ----------------------------------------------------------------------
# pieces.py
# ----------------------------------------------------------------------
class Color(IntEnum):
    U = 0
    R = 1
    F = 2
    D = 3
    L = 4
    B = 5

class Corner(IntEnum):
    URF = 0
    UFL = 1
    ULB = 2
    UBR = 3
    DFR = 4
    DLF = 5
    DBL = 6
    DRB = 7

class Edge(IntEnum):
    UR = 0
    UF = 1
    UL = 2
    UB = 3
    DR = 4
    DF = 5
    DL = 6
    DB = 7
    FR = 8
    FL = 9
    BL = 10
    BR = 11

class Facelet(IntEnum):
    U1 = 0; U2 = 1; U3 = 2; U4 = 3; U5 = 4; U6 = 5; U7 = 6; U8 = 7; U9 = 8
    R1 = 9; R2 = 10; R3 = 11; R4 = 12; R5 = 13; R6 = 14; R7 = 15; R8 = 16; R9 = 17
    F1 = 18; F2 = 19; F3 = 20; F4 = 21; F5 = 22; F6 = 23; F7 = 24; F8 = 25; F9 = 26
    D1 = 27; D2 = 28; D3 = 29; D4 = 30; D5 = 31; D6 = 32; D7 = 33; D8 = 34; D9 = 35
    L1 = 36; L2 = 37; L3 = 38; L4 = 39; L5 = 40; L6 = 41; L7 = 42; L8 = 43; L9 = 44
    B1 = 45; B2 = 46; B3 = 47; B4 = 48; B5 = 49; B6 = 50; B7 = 51; B8 = 52; B9 = 53

# ----------------------------------------------------------------------
# cubes/cubiecube.py
# ----------------------------------------------------------------------
def choose(n, k):
    """Binomial coefficient."""
    if 0 <= k <= n:
        num = 1
        den = 1
        for i in range(1, min(k, n - k) + 1):
            num *= n
            den *= i
            n -= 1
        return num // den
    else:
        return 0

# Corner and edge move data for the six basic moves (U,R,F,D,L,B)
_cpU = (Corner.UBR, Corner.URF, Corner.UFL, Corner.ULB,
        Corner.DFR, Corner.DLF, Corner.DBL, Corner.DRB)
_coU = (0,0,0,0,0,0,0,0)
_epU = (Edge.UB, Edge.UR, Edge.UF, Edge.UL,
        Edge.DR, Edge.DF, Edge.DL, Edge.DB,
        Edge.FR, Edge.FL, Edge.BL, Edge.BR)
_eoU = (0,0,0,0,0,0,0,0,0,0,0,0)

_cpR = (Corner.DFR, Corner.UFL, Corner.ULB, Corner.URF,
        Corner.DRB, Corner.DLF, Corner.DBL, Corner.UBR)
_coR = (2,0,0,1,1,0,0,2)
_epR = (Edge.FR, Edge.UF, Edge.UL, Edge.UB,
        Edge.BR, Edge.DF, Edge.DL, Edge.DB,
        Edge.DR, Edge.FL, Edge.BL, Edge.UR)
_eoR = (0,0,0,0,0,0,0,0,0,0,0,0)

_cpF = (Corner.UFL, Corner.DLF, Corner.ULB, Corner.UBR,
        Corner.URF, Corner.DFR, Corner.DBL, Corner.DRB)
_coF = (1,2,0,0,2,1,0,0)
_epF = (Edge.UR, Edge.FL, Edge.UL, Edge.UB,
        Edge.DR, Edge.FR, Edge.DL, Edge.DB,
        Edge.UF, Edge.DF, Edge.BL, Edge.BR)
_eoF = (0,1,0,0,0,1,0,0,1,1,0,0)

_cpD = (Corner.URF, Corner.UFL, Corner.ULB, Corner.UBR,
        Corner.DLF, Corner.DBL, Corner.DRB, Corner.DFR)
_coD = (0,0,0,0,0,0,0,0)
_epD = (Edge.UR, Edge.UF, Edge.UL, Edge.UB,
        Edge.DF, Edge.DL, Edge.DB, Edge.DR,
        Edge.FR, Edge.FL, Edge.BL, Edge.BR)
_eoD = (0,0,0,0,0,0,0,0,0,0,0,0)

_cpL = (Corner.URF, Corner.ULB, Corner.DBL, Corner.UBR,
        Corner.DFR, Corner.UFL, Corner.DLF, Corner.DRB)
_coL = (0,1,2,0,0,2,1,0)
_epL = (Edge.UR, Edge.UF, Edge.BL, Edge.UB,
        Edge.DR, Edge.DF, Edge.FL, Edge.DB,
        Edge.FR, Edge.UL, Edge.DL, Edge.BR)
_eoL = (0,0,0,0,0,0,0,0,0,0,0,0)

_cpB = (Corner.URF, Corner.UFL, Corner.UBR, Corner.DRB,
        Corner.DFR, Corner.DLF, Corner.ULB, Corner.DBL)
_coB = (0,0,1,2,0,0,2,1)
_epB = (Edge.UR, Edge.UF, Edge.UL, Edge.BR,
        Edge.DR, Edge.DF, Edge.DL, Edge.BL,
        Edge.FR, Edge.FL, Edge.UB, Edge.DB)
_eoB = (0,0,0,1,0,0,0,1,0,0,1,1)

class CubieCube:
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        if cp and co and ep and eo:
            self.cp = cp[:]
            self.co = co[:]
            self.ep = ep[:]
            self.eo = eo[:]
        else:
            # solved cube
            self.cp = [Corner.URF, Corner.UFL, Corner.ULB, Corner.UBR,
                       Corner.DFR, Corner.DLF, Corner.DBL, Corner.DRB]
            self.co = [0]*8
            self.ep = [Edge.UR, Edge.UF, Edge.UL, Edge.UB,
                       Edge.DR, Edge.DF, Edge.DL, Edge.DB,
                       Edge.FR, Edge.FL, Edge.BL, Edge.BR]
            self.eo = [0]*12

    def corner_multiply(self, b):
        self.cp = [self.cp[b.cp[i]] for i in range(8)]
        self.co = [(self.co[b.cp[i]] + b.co[i]) % 3 for i in range(8)]

    def edge_multiply(self, b):
        self.ep = [self.ep[b.ep[i]] for i in range(12)]
        self.eo = [(self.eo[b.ep[i]] + b.eo[i]) % 2 for i in range(12)]

    def multiply(self, b):
        self.corner_multiply(b)
        self.edge_multiply(b)

    def move(self, i):
        self.multiply(MOVE_CUBE[i])

    def inverse_cubiecube(self):
        inv = CubieCube()
        for e in range(12):
            inv.ep[self.ep[e]] = e
        for e in range(12):
            inv.eo[e] = self.eo[inv.ep[e]]
        for c in range(8):
            inv.cp[self.cp[c]] = c
        for c in range(8):
            inv.co[c] = (-self.co[inv.cp[c]]) % 3
        return inv

    def to_facecube(self):
        # will be defined after FaceCube
        return _cubie_to_facecube(self)

    @property
    def corner_parity(self):
        s = 0
        for i in range(7,0,-1):
            for j in range(i-1,-1,-1):
                if self.cp[j] > self.cp[i]:
                    s += 1
        return s % 2

    @property
    def edge_parity(self):
        s = 0
        for i in range(11,0,-1):
            for j in range(i-1,-1,-1):
                if self.ep[j] > self.ep[i]:
                    s += 1
        return s % 2

    # Phase 1 coordinates
    @property
    def twist(self):
        return reduce(lambda x,y: 3*x + y, self.co[:7])

    @twist.setter
    def twist(self, twist):
        if not 0 <= twist < 3**7:
            raise ValueError("twist out of range")
        total = 0
        for i in range(7):
            x = twist % 3
            self.co[6-i] = x
            total += x
            twist //= 3
        self.co[7] = (-total) % 3

    @property
    def flip(self):
        return reduce(lambda x,y: 2*x + y, self.eo[:11])

    @flip.setter
    def flip(self, flip):
        if not 0 <= flip < 2**11:
            raise ValueError("flip out of range")
        total = 0
        for i in range(11):
            x = flip % 2
            self.eo[10-i] = x
            total += x
            flip //= 2
        self.eo[11] = (-total) % 2

    @property
    def udslice(self):
        udslice, seen = 0, 0
        for j in range(12):
            if 8 <= self.ep[j] < 12:
                seen += 1
            elif seen >= 1:
                udslice += choose(j, seen-1)
        return udslice

    @udslice.setter
    def udslice(self, udslice):
        if not 0 <= udslice < choose(12,4):
            raise ValueError("udslice out of range")
        slice_edges = [Edge.FR, Edge.FL, Edge.BL, Edge.BR]
        other_edges = [Edge.UR, Edge.UF, Edge.UL, Edge.UB,
                       Edge.DR, Edge.DF, Edge.DL, Edge.DB]
        for i in range(12):
            self.ep[i] = Edge.DB
        seen = 3
        for j in range(11,-1,-1):
            if udslice - choose(j, seen) < 0:
                self.ep[j] = slice_edges[seen]
                seen -= 1
            else:
                udslice -= choose(j, seen)
        x = 0
        for j in range(12):
            if self.ep[j] == Edge.DB:
                self.ep[j] = other_edges[x]
                x += 1

    # Phase 2 coordinates
    @property
    def edge4(self):
        e4 = self.ep[8:]
        res = 0
        for j in range(3,0,-1):
            s = 0
            for i in range(j):
                if e4[i] > e4[j]:
                    s += 1
            res = j * (res + s)
        return res

    @edge4.setter
    def edge4(self, edge4):
        if not 0 <= edge4 < 24:
            raise ValueError("edge4 out of range")
        slice_edges = [Edge.FR, Edge.FL, Edge.BL, Edge.BR]
        coeffs = [0]*3
        for i in range(1,4):
            coeffs[i-1] = edge4 % (i+1)
            edge4 //= i+1
        perm = [0]*4
        for i in range(2,-1,-1):
            perm[i+1] = slice_edges.pop(i+1 - coeffs[i])
        perm[0] = slice_edges[0]
        self.ep[8:] = perm[:]

    @property
    def edge8(self):
        res = 0
        for j in range(7,0,-1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            res = j * (res + s)
        return res

    @edge8.setter
    def edge8(self, edge8):
        edges = list(range(8))
        perm = [0]*8
        coeffs = [0]*7
        for i in range(1,8):
            coeffs[i-1] = edge8 % (i+1)
            edge8 //= i+1
        for i in range(6,-1,-1):
            perm[i+1] = edges.pop(i+1 - coeffs[i])
        perm[0] = edges[0]
        self.ep[:8] = perm[:]

    @property
    def corner(self):
        res = 0
        for j in range(7,0,-1):
            s = 0
            for i in range(j):
                if self.cp[i] > self.cp[j]:
                    s += 1
            res = j * (res + s)
        return res

    @corner.setter
    def corner(self, corn):
        corners = list(range(8))
        perm = [0]*8
        coeffs = [0]*7
        for i in range(1,8):
            coeffs[i-1] = corn % (i+1)
            corn //= i+1
        for i in range(6,-1,-1):
            perm[i+1] = corners.pop(i+1 - coeffs[i])
        perm[0] = corners[0]
        self.cp = perm[:]

    # Not used in solving, but needed for random cube generation
    @property
    def edge(self):
        res = 0
        for j in range(11,0,-1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            res = j * (res + s)
        return res

    @edge.setter
    def edge(self, edge):
        edges = list(range(12))
        perm = [0]*12
        coeffs = [0]*11
        for i in range(1,12):
            coeffs[i-1] = edge % (i+1)
            edge //= i+1
        for i in range(10,-1,-1):
            perm[i+1] = edges.pop(i+1 - coeffs[i])
        perm[0] = edges[0]
        self.ep = perm[:]

    def verify(self):
        # Check solvability
        edge_count = [0]*12
        for e in self.ep:
            edge_count[e] += 1
        if any(c != 1 for c in edge_count):
            return -2
        if sum(self.eo) % 2 != 0:
            return -3
        corner_count = [0]*8
        for c in self.cp:
            corner_count[c] += 1
        if any(c != 1 for c in corner_count):
            return -4
        if sum(self.co) % 3 != 0:
            return -5
        if self.edge_parity != self.corner_parity:
            return -6
        return 0

# The six basic moves as CubieCube instances
MOVE_CUBE = [CubieCube() for _ in range(6)]
MOVE_CUBE[0].cp = _cpU; MOVE_CUBE[0].co = _coU; MOVE_CUBE[0].ep = _epU; MOVE_CUBE[0].eo = _eoU
MOVE_CUBE[1].cp = _cpR; MOVE_CUBE[1].co = _coR; MOVE_CUBE[1].ep = _epR; MOVE_CUBE[1].eo = _eoR
MOVE_CUBE[2].cp = _cpF; MOVE_CUBE[2].co = _coF; MOVE_CUBE[2].ep = _epF; MOVE_CUBE[2].eo = _eoF
MOVE_CUBE[3].cp = _cpD; MOVE_CUBE[3].co = _coD; MOVE_CUBE[3].ep = _epD; MOVE_CUBE[3].eo = _eoD
MOVE_CUBE[4].cp = _cpL; MOVE_CUBE[4].co = _coL; MOVE_CUBE[4].ep = _epL; MOVE_CUBE[4].eo = _eoL
MOVE_CUBE[5].cp = _cpB; MOVE_CUBE[5].co = _coB; MOVE_CUBE[5].ep = _epB; MOVE_CUBE[5].eo = _eoB

# ----------------------------------------------------------------------
# cubes/facecube.py
# ----------------------------------------------------------------------
# Corner and edge facelet mappings
corner_facelet = (
    (Facelet.U9, Facelet.R1, Facelet.F3),
    (Facelet.U7, Facelet.F1, Facelet.L3),
    (Facelet.U1, Facelet.L1, Facelet.B3),
    (Facelet.U3, Facelet.B1, Facelet.R3),
    (Facelet.D3, Facelet.F9, Facelet.R7),
    (Facelet.D1, Facelet.L9, Facelet.F7),
    (Facelet.D7, Facelet.B9, Facelet.L7),
    (Facelet.D9, Facelet.R9, Facelet.B7),
)

edge_facelet = (
    (Facelet.U6, Facelet.R2),
    (Facelet.U8, Facelet.F2),
    (Facelet.U4, Facelet.L2),
    (Facelet.U2, Facelet.B2),
    (Facelet.D6, Facelet.R8),
    (Facelet.D2, Facelet.F8),
    (Facelet.D4, Facelet.L8),
    (Facelet.D8, Facelet.B8),
    (Facelet.F6, Facelet.R4),
    (Facelet.F4, Facelet.L6),
    (Facelet.B6, Facelet.L4),
    (Facelet.B4, Facelet.R6),
)

corner_color = (
    (Color.U, Color.R, Color.F),
    (Color.U, Color.F, Color.L),
    (Color.U, Color.L, Color.B),
    (Color.U, Color.B, Color.R),
    (Color.D, Color.F, Color.R),
    (Color.D, Color.L, Color.F),
    (Color.D, Color.B, Color.L),
    (Color.D, Color.R, Color.B),
)

edge_color = (
    (Color.U, Color.R),
    (Color.U, Color.F),
    (Color.U, Color.L),
    (Color.U, Color.B),
    (Color.D, Color.R),
    (Color.D, Color.F),
    (Color.D, Color.L),
    (Color.D, Color.B),
    (Color.F, Color.R),
    (Color.F, Color.L),
    (Color.B, Color.L),
    (Color.B, Color.R),
)

class FaceCube:
    def __init__(self, cube_string="".join(c*9 for c in "URFDLB")):
        self.f = [0]*54
        for i,ch in enumerate(cube_string):
            self.f[i] = Color[ch]

    def to_string(self):
        return "".join(Color(i).name for i in self.f)

    def to_cubiecube(self):
        cc = CubieCube()
        for i in range(8):
            # find orientation
            for ori in range(3):
                if self.f[corner_facelet[i][ori]] in (Color.U, Color.D):
                    break
            col1 = self.f[corner_facelet[i][(ori+1)%3]]
            col2 = self.f[corner_facelet[i][(ori+2)%3]]
            for j in range(8):
                if col1 == corner_color[j][1] and col2 == corner_color[j][2]:
                    cc.cp[i] = j
                    cc.co[i] = ori
                    break
        for i in range(12):
            for j in range(12):
                if (self.f[edge_facelet[i][0]] == edge_color[j][0] and
                    self.f[edge_facelet[i][1]] == edge_color[j][1]):
                    cc.ep[i] = j
                    cc.eo[i] = 0
                    break
                if (self.f[edge_facelet[i][0]] == edge_color[j][1] and
                    self.f[edge_facelet[i][1]] == edge_color[j][0]):
                    cc.ep[i] = j
                    cc.eo[i] = 1
                    break
        return cc

# Forward declaration helper for CubieCube.to_facecube
def _cubie_to_facecube(cube):
    ret = FaceCube()
    for i in range(8):
        j = cube.cp[i]
        ori = cube.co[i]
        for k in range(3):
            ret.f[corner_facelet[i][(k+ori)%3]] = corner_color[j][k]
    for i in range(12):
        j = cube.ep[i]
        ori = cube.eo[i]
        for k in range(2):
            ret.f[edge_facelet[i][(k+ori)%2]] = edge_color[j][k]
    return ret

# Bind the method
CubieCube.to_facecube = _cubie_to_facecube

# ----------------------------------------------------------------------
# moves.py
# ----------------------------------------------------------------------
class PruningTable:
    def __init__(self, table, stride):
        self.table = table
        self.stride = stride
    def __getitem__(self, x):
        return self.table[x[0]*self.stride + x[1]]

class moves:
    _moves_loaded = False

    TWIST   = 2187      # 3^7
    FLIP    = 2048      # 2^11
    UDSLICE = 495       # C(12,4)
    EDGE4   = 24        # 4!
    EDGE8   = 40320     # 8!
    CORNER  = 40320     # 8!
    EDGE    = 479001600 # 12!  (not used in solving)
    MOVES   = 18

    def __init__(self):
        if not self._moves_loaded:
            self.load_moves()

    @classmethod
    def load_moves(cls):
        if os.path.isfile("Cube/moves.json"):
            with open("Cube/moves.json","r") as f:
                moves = json.load(f)
            cls.twist_move = moves["twist_move"]
            cls.flip_move = moves["flip_move"]
            cls.udslice_move = moves["udslice_move"]
            cls.edge4_move = moves["edge4_move"]
            cls.edge8_move = moves["edge8_move"]
            cls.corner_move = moves["corner_move"]
            cls.udslice_twist_prune = PruningTable(moves["udslice_twist_prune"], cls.TWIST)
            cls.udslice_flip_prune   = PruningTable(moves["udslice_flip_prune"],   cls.FLIP)
            cls.edge4_edge8_prune    = PruningTable(moves["edge4_edge8_prune"],    cls.EDGE8)
            cls.edge4_corner_prune   = PruningTable(moves["edge4_corner_prune"],   cls.CORNER)
        else:
            # Generate all moves
            cls.twist_move = cls.make_twist_table()
            cls.flip_move = cls.make_flip_table()
            cls.udslice_move = cls.make_udslice_table()
            cls.edge4_move = cls.make_edge4_table()
            cls.edge8_move = cls.make_edge8_table()
            cls.corner_move = cls.make_corner_table()
            cls.udslice_twist_prune = cls.make_udslice_twist_prune()
            cls.udslice_flip_prune   = cls.make_udslice_flip_prune()
            cls.edge4_edge8_prune    = cls.make_edge4_edge8_prune()
            cls.edge4_corner_prune   = cls.make_edge4_corner_prune()

            # Save for future runs
            out = {
                "twist_move": cls.twist_move,
                "flip_move": cls.flip_move,
                "udslice_move": cls.udslice_move,
                "edge4_move": cls.edge4_move,
                "edge8_move": cls.edge8_move,
                "corner_move": cls.corner_move,
                "udslice_twist_prune": cls.udslice_twist_prune.table,
                "udslice_flip_prune":   cls.udslice_flip_prune.table,
                "edge4_edge8_prune":    cls.edge4_edge8_prune.table,
                "edge4_corner_prune":   cls.edge4_corner_prune.table,
            }
            with open("Cube/moves.json","w") as f:
                json.dump(out, f)

        cls._moves_loaded = True

    @classmethod
    def make_twist_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.TWIST)]
        a = CubieCube()
        for i in range(cls.TWIST):
            a.twist = i
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    tab[i][3*j+k] = a.twist
                a.corner_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_flip_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.FLIP)]
        a = CubieCube()
        for i in range(cls.FLIP):
            a.flip = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    tab[i][3*j+k] = a.flip
                a.edge_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_udslice_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.UDSLICE)]
        a = CubieCube()
        for i in range(cls.UDSLICE):
            a.udslice = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    tab[i][3*j+k] = a.udslice
                a.edge_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_edge4_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.EDGE4)]
        a = CubieCube()
        for i in range(cls.EDGE4):
            a.edge4 = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    if k%2==0 and j%3!=0:
                        tab[i][3*j+k] = -1
                    else:
                        tab[i][3*j+k] = a.edge4
                a.edge_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_edge8_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.EDGE8)]
        a = CubieCube()
        for i in range(cls.EDGE8):
            a.edge8 = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    if k%2==0 and j%3!=0:
                        tab[i][3*j+k] = -1
                    else:
                        tab[i][3*j+k] = a.edge8
                a.edge_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_corner_table(cls):
        tab = [[0]*cls.MOVES for _ in range(cls.CORNER)]
        a = CubieCube()
        for i in range(cls.CORNER):
            a.corner = i
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    if k%2==0 and j%3!=0:
                        tab[i][3*j+k] = -1
                    else:
                        tab[i][3*j+k] = a.corner
                a.corner_multiply(MOVE_CUBE[j])
        return tab

    @classmethod
    def make_udslice_twist_prune(cls):
        size = cls.UDSLICE * cls.TWIST
        prune = [-1]*size
        prune[0] = 0
        count, depth = 1, 0
        while count < size:
            for i in range(size):
                if prune[i] == depth:
                    m = [ cls.udslice_move[i//cls.TWIST][j] * cls.TWIST +
                          cls.twist_move[i%cls.TWIST][j] for j in range(18) ]
                    for x in m:
                        if prune[x] == -1:
                            count += 1
                            prune[x] = depth+1
            depth += 1
        return PruningTable(prune, cls.TWIST)

    @classmethod
    def make_udslice_flip_prune(cls):
        size = cls.UDSLICE * cls.FLIP
        prune = [-1]*size
        prune[0] = 0
        count, depth = 1, 0
        while count < size:
            for i in range(size):
                if prune[i] == depth:
                    m = [ cls.udslice_move[i//cls.FLIP][j] * cls.FLIP +
                          cls.flip_move[i%cls.FLIP][j] for j in range(18) ]
                    for x in m:
                        if prune[x] == -1:
                            count += 1
                            prune[x] = depth+1
            depth += 1
        return PruningTable(prune, cls.FLIP)

    @classmethod
    def make_edge4_edge8_prune(cls):
        size = cls.EDGE4 * cls.EDGE8
        prune = [-1]*size
        prune[0] = 0
        count, depth = 1, 0
        while count < size:
            for i in range(size):
                if prune[i] == depth:
                    m = [ cls.edge4_move[i//cls.EDGE8][j] * cls.EDGE8 +
                          cls.edge8_move[i%cls.EDGE8][j] for j in range(18) ]
                    for x in m:
                        if prune[x] == -1:
                            count += 1
                            prune[x] = depth+1
            depth += 1
        return PruningTable(prune, cls.EDGE8)

    @classmethod
    def make_edge4_corner_prune(cls):
        size = cls.EDGE4 * cls.CORNER
        prune = [-1]*size
        prune[0] = 0
        count, depth = 1, 0
        while count < size:
            for i in range(size):
                if prune[i] == depth:
                    m = [ cls.edge4_move[i//cls.CORNER][j] * cls.CORNER +
                          cls.corner_move[i%cls.CORNER][j] for j in range(18) ]
                    for x in m:
                        if prune[x] == -1:
                            count += 1
                            prune[x] = depth+1
            depth += 1
        return PruningTable(prune, cls.CORNER)

# ----------------------------------------------------------------------
# cubes/coordcube.py
# ----------------------------------------------------------------------
class CoordCube:
    def __init__(self, twist=0, flip=0, udslice=0, edge4=0, edge8=0, corner=0):
        self.moves = moves()
        self.twist = twist
        self.flip = flip
        self.udslice = udslice
        self.edge4 = edge4
        self.edge8 = edge8
        self.corner = corner

    @classmethod
    def from_cubiecube(cls, cube):
        return cls(cube.twist, cube.flip, cube.udslice,
                   cube.edge4, cube.edge8, cube.corner)

    def move(self, mv):
        self.twist   = self.moves.twist_move[self.twist][mv]
        self.flip    = self.moves.flip_move[self.flip][mv]
        self.udslice = self.moves.udslice_move[self.udslice][mv]
        self.edge4   = self.moves.edge4_move[self.edge4][mv]
        self.edge8   = self.moves.edge8_move[self.edge8][mv]
        self.corner  = self.moves.corner_move[self.corner][mv]

# ----------------------------------------------------------------------
# solve.py
# ----------------------------------------------------------------------
class SolutionManager:
    def __init__(self, facelets):
        self.moves = moves()
        self.facelets = facelets.upper()
        status = self.verify()
        if status:
            msg = {
                -1: "each colour appears exactly 9 times",
                -2: "not all edges exist exactly once",
                -3: "one edge should be flipped",
                -4: "not all corners exist exactly once",
                -5: "one corner should be twisted",
                -6: "two corners or edges should be exchanged",
            }[status]
            raise ValueError("Invalid cube: "+msg)

    def solve(self, max_length=25, timeout=float('inf')):
        self._phase_1_initialise(max_length)
        self._allowed_length = max_length
        self._timeout = timeout

        for depth in range(self._allowed_length):
            n = self._phase_1_search(0, depth)
            if n >= 0:
                return self._solution_to_string(n)
            elif n == -2:
                return -2
        return -1

    def verify(self):
        count = [0]*6
        try:
            for ch in self.facelets:
                count[Color[ch]] += 1
        except (IndexError, ValueError):
            return -1
        if any(c != 9 for c in count):
            return -1
        fc = FaceCube(self.facelets)
        cc = fc.to_cubiecube()
        return cc.verify()

    def _phase_1_initialise(self, max_length):
        self.axis = [0]*max_length
        self.power = [0]*max_length
        self.twist = [0]*max_length
        self.flip = [0]*max_length
        self.udslice = [0]*max_length
        self.corner = [0]*max_length
        self.edge4 = [0]*max_length
        self.edge8 = [0]*max_length
        self.min_dist_1 = [0]*max_length
        self.min_dist_2 = [0]*max_length

        self.f = FaceCube(self.facelets)
        self.c = CoordCube.from_cubiecube(self.f.to_cubiecube())
        self.twist[0] = self.c.twist
        self.flip[0] = self.c.flip
        self.udslice[0] = self.c.udslice
        self.corner[0] = self.c.corner
        self.edge4[0] = self.c.edge4
        self.edge8[0] = self.c.edge8
        self.min_dist_1[0] = self._phase_1_cost(0)

    def _phase_2_initialise(self, n):
        if time.time() > self._timeout:
            return -2
        cc = self.f.to_cubiecube()
        for i in range(n):
            for _ in range(self.power[i]):
                cc.move(self.axis[i])
        self.edge4[n] = cc.edge4
        self.edge8[n] = cc.edge8
        self.corner[n] = cc.corner
        self.min_dist_2[n] = self._phase_2_cost(n)
        for depth in range(self._allowed_length - n):
            m = self._phase_2_search(n, depth)
            if m >= 0:
                return m
        return -1

    def _phase_1_cost(self, n):
        return max(
            self.moves.udslice_twist_prune[self.udslice[n], self.twist[n]],
            self.moves.udslice_flip_prune[self.udslice[n], self.flip[n]]
        )

    def _phase_2_cost(self, n):
        return max(
            self.moves.edge4_corner_prune[self.edge4[n], self.corner[n]],
            self.moves.edge4_edge8_prune[self.edge4[n], self.edge8[n]]
        )

    def _phase_1_search(self, n, depth):
        if time.time() > self._timeout:
            return -2
        if self.min_dist_1[n] == 0:
            return self._phase_2_initialise(n)
        if self.min_dist_1[n] <= depth:
            for i in range(6):
                if n>0 and self.axis[n-1] in (i, i+3):
                    continue
                for j in range(1,4):
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3*i + j - 1

                    self.twist[n+1]   = self.moves.twist_move[self.twist[n]][mv]
                    self.flip[n+1]    = self.moves.flip_move[self.flip[n]][mv]
                    self.udslice[n+1] = self.moves.udslice_move[self.udslice[n]][mv]
                    self.min_dist_1[n+1] = self._phase_1_cost(n+1)

                    m = self._phase_1_search(n+1, depth-1)
                    if m >= 0:
                        return m
                    if m == -2:
                        return -2
        return -1

    def _phase_2_search(self, n, depth):
        if self.min_dist_2[n] == 0:
            return n
        if self.min_dist_2[n] <= depth:
            for i in range(6):
                if n>0 and self.axis[n-1] in (i, i+3):
                    continue
                for j in range(1,4):
                    if i in (1,2,4,5) and j != 2:
                        continue
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3*i + j - 1

                    self.edge4[n+1]   = self.moves.edge4_move[self.edge4[n]][mv]
                    self.edge8[n+1]   = self.moves.edge8_move[self.edge8[n]][mv]
                    self.corner[n+1]  = self.moves.corner_move[self.corner[n]][mv]
                    self.min_dist_2[n+1] = self._phase_2_cost(n+1)

                    m = self._phase_2_search(n+1, depth-1)
                    if m >= 0:
                        return m
        return -1

    def _solution_to_string(self, length):
        def recover(mv):
            ax, pw = mv
            if pw == 1:
                return Color(ax).name
            if pw == 2:
                return Color(ax).name + "2"
            if pw == 3:
                return Color(ax).name + "'"
            raise RuntimeError("Invalid move")
        moves = zip(self.axis[:length], self.power[:length])
        return " ".join(map(recover, moves))

# ----------------------------------------------------------------------
# random.py
# ----------------------------------------------------------------------
def random_cube():
    cc = CubieCube()
    cc.flip = random.randint(0, moves.FLIP)
    cc.twist = random.randint(0, moves.TWIST)
    while True:
        cc.corner = random.randint(0, moves.CORNER)
        cc.edge = random.randint(0, moves.EDGE)
        if cc.edge_parity == cc.corner_parity:
            break
    return cc.to_facecube().to_string()

# ----------------------------------------------------------------------
# __init__.py (public interface)
# ----------------------------------------------------------------------
def solve(cube_string, max_length=25, max_time=10):
    sm = SolutionManager(cube_string)
    solution = sm.solve(max_length, time.time() + max_time)
    if isinstance(solution, str):
        return solution
    elif solution == -2:
        raise RuntimeError("max_time exceeded, no solution found")
    elif solution == -1:
        raise RuntimeError("no solution found, try increasing max_length")
    raise RuntimeError(f"Unexpected return {solution}")

def solve_best(cube_string, max_length=25, max_time=10):
    return list(solve_best_generator(cube_string, max_length, max_time))

def solve_best_generator(cube_string, max_length=25, max_time=10):
    sm = SolutionManager(cube_string)
    timeout = time.time() + max_time
    while True:
        solution = sm.solve(max_length, timeout)
        if isinstance(solution, str):
            yield solution
            max_length = len(solution.split(" ")) - 1
        elif solution in (-2, -1):
            break
        else:
            raise RuntimeError(f"Unexpected return {solution}")