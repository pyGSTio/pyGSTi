"""
Variables for working with the 2-qubit model containing the gates
I*X(pi/2), I*Y(pi/2), I*Z(pi/2), X(pi/2)*I, Y(pi/2)*I, Z(pi/2)*I and CNOT.
"""
#***************************************************************************************************
# Copyright 2015, 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 or in the LICENSE file in the root pyGSTi directory.
#***************************************************************************************************

from collections import OrderedDict
from pygsti.construction import circuitconstruction as _strc
from pygsti.construction import modelconstruction as _setc

from pygsti.modelpacks._modelpack import SMQModelPack

fiducials16 = _strc.circuit_list([(), (('Gx', 1),), (('Gy', 1),), (('Gx', 1), ('Gx', 1)), (('Gx', 0),), (('Gx', 0), ('Gx', 1)), (('Gx', 0), ('Gy', 1)), (('Gx', 0), ('Gx', 1), ('Gx', 1)), (('Gy', 0),), (('Gy', 0), ('Gx', 1)), (('Gy', 0), ('Gy', 1)), (('Gy', 0), ('Gx', 1), ('Gx', 1)), (('Gx', 0), ('Gx', 0)), (('Gx', 0), ('Gx', 0), ('Gx', 1)), (('Gx', 0), ('Gx', 0), ('Gy', 1)), (('Gx', 0), ('Gx', 0), ('Gx', 1), ('Gx', 1))], line_labels=[0, 1])


class _Module(SMQModelPack):
    description = "I*X(pi/2), I*Y(pi/2), I*Z(pi/2), X(pi/2)*I, Y(pi/2)*I, Z(pi/2)*I and CNOT gates"

    gates = [('Gx', 1), ('Gy', 1), ('Gz', 1), ('Gx', 0), ('Gy', 0), ('Gz', 0), ('Gcnot', 0, 1)]

    germs = _strc.circuit_list([((),), (('Gx', 0),), (('Gy', 0),), (('Gx', 1),), (('Gy', 1),), (('Gz', 0),), (('Gz', 1),), (('Gcnot', 0, 1),), (('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gz', 0)), (('Gx', 1), ('Gz', 1)), (('Gy', 0), ('Gcnot', 0, 1)), (('Gy', 1), ('Gy', 0)), (('Gx', 1), ('Gx', 0)), (('Gx', 1), ('Gy', 0)), (('Gy', 1), ('Gx', 0)), (('Gy', 1), ('Gcnot', 0, 1)), (('Gx', 0), ('Gcnot', 0, 1)), (('Gx', 1), ('Gcnot', 0, 1)), ((), ('Gx', 1)), ((), ('Gy', 1)), ((), ('Gy', 0)), ((), ('Gcnot', 0, 1)), (('Gz', 1), ('Gz', 0)), (('Gz', 1), ('Gy', 0)), (('Gx', 1), ('Gz', 0)), (('Gz', 1), ('Gx', 0)), (('Gy', 1), ('Gz', 0)), (('Gy', 0), ('Gz', 0)), (('Gz', 1), ('Gcnot', 0, 1)), (('Gx', 0), ('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gx', 0), ('Gz', 0)), (('Gy', 0), ('Gy', 0), ('Gz', 0)), (('Gx', 0), ('Gy', 0), ('Gz', 0)), (('Gx', 1), ('Gx', 1), ('Gz', 1)), (('Gy', 1), ('Gy', 1), ('Gz', 1)), (('Gx', 1), ('Gy', 1), ('Gz', 1)), (('Gx', 0), ('Gy', 0), ('Gy', 0)), (('Gx', 1), ('Gy', 1), ('Gy', 1)), (('Gy', 1), ('Gx', 0), ('Gx', 0)), (('Gy', 1), ('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gx', 0), ('Gy', 1)), (('Gx', 1), ('Gy', 0), ('Gx', 0)), (('Gx', 1), ('Gy', 0), ('Gy', 1)), (('Gx', 1), ('Gy', 1), ('Gy', 0)), (('Gx', 1), ('Gy', 1), ('Gx', 0)), (('Gy', 1), ('Gy', 0), ('Gx', 0)), (('Gy', 1), ('Gcnot', 0, 1), ('Gx', 0)), (('Gx', 1), ('Gx', 1), ('Gcnot', 0, 1)), (('Gx', 0), ('Gcnot', 0, 1), ('Gcnot', 0, 1)), (('Gy', 1), ('Gy', 0), ('Gcnot', 0, 1)), (('Gy', 0), ('Gcnot', 0, 1), ('Gcnot', 0, 1)), (('Gx', 1), ('Gy', 1), ('Gcnot', 0, 1)), (('Gy', 1), ('Gcnot', 0, 1), ('Gcnot', 0, 1)), (('Gx', 0), ('Gy', 0), ()), (('Gx', 0), (), ('Gy', 0)), (('Gx', 0), (), ()), (('Gy', 0), (), ()), (('Gx', 1), ('Gy', 1), ()), (('Gx', 1), (), ('Gy', 1)), (('Gx', 1), (), ()), (('Gy', 1), (), ()), ((), ('Gx', 1), ('Gy', 0)), ((), ('Gy', 1), ('Gy', 0)), ((), ('Gy', 0), ('Gx', 1)), ((), ('Gx', 0), ('Gz', 0)), ((), ('Gy', 0), ('Gz', 0)), ((), ('Gx', 1), ('Gz', 1)), ((), ('Gy', 1), ('Gz', 1)), (('Gz', 1), ('Gz', 0), ('Gy', 0)), (('Gy', 1), ('Gz', 0), ('Gz', 1)), (('Gz', 0), ('Gz', 0), ('Gcnot', 0, 1)), (('Gy', 1), ('Gy', 0), ('Gz', 1)), (('Gz', 1), ('Gx', 0), ('Gcnot', 0, 1)), (('Gy', 0), ('Gz', 0), ('Gcnot', 0, 1)), (('Gx', 1), ('Gz', 0), ('Gz', 1)), (('Gz', 1), ('Gy', 0), ('Gcnot', 0, 1)), (('Gx', 0), ('Gz', 0), ('Gcnot', 0, 1)), (('Gz', 1), ('Gcnot', 0, 1), ('Gy', 0)), (('Gz', 1), ('Gcnot', 0, 1), ('Gx', 0)), (('Gx', 1), ('Gcnot', 0, 1), ('Gz', 0)), (('Gy', 1), ('Gz', 1), ('Gz', 1)), (('Gx', 1), ('Gz', 0), ('Gcnot', 0, 1)), (('Gcnot', 0, 1), ('Gx', 1), ('Gx', 0), ('Gx', 0)), (('Gy', 0), ('Gx', 1), ('Gx', 0), ('Gy', 1)), (('Gx', 1), ('Gy', 1), ('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gx', 1), ('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gy', 0), ('Gy', 0), ('Gy', 0)), (('Gy', 0), ('Gy', 0), ('Gy', 1), ('Gy', 0)), (('Gy', 0), ('Gx', 1), ('Gx', 1), ('Gx', 1)), (('Gx', 0), ('Gy', 0), ('Gx', 1), ('Gx', 1)), (('Gcnot', 0, 1), ('Gy', 0), ('Gcnot', 0, 1), ('Gx', 0)), (('Gcnot', 0, 1), ('Gx', 1), ('Gcnot', 0, 1), ('Gy', 1)), (('Gx', 1), ('Gx', 0), ('Gcnot', 0, 1), ('Gy', 1)), (('Gx', 1), ('Gy', 1), ('Gx', 0), ('Gcnot', 0, 1)), (('Gx', 0), ('Gy', 0), ('Gy', 0), ()), (('Gx', 1), ('Gy', 1), ('Gy', 1), ()), (('Gy', 1), ('Gx', 0), (), ()), (('Gx', 1), (), (), ('Gx', 0)), (('Gz', 1), ('Gz', 0), ('Gx', 0), ('Gz', 1)), (('Gy', 1), ('Gy', 0), ('Gx', 0), ('Gx', 0), ('Gy', 1)), (('Gx', 0), ('Gx', 0), ('Gy', 1), ('Gy', 0), ('Gy', 1)), (('Gy', 1), ('Gx', 1), ('Gx', 0), ('Gx', 1), ('Gx', 0)), (('Gy', 0), ('Gy', 1), ('Gy', 0), ('Gx', 1), ('Gx', 1)), (('Gy', 1), ('Gx', 0), ('Gx', 1), ('Gy', 1), ('Gy', 0)), (('Gy', 1), ('Gy', 1), ('Gx', 0), ('Gy', 0), ('Gx', 0)), (('Gy', 0), ('Gcnot', 0, 1), ('Gy', 1), ('Gy', 1), ('Gx', 0)), (('Gy', 1), ('Gz', 0), ('Gx', 0), ('Gx', 0), ('Gy', 1)), (('Gz', 1), ('Gz', 1), ('Gy', 0), ('Gz', 0), ('Gy', 0)), (('Gx', 0), ('Gx', 1), ('Gy', 1), ('Gx', 0), ('Gy', 1), ('Gy', 0)), (('Gx', 0), ('Gy', 1), ('Gx', 1), ('Gy', 0), ('Gx', 1), ('Gx', 1)), (('Gy', 0), ('Gy', 1), ('Gx', 0), ('Gy', 0), ('Gx', 0), ('Gcnot', 0, 1)), (('Gx', 0), ('Gx', 0), ('Gy', 0), ('Gx', 0), ('Gy', 0), ('Gy', 0)), (('Gx', 1), ('Gx', 1), ('Gy', 1), ('Gx', 1), ('Gy', 1), ('Gy', 1)), (('Gy', 0), ('Gx', 0), ('Gx', 1), ('Gy', 1), ('Gx', 0), ('Gx', 1)), (('Gy', 0), ('Gx', 0), ('Gx', 1), ('Gx', 0), ('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gx', 1), ('Gy', 1), ('Gy', 1), ('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gy', 1), ('Gy', 1), ('Gx', 1), ('Gx', 0), ('Gx', 0)), (('Gy', 0), ('Gy', 1), ('Gx', 0), ('Gy', 1), ('Gy', 1), ('Gy', 1)), (('Gy', 0), ('Gy', 0), ('Gy', 0), ('Gy', 1), ('Gy', 0), ('Gx', 1)), (('Gy', 1), ('Gy', 1), ('Gx', 0), ('Gy', 1), ('Gx', 1), ('Gy', 1)), (('Gy', 1), ('Gx', 1), ('Gy', 0), ('Gy', 0), ('Gx', 1), ('Gx', 0), ('Gy', 1)), (('Gy', 0), ('Gx', 0), ('Gy', 1), ('Gx', 0), ('Gx', 1), ('Gx', 0), ('Gy', 0), ('Gy', 1)), (('Gx', 1), ('Gx', 1), ('Gy', 0), ('Gx', 0), ('Gy', 1), ('Gx', 0), ('Gy', 1), ('Gy', 0))], line_labels=[0, 1])

    germs_lite = _strc.circuit_list([((),), (('Gx', 0),), (('Gy', 0),), (('Gx', 1),), (('Gy', 1),), (('Gz', 0),), (('Gz', 1),), (('Gcnot', 0, 1),), (('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gz', 0)), (('Gx', 1), ('Gz', 1)), (('Gy', 0), ('Gcnot', 0, 1)), (('Gx', 0), ('Gx', 0), ('Gy', 0)), (('Gx', 1), ('Gx', 1), ('Gy', 1)), (('Gx', 0), ('Gx', 0), ('Gz', 0)), (('Gy', 0), ('Gy', 0), ('Gz', 0)), (('Gx', 0), ('Gy', 0), ('Gz', 0)), (('Gx', 1), ('Gx', 1), ('Gz', 1)), (('Gy', 1), ('Gy', 1), ('Gz', 1)), (('Gx', 1), ('Gy', 1), ('Gz', 1)), (('Gcnot', 0, 1), ('Gx', 1), ('Gx', 0), ('Gx', 0)), (('Gx', 0), ('Gx', 1), ('Gy', 1), ('Gx', 0), ('Gy', 1), ('Gy', 0)), (('Gx', 0), ('Gy', 1), ('Gx', 1), ('Gy', 0), ('Gx', 1), ('Gx', 1)), (('Gy', 0), ('Gy', 1), ('Gx', 0), ('Gy', 0), ('Gx', 0), ('Gcnot', 0, 1)), (('Gy', 0), ('Gx', 0), ('Gy', 1), ('Gx', 0), ('Gx', 1), ('Gx', 0), ('Gy', 0), ('Gy', 1))], line_labels=[0, 1])

    fiducials = fiducials16

    prepStrs = fiducials16

    effectStrs = _strc.circuit_list([(), (('Gx', 1),), (('Gy', 1),), (('Gx', 1), ('Gx', 1)), (('Gx', 0),), (('Gy', 0),), (('Gx', 0), ('Gx', 0)), (('Gx', 0), ('Gx', 1)), (('Gx', 0), ('Gy', 1)), (('Gy', 0), ('Gx', 1)), (('Gy', 0), ('Gy', 1))], line_labels=[0, 1])

    clifford_compilation = None
    global_fidPairs = [(0, 1), (3, 9), (4, 1), (4, 4), (6, 0), (6, 1), (6, 4), (7, 1), (7, 10), (8, 7), (8, 8), (9, 1), (9, 5), (9, 8), (9, 10), (10, 2), (11, 4), (13, 1), (13, 4), (14, 1), (14, 2), (15, 9)]
    pergerm_fidPairsDict = {('Gzi',): [(0, 2), (0, 5), (0, 6), (0, 8), (1, 1), (1, 5), (1, 6), (1, 7), (2, 6), (3, 1), (3, 3), (3, 5), (3, 6), (3, 8), (3, 10), (4, 1), (4, 2), (4, 4), (4, 5), (4, 9), (5, 0), (5, 7), (6, 7), (6, 8), (6, 9), (8, 0), (8, 5), (8, 6), (9, 4), (9, 6), (9, 7), (10, 3), (10, 7), (10, 8), (11, 0), (11, 10), (12, 0), (12, 8), (13, 6), (13, 9), (14, 0), (14, 2), (14, 4), (14, 7), (15, 0), (15, 1)], ('Gix',): [(0, 5), (1, 0), (1, 1), (2, 2), (2, 5), (2, 9), (3, 3), (3, 4), (3, 8), (4, 0), (4, 2), (4, 7), (4, 8), (4, 10), (5, 0), (5, 1), (5, 2), (5, 6), (5, 8), (6, 7), (6, 8), (6, 9), (7, 0), (7, 4), (8, 5), (8, 9), (9, 5), (10, 8), (10, 10), (12, 2), (12, 4), (12, 7), (13, 2), (13, 3), (13, 9), (14, 0), (14, 5), (14, 6), (15, 5), (15, 8), (15, 9)], ('Gcnot',): [(0, 7), (1, 0), (2, 4), (4, 3), (5, 5), (5, 10), (6, 1), (6, 10), (7, 8), (8, 2), (8, 5), (8, 6), (9, 0), (9, 4), (9, 6), (9, 9), (10, 2), (10, 4), (10, 5), (11, 5), (12, 2), (13, 7), (14, 1), (14, 2), (14, 3), (14, 6), (15, 8), (15, 10)], ('Gyi',): [(3, 1), (4, 1), (4, 2), (5, 0), (5, 1), (5, 7), (6, 0), (6, 8), (7, 2), (7, 4), (7, 9), (8, 0), (8, 7), (9, 2), (9, 3), (10, 9), (10, 10), (14, 7), (14, 9), (15, 10)], ('Giy',): [(0, 0), (0, 7), (1, 1), (3, 5), (3, 6), (4, 2), (4, 4), (4, 5), (5, 3), (5, 7), (7, 1), (7, 8), (8, 5), (9, 4), (9, 5), (9, 9), (10, 5), (11, 5), (11, 6), (11, 8), (11, 10), (12, 0), (12, 3), (13, 10), (14, 0), (14, 5), (14, 6), (14, 7), (15, 0), (15, 6), (15, 9)], ('Giz',): [(0, 7), (2, 2), (3, 2), (3, 4), (3, 7), (3, 10), (4, 1), (4, 3), (4, 4), (4, 8), (5, 7), (6, 4), (6, 6), (6, 7), (6, 9), (7, 0), (8, 0), (8, 7), (9, 2), (9, 3), (10, 5), (10, 6), (10, 9), (10, 10), (11, 5), (11, 8), (12, 2), (12, 4), (12, 6), (12, 8), (13, 2), (13, 3), (14, 2), (14, 5), (14, 7), (14, 9), (15, 8)], ('Gii',): [(0, 8), (1, 0), (1, 1), (1, 3), (1, 10), (2, 5), (2, 9), (3, 3), (3, 9), (4, 3), (4, 8), (5, 0), (5, 5), (5, 7), (6, 4), (6, 6), (6, 8), (6, 10), (7, 0), (7, 2), (7, 3), (7, 4), (7, 6), (7, 10), (8, 3), (8, 5), (9, 3), (9, 4), (9, 5), (9, 6), (9, 8), (9, 9), (10, 3), (10, 9), (10, 10), (11, 1), (11, 5), (12, 5), (12, 7), (12, 9), (13, 0), (13, 10), (14, 0), (14, 1), (14, 2), (14, 6), (15, 0), (15, 5), (15, 6), (15, 7), (15, 8)], ('Gxi',): [(0, 7), (1, 1), (1, 7), (2, 7), (3, 3), (4, 9), (5, 4), (7, 2), (7, 10), (8, 2), (9, 2), (9, 8), (9, 9), (10, 1), (10, 10), (11, 2), (11, 5), (11, 6), (13, 2), (14, 7), (15, 2), (15, 3)], ('Giz', 'Gzi'): [(0, 0), (0, 4), (0, 9), (1, 1), (1, 6), (2, 0), (2, 1), (2, 7), (3, 7), (4, 2), (4, 10), (5, 4), (5, 7), (5, 9), (5, 10), (6, 8), (7, 2), (7, 4), (7, 5), (8, 0), (8, 6), (9, 8), (9, 10), (10, 2), (10, 3), (10, 4), (10, 5), (10, 9), (11, 10), (12, 1), (12, 8), (13, 9), (14, 7), (14, 10), (15, 0), (15, 3), (15, 8)], ('Giy', 'Gyi'): [(0, 6), (0, 8), (0, 10), (1, 0), (1, 1), (1, 3), (2, 9), (3, 8), (4, 4), (4, 7), (5, 7), (6, 1), (7, 0), (7, 8), (9, 10), (10, 5), (11, 5), (12, 5), (12, 6), (14, 0), (15, 0), (15, 6), (15, 8)], ('Giy', 'Gxi'): [(1, 1), (2, 8), (3, 0), (3, 2), (3, 6), (4, 7), (7, 2), (8, 6), (9, 1), (9, 7), (9, 9), (10, 2), (10, 10), (11, 8), (12, 6), (13, 2), (13, 7), (14, 2), (15, 5)], ('Gii', 'Giy'): [(0, 0), (0, 7), (1, 1), (3, 5), (3, 6), (4, 2), (4, 4), (4, 5), (5, 3), (5, 7), (7, 1), (7, 8), (8, 5), (9, 4), (9, 5), (9, 9), (10, 5), (11, 5), (11, 6), (11, 8), (11, 10), (12, 0), (12, 3), (13, 10), (14, 0), (14, 5), (14, 6), (14, 7), (15, 0), (15, 6), (15, 9)], ('Gix', 'Giy'): [(1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 9), (15, 1)], ('Gyi', 'Gzi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Giz'): [(0, 1), (0, 3), (3, 0), (3, 6), (5, 5), (5, 8), (6, 8), (7, 0), (8, 3), (8, 9), (9, 9), (10, 9), (10, 10), (11, 6), (15, 0)], ('Gii', 'Gcnot'): [(0, 7), (1, 0), (2, 4), (4, 3), (5, 5), (5, 10), (6, 1), (6, 10), (7, 8), (8, 2), (8, 5), (8, 6), (9, 0), (9, 4), (9, 6), (9, 9), (10, 2), (10, 4), (10, 5), (11, 5), (12, 2), (13, 7), (14, 1), (14, 2), (14, 3), (14, 6), (15, 8), (15, 10)], ('Gyi', 'Gcnot'): [(0, 2), (1, 0), (1, 4), (1, 9), (3, 10), (4, 3), (5, 7), (7, 4), (7, 7), (7, 8), (8, 7), (8, 9), (9, 2), (9, 6), (10, 3), (14, 10), (15, 4)], ('Gix', 'Gxi'): [(0, 0), (1, 5), (2, 4), (3, 3), (3, 5), (5, 2), (6, 1), (6, 8), (6, 10), (8, 6), (10, 2), (10, 8), (10, 10), (11, 8), (12, 1), (13, 1), (13, 4), (13, 6), (13, 10), (14, 8), (15, 3)], ('Gii', 'Gyi'): [(3, 1), (4, 1), (4, 2), (5, 0), (5, 1), (5, 7), (6, 0), (6, 8), (7, 2), (7, 4), (7, 9), (8, 0), (8, 7), (9, 2), (9, 3), (10, 9), (10, 10), (14, 7), (14, 9), (15, 10)], ('Gix', 'Gyi'): [(0, 5), (0, 9), (1, 6), (3, 1), (3, 2), (5, 0), (5, 4), (6, 0), (6, 8), (9, 7), (10, 9), (11, 1), (11, 4), (14, 4), (14, 9), (15, 5), (15, 7)], ('Gix', 'Gcnot'): [(2, 2), (3, 1), (4, 5), (4, 7), (4, 8), (5, 3), (5, 4), (8, 5), (9, 4), (9, 6), (10, 10), (12, 0), (13, 0), (14, 5), (15, 1), (15, 7), (15, 10)], ('Giz', 'Gxi'): [(1, 1), (2, 5), (3, 7), (3, 10), (4, 6), (5, 7), (6, 2), (6, 9), (7, 1), (7, 9), (8, 7), (8, 8), (10, 10), (11, 5), (12, 5), (14, 2), (14, 5), (14, 8), (15, 3), (15, 5)], ('Giz', 'Gcnot'): [(0, 0), (0, 8), (1, 2), (1, 7), (1, 9), (3, 0), (4, 5), (5, 8), (5, 9), (5, 10), (6, 3), (6, 9), (7, 5), (7, 6), (8, 0), (8, 5), (8, 8), (10, 8), (10, 10), (11, 6), (12, 8), (14, 0), (14, 1), (14, 10), (15, 2)], ('Giy', 'Gcnot'): [(0, 2), (1, 0), (1, 4), (1, 9), (3, 10), (4, 3), (5, 7), (7, 4), (7, 7), (7, 8), (8, 7), (8, 9), (9, 2), (9, 6), (10, 3), (14, 10), (15, 4)], ('Gxi', 'Gyi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gzi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gzi'): [(0, 7), (1, 1), (2, 6), (3, 2), (5, 9), (6, 3), (6, 4), (6, 5), (7, 3), (8, 1), (8, 6), (8, 10), (9, 0), (9, 5), (9, 6), (9, 9), (10, 4), (10, 7), (10, 8), (10, 9), (11, 0), (12, 0), (12, 9), (14, 5), (14, 10), (15, 3)], ('Gxi', 'Gcnot'): [(0, 1), (0, 5), (1, 3), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gii', 'Gix'): [(0, 5), (1, 0), (1, 1), (2, 2), (2, 5), (2, 9), (3, 3), (3, 4), (3, 8), (4, 0), (4, 2), (4, 7), (4, 8), (4, 10), (5, 0), (5, 1), (5, 2), (5, 6), (5, 8), (6, 7), (6, 8), (6, 9), (7, 0), (7, 4), (8, 5), (8, 9), (9, 5), (10, 8), (10, 10), (12, 2), (12, 4), (12, 7), (13, 2), (13, 3), (13, 9), (14, 0), (14, 5), (14, 6), (15, 5), (15, 8), (15, 9)], ('Gix', 'Gzi'): [(0, 5), (0, 9), (1, 2), (1, 8), (4, 4), (4, 10), (5, 0), (5, 4), (5, 9), (6, 0), (6, 1), (6, 3), (6, 10), (7, 1), (7, 5), (7, 8), (9, 4), (9, 8), (10, 10), (11, 3), (11, 7), (12, 1), (12, 4), (12, 9), (12, 10), (13, 7), (14, 2), (14, 7), (15, 1), (15, 4), (15, 7)], ('Giz', 'Gyi'): [(0, 6), (1, 6), (2, 3), (2, 9), (2, 10), (4, 7), (4, 9), (5, 2), (5, 5), (5, 7), (7, 4), (9, 2), (10, 2), (12, 5), (12, 6), (12, 10), (13, 1), (14, 9)], ('Gyi', 'Gyi', 'Gzi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gii', 'Gii'): [(3, 1), (4, 1), (4, 2), (5, 0), (5, 1), (5, 7), (6, 0), (6, 8), (7, 2), (7, 4), (7, 9), (8, 0), (8, 7), (9, 2), (9, 3), (10, 9), (10, 10), (14, 7), (14, 9), (15, 10)], ('Gii', 'Gxi', 'Gzi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gix', 'Giz'): [(0, 0), (0, 6), (1, 5), (2, 7), (4, 4), (6, 4), (7, 4), (7, 10), (9, 2), (9, 5), (10, 10), (11, 2), (12, 0), (13, 10), (14, 0)], ('Giy', 'Gcnot', 'Gxi'): [(0, 1), (0, 5), (1, 3), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Giy', 'Gii'): [(1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 9), (15, 1)], ('Gxi', 'Gyi', 'Gzi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gcnot', 'Gzi'): [(0, 1), (0, 5), (1, 5), (2, 5), (2, 7), (4, 4), (5, 0), (6, 0), (6, 10), (7, 0), (7, 5), (8, 5), (10, 10), (11, 9), (12, 7), (12, 9), (14, 2), (15, 5)], ('Gii', 'Giy', 'Giz'): [(0, 2), (0, 6), (3, 4), (4, 7), (5, 5), (6, 7), (7, 6), (8, 5), (10, 2), (10, 8), (11, 6), (11, 10), (12, 6), (14, 1), (14, 4)], ('Gix', 'Gxi', 'Giy'): [(0, 6), (3, 0), (5, 0), (6, 7), (7, 1), (8, 3), (9, 9), (10, 4), (10, 9), (12, 9), (13, 2), (14, 5), (14, 8), (14, 10), (15, 6)], ('Gxi', 'Gii', 'Gii'): [(0, 7), (1, 1), (1, 7), (2, 7), (3, 3), (4, 9), (5, 4), (7, 2), (7, 10), (8, 2), (9, 2), (9, 8), (9, 9), (10, 1), (10, 10), (11, 2), (11, 5), (11, 6), (13, 2), (14, 7), (15, 2), (15, 3)], ('Giz', 'Gcnot', 'Gxi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (7, 8), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 4), (15, 5)], ('Gix', 'Gyi', 'Gxi'): [(1, 10), (2, 10), (4, 8), (5, 5), (5, 6), (6, 10), (7, 0), (7, 5), (7, 6), (7, 8), (8, 5), (12, 5), (13, 0), (13, 2), (14, 1)], ('Gix', 'Giy', 'Gyi'): [(0, 1), (4, 2), (4, 7), (6, 7), (8, 3), (9, 5), (9, 7), (10, 0), (10, 4), (10, 5), (11, 2), (11, 9), (14, 6), (14, 8), (15, 3)], ('Giz', 'Gyi', 'Gcnot'): [(0, 1), (0, 5), (1, 3), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gii', 'Gii'): [(0, 0), (0, 7), (1, 1), (3, 5), (3, 6), (4, 2), (4, 4), (4, 5), (5, 3), (5, 7), (7, 1), (7, 8), (8, 5), (9, 4), (9, 5), (9, 9), (10, 5), (11, 5), (11, 6), (11, 8), (11, 10), (12, 0), (12, 3), (13, 10), (14, 0), (14, 5), (14, 6), (14, 7), (15, 0), (15, 6), (15, 9)], ('Giy', 'Gxi', 'Gxi'): [(1, 7), (2, 2), (4, 8), (7, 2), (7, 10), (8, 6), (9, 8), (9, 9), (10, 1), (11, 4), (11, 9), (12, 8), (12, 9), (13, 0), (13, 1), (13, 9)], ('Gii', 'Gix', 'Gyi'): [(0, 5), (0, 9), (1, 6), (3, 1), (3, 2), (5, 0), (5, 4), (6, 0), (6, 8), (9, 7), (10, 9), (11, 1), (11, 4), (14, 4), (14, 9), (15, 5), (15, 7)], ('Gzi', 'Gzi', 'Gcnot'): [(0, 7), (1, 0), (2, 4), (4, 3), (5, 5), (5, 10), (6, 1), (6, 10), (7, 8), (8, 2), (8, 5), (8, 6), (9, 0), (9, 4), (9, 6), (9, 9), (10, 2), (10, 4), (10, 5), (11, 5), (12, 2), (13, 7), (14, 1), (14, 2), (14, 3), (14, 6), (15, 8), (15, 10)], ('Giy', 'Gcnot', 'Gcnot'): [(0, 0), (0, 7), (1, 1), (3, 5), (3, 6), (4, 2), (4, 4), (4, 5), (5, 3), (5, 7), (7, 1), (7, 8), (8, 5), (9, 4), (9, 5), (9, 9), (10, 5), (11, 5), (11, 6), (11, 8), (11, 10), (12, 0), (12, 3), (13, 10), (14, 0), (14, 5), (14, 6), (14, 7), (15, 0), (15, 6), (15, 9)], ('Giy', 'Gyi', 'Giz'): [(3, 0), (4, 4), (5, 1), (5, 8), (6, 5), (7, 3), (8, 6), (8, 7), (9, 5), (10, 3), (11, 4), (14, 0), (14, 6), (14, 9), (15, 5)], ('Giz', 'Gzi', 'Gyi'): [(0, 7), (1, 10), (2, 10), (4, 8), (5, 5), (5, 6), (6, 1), (6, 10), (7, 0), (7, 5), (7, 6), (7, 8), (8, 5), (10, 2), (10, 5), (12, 5), (13, 0), (13, 2), (14, 1)], ('Gix', 'Giy', 'Giz'): [(0, 6), (0, 8), (0, 10), (1, 0), (1, 1), (1, 3), (2, 9), (3, 8), (4, 4), (4, 7), (5, 7), (6, 1), (7, 0), (7, 8), (9, 10), (10, 5), (11, 5), (12, 5), (12, 6), (14, 0), (15, 0), (15, 6), (15, 8)], ('Gii', 'Gix', 'Giz'): [(0, 1), (0, 3), (3, 0), (3, 6), (5, 5), (5, 8), (6, 8), (7, 0), (8, 3), (8, 9), (9, 9), (10, 9), (10, 10), (11, 6), (15, 0)], ('Gix', 'Gyi', 'Giy'): [(3, 0), (4, 4), (5, 1), (5, 8), (6, 5), (7, 3), (8, 6), (8, 7), (9, 5), (10, 3), (11, 4), (14, 0), (14, 6), (14, 9), (15, 5)], ('Gxi', 'Gii', 'Gyi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gzi', 'Gcnot'): [(0, 2), (1, 0), (1, 4), (1, 9), (2, 4), (2, 10), (4, 3), (7, 4), (7, 8), (8, 7), (8, 9), (9, 2), (9, 6), (10, 3), (15, 4)], ('Gix', 'Gix', 'Gcnot'): [(0, 6), (0, 7), (2, 2), (2, 3), (2, 5), (2, 9), (4, 4), (4, 9), (6, 1), (8, 10), (12, 3), (12, 9), (13, 3), (14, 10), (15, 3)], ('Gix', 'Gii', 'Gii'): [(0, 5), (1, 0), (1, 1), (2, 2), (2, 5), (2, 9), (3, 3), (3, 4), (3, 8), (4, 0), (4, 2), (4, 7), (4, 8), (4, 10), (5, 0), (5, 1), (5, 2), (5, 6), (5, 8), (6, 7), (6, 8), (6, 9), (7, 0), (7, 4), (8, 5), (8, 9), (9, 5), (10, 8), (10, 10), (12, 2), (12, 4), (12, 7), (13, 2), (13, 3), (13, 9), (14, 0), (14, 5), (14, 6), (15, 5), (15, 8), (15, 9)], ('Gix', 'Gzi', 'Gcnot'): [(0, 1), (0, 5), (1, 5), (2, 5), (2, 7), (4, 4), (5, 0), (6, 0), (6, 10), (7, 0), (7, 5), (8, 5), (10, 10), (11, 9), (12, 7), (12, 9), (14, 2), (15, 5)], ('Gxi', 'Gyi', 'Gii'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gix', 'Giy'): [(0, 0), (0, 6), (1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (6, 7), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 1), (13, 9), (15, 1)], ('Gix', 'Gzi', 'Giz'): [(0, 7), (1, 10), (2, 10), (4, 8), (5, 5), (5, 6), (6, 1), (6, 10), (7, 0), (7, 5), (7, 6), (7, 8), (8, 5), (10, 2), (10, 5), (12, 5), (13, 0), (13, 2), (14, 1)], ('Gii', 'Gyi', 'Gzi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gzi', 'Gcnot'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gii', 'Giy', 'Gyi'): [(0, 6), (0, 8), (0, 10), (1, 0), (1, 1), (1, 3), (2, 9), (3, 8), (4, 4), (4, 7), (5, 7), (6, 1), (7, 0), (7, 8), (9, 10), (10, 5), (11, 5), (12, 5), (12, 6), (14, 0), (15, 0), (15, 6), (15, 8)], ('Giy', 'Gxi', 'Gyi'): [(0, 9), (1, 1), (1, 9), (2, 7), (3, 4), (4, 4), (4, 10), (6, 0), (6, 3), (7, 0), (9, 4), (11, 5), (12, 4), (13, 7), (14, 0)], ('Giy', 'Gyi', 'Gxi'): [(0, 9), (1, 1), (1, 9), (2, 7), (3, 4), (4, 4), (4, 10), (6, 0), (6, 3), (7, 0), (9, 4), (11, 5), (12, 4), (13, 7), (14, 0)], ('Gii', 'Gyi', 'Gix'): [(0, 5), (0, 9), (1, 6), (3, 1), (3, 2), (5, 0), (5, 4), (6, 0), (6, 8), (9, 7), (10, 9), (11, 1), (11, 4), (14, 4), (14, 9), (15, 5), (15, 7)], ('Gix', 'Giy', 'Gxi'): [(0, 6), (3, 0), (5, 0), (6, 7), (7, 1), (8, 3), (9, 9), (10, 4), (10, 9), (12, 9), (13, 2), (14, 5), (14, 8), (14, 10), (15, 6)], ('Giy', 'Giz', 'Giz'): [(0, 5), (0, 9), (1, 1), (1, 7), (2, 3), (3, 5), (3, 9), (4, 4), (4, 7), (4, 8), (5, 7), (6, 2), (6, 5), (7, 7), (7, 9), (7, 10), (8, 0), (9, 9), (10, 3), (10, 7), (11, 3), (12, 9), (13, 3), (13, 4), (14, 6), (14, 10)], ('Giz', 'Gxi', 'Gcnot'): [(0, 1), (0, 5), (1, 3), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gcnot', 'Gcnot'): [(3, 1), (4, 1), (4, 2), (5, 0), (5, 1), (5, 7), (6, 0), (6, 8), (7, 2), (7, 4), (7, 9), (8, 0), (8, 7), (9, 2), (9, 3), (10, 9), (10, 10), (14, 7), (14, 9), (15, 10)], ('Gix', 'Giy', 'Gcnot'): [(0, 3), (1, 0), (1, 4), (3, 10), (4, 3), (5, 7), (7, 2), (7, 4), (7, 7), (7, 8), (8, 1), (8, 5), (8, 7), (8, 9), (9, 2), (9, 6), (10, 3), (14, 10), (15, 4)], ('Giy', 'Gyi', 'Gcnot'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (7, 8), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 4), (15, 5)], ('Giz', 'Gcnot', 'Gyi'): [(0, 1), (0, 5), (1, 3), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gyi', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Giy', 'Giz'): [(0, 1), (0, 5), (3, 7), (3, 9), (4, 2), (4, 7), (6, 7), (7, 3), (8, 3), (9, 2), (9, 10), (11, 9), (12, 0), (14, 1), (14, 3), (15, 1)], ('Gxi', 'Gcnot', 'Gcnot'): [(0, 7), (1, 1), (1, 7), (2, 7), (3, 3), (4, 9), (5, 4), (7, 2), (7, 10), (8, 2), (9, 2), (9, 8), (9, 9), (10, 1), (10, 10), (11, 2), (11, 5), (11, 6), (13, 2), (14, 7), (15, 2), (15, 3)], ('Gix', 'Gii', 'Giy'): [(1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 9), (15, 1)], ('Gix', 'Giy', 'Giy'): [(0, 4), (0, 5), (0, 7), (1, 1), (1, 6), (2, 3), (4, 10), (5, 4), (6, 8), (7, 4), (7, 10), (8, 8), (8, 9), (10, 5), (11, 5), (11, 6), (11, 9), (13, 10), (14, 1), (14, 9)], ('Giy', 'Gzi', 'Giz'): [(0, 4), (0, 6), (2, 2), (3, 1), (4, 1), (4, 3), (4, 5), (4, 7), (5, 1), (5, 3), (5, 4), (8, 5), (8, 8), (9, 4), (9, 6), (12, 1), (13, 0), (13, 2), (15, 1)], ('Gxi', 'Gxi', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gxi', 'Gzi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giz', 'Gzi', 'Gxi', 'Giz'): [(1, 10), (2, 10), (4, 8), (5, 5), (5, 6), (6, 10), (7, 0), (7, 5), (7, 6), (7, 8), (8, 5), (12, 5), (13, 0), (13, 2), (14, 1)], ('Gix', 'Gxi', 'Gcnot', 'Giy'): [(0, 1), (0, 2), (0, 5), (0, 10), (1, 3), (1, 7), (2, 1), (2, 7), (3, 6), (5, 1), (6, 10), (7, 0), (7, 6), (9, 0), (9, 2), (10, 4), (11, 7), (11, 9), (13, 7), (14, 3), (14, 7), (15, 5), (15, 10)], ('Gyi', 'Gix', 'Gxi', 'Giy'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gii', 'Gii', 'Gxi'): [(0, 0), (1, 5), (2, 4), (3, 3), (3, 5), (5, 2), (6, 1), (6, 8), (6, 10), (8, 6), (10, 2), (10, 8), (10, 10), (11, 8), (12, 1), (13, 1), (13, 4), (13, 6), (13, 10), (14, 8), (15, 3)], ('Gix', 'Giy', 'Gxi', 'Gyi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gxi', 'Gii', 'Gii'): [(1, 1), (2, 8), (3, 0), (3, 2), (3, 6), (4, 7), (7, 2), (8, 6), (9, 1), (9, 7), (9, 9), (10, 2), (10, 10), (11, 8), (12, 6), (13, 2), (13, 7), (14, 2), (15, 5)], ('Gcnot', 'Gix', 'Gxi', 'Gxi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gix', 'Gix', 'Gix'): [(0, 5), (0, 9), (1, 6), (3, 1), (3, 2), (5, 0), (5, 4), (6, 0), (6, 8), (9, 7), (10, 9), (11, 1), (11, 4), (14, 4), (14, 9), (15, 5), (15, 7)], ('Gyi', 'Gyi', 'Giy', 'Gyi'): [(0, 2), (1, 1), (1, 4), (2, 1), (2, 10), (3, 10), (4, 0), (5, 3), (5, 7), (6, 4), (6, 10), (8, 2), (8, 3), (9, 0), (10, 8), (11, 1), (11, 7), (13, 1), (13, 8)], ('Gix', 'Giy', 'Gxi', 'Gcnot'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Giy', 'Giy', 'Gii'): [(0, 4), (0, 5), (0, 7), (1, 1), (1, 6), (2, 3), (4, 10), (5, 4), (6, 8), (7, 4), (7, 10), (8, 8), (8, 9), (10, 5), (11, 5), (11, 6), (11, 9), (13, 10), (14, 1), (14, 9)], ('Gcnot', 'Gyi', 'Gcnot', 'Gxi'): [(0, 0), (1, 0), (1, 10), (4, 0), (4, 4), (5, 10), (7, 9), (8, 9), (9, 0), (9, 9), (10, 3), (10, 4), (10, 8), (11, 5), (12, 5), (12, 9), (13, 1), (13, 9), (15, 1)], ('Gxi', 'Gyi', 'Gix', 'Gix'): [(1, 10), (2, 10), (4, 8), (5, 5), (5, 6), (6, 10), (7, 0), (7, 5), (7, 6), (7, 8), (8, 5), (12, 5), (13, 0), (13, 2), (14, 1)], ('Gxi', 'Gyi', 'Gyi', 'Gyi'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gix', 'Gix', 'Giy'): [(1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 9), (15, 1)], ('Gcnot', 'Gix', 'Gcnot', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gyi', 'Gyi', 'Gii'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giz', 'Giz', 'Gyi', 'Gzi', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Giy', 'Gxi', 'Gyi', 'Gxi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Giy', 'Gyi', 'Gix', 'Gix'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gyi', 'Gxi', 'Gxi', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gzi', 'Gxi', 'Gxi', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gxi', 'Giy', 'Gyi', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gcnot', 'Giy', 'Giy', 'Gxi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gxi', 'Gix', 'Giy', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gix', 'Gxi', 'Gix', 'Gxi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Giy', 'Giy', 'Gix', 'Gxi', 'Gxi'): [(1, 1), (2, 5), (4, 3), (5, 5), (6, 3), (7, 1), (10, 2), (10, 5), (11, 2), (11, 5), (12, 7), (12, 10), (13, 0), (13, 4), (14, 5)], ('Gyi', 'Giy', 'Gxi', 'Giy', 'Giy', 'Giy'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Giy', 'Gix', 'Gyi', 'Gix', 'Gix'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Giy', 'Gxi', 'Gyi', 'Gxi', 'Gcnot'): [(0, 1), (0, 2), (0, 5), (1, 3), (1, 9), (2, 4), (2, 10), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gix', 'Giy', 'Gxi', 'Giy', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gix', 'Giy', 'Giy', 'Gxi', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gyi', 'Gyi', 'Giy', 'Gyi', 'Gix'): [(0, 3), (1, 0), (1, 4), (3, 10), (4, 3), (5, 7), (7, 2), (7, 4), (7, 7), (7, 8), (8, 1), (8, 5), (8, 7), (8, 9), (9, 2), (9, 6), (10, 3), (14, 10), (15, 4)], ('Giy', 'Giy', 'Gxi', 'Giy', 'Gix', 'Giy'): [(0, 4), (0, 6), (1, 1), (2, 2), (4, 1), (4, 3), (5, 1), (5, 3), (6, 10), (8, 2), (8, 8), (9, 4), (10, 7), (12, 1), (13, 2), (15, 6), (15, 9)], ('Gyi', 'Gxi', 'Gix', 'Giy', 'Gxi', 'Gix'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gxi', 'Gxi', 'Gyi', 'Gxi', 'Gyi', 'Gyi'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gix', 'Giy', 'Gix', 'Giy', 'Giy'): [(1, 0), (1, 10), (4, 0), (4, 4), (4, 7), (4, 8), (5, 5), (7, 6), (8, 9), (9, 9), (10, 2), (10, 8), (11, 10), (12, 6), (12, 9), (13, 9), (15, 1)], ('Gyi', 'Gxi', 'Gix', 'Gxi', 'Gix', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Giy', 'Gix', 'Gyi', 'Gyi', 'Gix', 'Gxi', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gyi', 'Gxi', 'Giy', 'Gxi', 'Gix', 'Gxi', 'Gyi', 'Giy'): [(0, 1), (0, 5), (1, 3), (3, 8), (5, 5), (7, 0), (9, 3), (9, 9), (9, 10), (10, 8), (12, 2), (12, 6), (14, 6), (15, 0), (15, 5)], ('Gix', 'Gix', 'Gyi', 'Gxi', 'Giy', 'Gxi', 'Giy', 'Gyi'): [(1, 1), (2, 5), (4, 3), (5, 5), (6, 3), (7, 1), (10, 2), (10, 5), (11, 2), (11, 5), (12, 7), (12, 10), (13, 0), (13, 4), (14, 5)]}
    global_fidPairs_lite = None
    pergerm_fidPairsDict_lite = None

    @property
    def _target_model(self):
        return _setc.build_explicit_model([(0, 1)], [(), ('Gx', 1), ('Gy', 1), ('Gz', 1), ('Gx', 0), ('Gy', 0), ('Gz', 0), ('Gcnot', 0, 1)], ['I(0):I(1)', 'I(0):X(pi/2,1)', 'I(0):Y(pi/2,1)', 'I(0):Z(pi/2,1)', 'X(pi/2,0):I(1)', 'Y(pi/2,0):I(1)', 'Z(pi/2,0):I(1)', 'CNOT(0,1)'], effectLabels=['00', '01', '10', '11'], effectExpressions=['0', '1', '2', '3'])


import sys
sys.modules[__name__] = _Module()

