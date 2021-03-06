""" RB circuit sampling functions """
#***************************************************************************************************
# Copyright 2015, 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 or in the LICENSE file in the root pyGSTi directory.
#***************************************************************************************************

from . import compilers as _cmpl
from ..objects import circuit as _cir
from ..objects import label as _lbl
from ..tools import symplectic as _symp
from .. import construction as _cnst
from .. import objects as _objs
from .. import io as _io
from .. import tools as _tools
from ..tools import group as _rbobjs

import numpy as _np
import copy as _copy
import itertools as _itertools


def find_all_sets_of_compatible_twoQgates(edgelist, n, gatename='Gcnot', aslabel=False):
    """
    todo.

    n : int . the number of two-qubit gates to have in the set.

    """
    co2Qgates = []

    # Go for all combinations of n two-qubit gates from the edgelist.
    for npairs in _itertools.combinations(edgelist, n):

        # Make a list of the qubits involved in the gates
        flat_list = [item for sublist in npairs for item in sublist]

        # If no qubit is involved in more than one gate we accept the combination
        if len(flat_list) == len(set(flat_list)):
            if aslabel:
                co2Qgates.append([_lbl.Label(gatename, pair) for pair in npairs])
            else:
                co2Qgates.append([gatename + ':' + pair[0] + ':' + pair[1] for pair in npairs])

    return co2Qgates


def circuit_layer_by_pairing_qubits(pspec, qubit_labels=None, twoQprob=0.5, oneQgatenames='all',
                                    twoQgatenames='all', modelname='clifford'):
    """
    Samples a random circuit layer by pairing up qubits and picking a two-qubit gate for a pair
    with the specificed probability. This sampler *assumes* all-to-all connectivity, and does
    not check that this condition is satisfied (more generally, it assumes that all gates can be
    applied in parallel in any combination that would be well-defined).

    The sampler works as follows: If there are an odd number of qubits, one qubit is chosen at
    random to have a uniformly random 1-qubit gate applied to it (from all possible 1-qubit gates,
    or those in `oneQgatenames` if not None). Then, the remaining qubits are paired up, uniformly
    at random. A uniformly random 2-qubit gate is then chosen for a pair with probability `twoQprob`
    (from all possible 2-qubit gates, or those in `twoQgatenames` if not None). If a 2-qubit gate
    is not chosen to act on a pair, then each qubit is independently and uniformly randomly assigned
    a 1-qubit gate.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit layer is being sampled for. This
       function assumes all-to-all connectivity, but does not check this is satisfied. Unless
       `qubit_labels` is not None, a circuit layer is sampled over all the qubits in `pspec`.

    qubit_labels : list, optional
        If not None, a list of the qubits to sample the circuit layer for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit layer is sampled to acton all the qubits
        in `pspec`.

    twoQprob : float, optional
        A probability for a two-qubit gate to be applied to a pair of qubits. So, the expected
        number of 2-qubit gates in the sampled layer is twoQprob*floor(n/2).

    oneQgatenames : 'all' or list, optional
        If not 'all', a list of the names of the 1-qubit gates to be sampled from when applying
        a 1-qubit gate to a qubit. If this is 'all', the full set of 1-qubit gate names is extracted
        from the ProcessorSpec.

    twoQgatenames : 'all' or list, optional
        If not 'all', a list of the names of the 2-qubit gates to be sampled from when applying
        a 2-qubit gate to a pair of qubits. If this is 'all', the full set of 2-qubit gate names is
        extracted from the ProcessorSpec.

    modelname : str, optional
        Only used if oneQgatenames or twoQgatenames is None. Specifies which of the
        `pspec.models` to use to extract the gate-set. The `clifford` default is suitable
        for Clifford or direct RB, but will not use any non-Clifford gates in the gate-set.

    Returns
    -------
    list of Labels
        A list of gate Labels that defines a "complete" circuit layer (there is one and only
        one gate acting on each qubit in `pspec` or `qubit_labels`).
    """
    if qubit_labels is None: n = pspec.number_of_qubits
    else:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
        n = len(qubit_labels)

    # If the one qubit and/or two qubit gate names are only specified as 'all', construct them.
    if (oneQgatenames == 'all') or (twoQgatenames == 'all'):
        if oneQgatenames == 'all':
            oneQpopulate = True
            oneQgatenames = []
        else:
            oneQpopulate = False
        if twoQgatenames == 'all':
            twoQpopulate = True
            twoQgatenames = []
        else:
            twoQpopulate = False

        operationlist = pspec.models[modelname].get_primitive_op_labels()
        for gate in operationlist:
            if oneQpopulate:
                if (gate.number_of_qubits == 1) and (gate.name not in oneQgatenames):
                    oneQgatenames.append(gate.name)
            if twoQpopulate:
                if (gate.number_of_qubits == 2) and (gate.name not in twoQgatenames):
                    twoQgatenames.append(gate.name)

    # Basic variables required for sampling the circuit layer.
    if qubit_labels is None:
        qubits = list(pspec.qubit_labels[:])  # copy this list
    else:
        qubits = list(qubit_labels[:])  # copy this list
    sampled_layer = []
    num_oneQgatenames = len(oneQgatenames)
    num_twoQgatenames = len(twoQgatenames)

    # If there is an odd number of qubits, begin by picking one to have a 1-qubit gate.
    if n % 2 != 0:
        q = qubits[_np.random.randint(0, n)]
        name = oneQgatenames[_np.random.randint(0, num_oneQgatenames)]
        del qubits[q]  # XXX is this correct?
        sampled_layer.append(_lbl.Label(name, q))

    # Go through n//2 times until all qubits have been paired up and gates on them sampled
    for i in range(n // 2):

        # Pick two of the remaining qubits : each qubit that is picked is deleted from the list.
        index = _np.random.randint(0, len(qubits))
        q1 = qubits[index]
        del qubits[index]
        index = _np.random.randint(0, len(qubits))
        q2 = qubits[index]
        del qubits[index]

        # Flip a coin to decide whether to act a two-qubit gate on that qubit
        if _np.random.binomial(1, twoQprob) == 1:
            # If there is more than one two-qubit gate on the pair, pick a uniformly random one.
            name = twoQgatenames[_np.random.randint(0, num_twoQgatenames)]
            sampled_layer.append(_lbl.Label(name, (q1, q2)))
        else:
            # Independently, pick uniformly random 1-qubit gates to apply to each qubit.
            name1 = oneQgatenames[_np.random.randint(0, num_oneQgatenames)]
            name2 = oneQgatenames[_np.random.randint(0, num_oneQgatenames)]
            sampled_layer.append(_lbl.Label(name1, q1))
            sampled_layer.append(_lbl.Label(name2, q2))

    return sampled_layer


def circuit_layer_by_edgegrab(pspec, qubit_labels=None, meantwoQgates=1, modelname='clifford'):
    """
    todo

    """
    assert(modelname == 'clifford'), "This function currently assumes sampling from a Clifford model!"
    if qubit_labels is None:
        qubits = list(pspec.qubit_labels[:])  # copy this list
    else:
        assert(isinstance(qubit_labels, (list, tuple))), "SubsetQs must be a list or a tuple!"
        qubits = list(qubit_labels[:])  # copy this list

    # Prep the sampling variables.
    sampled_layer = []
    edgelist = pspec.qubitgraph.edges()
    edgelist = [e for e in edgelist if all([q in qubits for q in e])]
    selectededges = []

    # Go through until all qubits have been assigned a gate.
    while len(edgelist) > 0:

        edge = edgelist[_np.random.randint(0, len(edgelist))]
        selectededges.append(edge)
        # Delete all edges containing these qubits.
        edgelist = [e for e in edgelist if not any([q in e for q in edge])]

    num2Qgates = len(selectededges)
    assert(num2Qgates >= meantwoQgates), "Device has insufficient connectivity!"

    if meantwoQgates > 0:
        twoQprob = meantwoQgates / num2Qgates
    else:
        twoQprob = 0

    unusedqubits = _copy.copy(qubits)
    for edge in selectededges:
        if bool(_np.random.binomial(1, twoQprob)):

            # The two-qubit gates on that edge.
            possibleops = pspec.clifford_ops_on_qubits[edge]
            #assert(len(possibleops) == 1), "Sampler assumes a single 2-qubit gate!"
            sampled_layer.append(possibleops[_np.random.randint(0, len(possibleops))])
            for q in edge:
                del unusedqubits[unusedqubits.index(q)]

    for q in unusedqubits:
        possibleops = pspec.clifford_ops_on_qubits[(q,)]
        gate = possibleops[_np.random.randint(0, len(possibleops))]
        sampled_layer.append(gate)

    return sampled_layer


def circuit_layer_by_Qelimination(pspec, qubit_labels=None, twoQprob=0.5, oneQgates='all',
                                  twoQgates='all', modelname='clifford'):
    """
    Samples a random circuit layer by eliminating qubits one by one. This sampler works
    with any connectivity, but the expected number of 2-qubit gates in a layer depends
    on both the specified 2-qubit gate probability and the exact connectivity graph.

    This sampler is the following algorithm: List all the qubits, and repeat the
    following steps until all qubits are deleted from this list. 1) Uniformly at random
    pick a qubit from the list, and delete it from the list 2) Flip a coin with  bias
    `twoQprob` to be "Heads". 3) If "Heads" then -- if there is one or more 2-qubit gates
    from this qubit to other qubits still in the list -- pick one of these at random.
    4) If we haven't chosen a 2-qubit gate for this qubit ("Tails" or "Heads" but there
    are no possible 2-qubit gates) then pick a uniformly random 1-qubit gate to apply to
    this qubit.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit layer is being sampled for. Unless
       `qubit_labels` is not None, a circuit layer is sampled over all the qubits in `pspec`.

    qubit_labels : list, optional
        If not None, a list of the qubits to sample the circuit layer for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit layer is sampled to acton all the qubits
        in `pspec`.

    twoQprob : float or None, optional
        None or a probability for a two-qubit gate to be applied to a pair of qubits. If
        None, sampling is uniform over all gates available on a qubit. If a float, if a
        2-qubit can is still possible on a qubit at that stage of the sampling, this is
        the probability a 2-qubit gate is chosen for that qubit. The expected number of
        2-qubit gates per layer depend on this quantity and the connectivity graph of
        the device.

    oneQgates : 'all' or list, optional
        If not 'all', a list of the 1-qubit gates to sample from, in the form of Label
        objects. This is *not* just gate names (e.g. "Gh"), but Labels each containing
        the gate name and the qubit it acts on. So it is possible to specify different
        1-qubit models on different qubits. If this is 'all', the full set of possible
        1-qubit gates is extracted from the ProcessorSpec.

    twoQgates : 'all' or list, optional
        If not 'all', a list of the 2-qubit gates to sample from, in the form of Label
        objects. This is *not* just gate names (e.g. "Gcnot"), but Labels each containing
        the gate name and the qubits it acts on. If this is 'all', the full set of possible
        2-qubit gates is extracted from the ProcessorSpec.

    modelname : str, optional
        Only used if oneQgatenames or twoQgatenames is None. Specifies the which of the
        `pspec.models` to use to extract the model. The `clifford` default is suitable
        for Clifford or direct RB, but will not use any non-Clifford gates in the model.

    Returns
    -------
    list of gates
        A list of gate Labels that defines a "complete" circuit layer (there is one and
        only one gate acting on each qubit in `pspec` or `qubit_labels`).
    """
    if qubit_labels is None:
        n = pspec.number_of_qubits
        qubits = list(pspec.qubit_labels[:])  # copy this list
    else:
        assert(isinstance(qubit_labels, (list, tuple))), "SubsetQs must be a list or a tuple!"
        n = len(qubit_labels)
        qubits = list(qubit_labels[:])  # copy this list

    # If oneQgates is specified, use the given list.
    if oneQgates != 'all':
        oneQgates_available = _copy.copy(oneQgates)
    # If oneQgates is not specified, extract this list from the ProcessorSpec
    else:
        oneQgates_available = list(pspec.models[modelname].get_primitive_op_labels())
        d = len(oneQgates_available)
        for i in range(0, d):
            # If it's not a 1-qubit gate, we delete it.
            if oneQgates_available[d - 1 - i].number_of_qubits != 1:
                del oneQgates_available[d - 1 - i]
            # If it's not a gate on the allowed qubits, we delete it.
            elif oneQgates_available[d - 1 - i].qubits[0] not in qubits:
                del oneQgates_available[d - 1 - i]

    # If twoQgates is specified, use the given list.
    if twoQgates != 'all':
        twoQgates_available = _copy.copy(twoQgates)
    # If twoQgates is not specified, extract this list from the ProcessorSpec
    else:
        twoQgates_available = list(pspec.models[modelname].get_primitive_op_labels())
        d = len(twoQgates_available)
        for i in range(0, d):
            # If it's not a 2-qubit gate, we delete it.
            if twoQgates_available[d - 1 - i].number_of_qubits != 2:
                del twoQgates_available[d - 1 - i]
            # If it's not a gate on the allowed qubits, we delete it.
            elif not set(twoQgates_available[d - 1 - i].qubits).issubset(set(qubits)):
                del twoQgates_available[d - 1 - i]

    # If the `twoQprob` is not None, we specify a weighting towards 2-qubit gates
    if twoQprob is not None:
        weighting = [1 - twoQprob, twoQprob]

    # Prep the sampling variables.
    sampled_layer = []
    remaining_qubits = _copy.deepcopy(qubits)
    num_qubits_used = 0

    # Go through until all qubits have been assigned a gate.
    while num_qubits_used < n:

        # Pick a random qubit
        r = _np.random.randint(0, n - num_qubits_used)
        q = remaining_qubits[r]
        del remaining_qubits[r]

        # Find the 1Q gates that act on q.
        oneQgates_remaining_on_q = []
        ll = len(oneQgates_available)
        for i in range(0, ll):
            if q in oneQgates_available[ll - 1 - i].qubits:
                oneQgates_remaining_on_q.append(oneQgates_available[ll - 1 - i])
                del oneQgates_available[ll - 1 - i]

        # Find the 2Q gates that act on q and a remaining qubit.
        twoQgates_remaining_on_q = []
        ll = len(twoQgates_available)
        for i in range(0, ll):
            if q in twoQgates_available[ll - 1 - i].qubits:
                twoQgates_remaining_on_q.append(twoQgates_available[ll - 1 - i])
                del twoQgates_available[ll - 1 - i]

        # If twoQprob is None, there is no weighting towards 2-qubit gates.
        if twoQprob is None:
            nrm = len(oneQgates_remaining_on_q) + len(twoQgates_remaining_on_q)
            weighting = [len(oneQgates_remaining_on_q) / nrm, len(twoQgates_remaining_on_q) / nrm]

        # Decide whether to to implement a 2-qubit gate or a 1-qubit gate.
        if len(twoQgates_remaining_on_q) == 0:
            xx = 1
        else:
            xx = _np.random.choice([1, 2], p=weighting)

        # Implement a 1-qubit gate on qubit q.
        if xx == 1:
            # Sample the gate
            r = _np.random.randint(0, len(oneQgates_remaining_on_q))
            sampled_layer.append(oneQgates_remaining_on_q[r])
            # We have assigned gates to 1 of the remaining qubits.
            num_qubits_used += 1

        # Implement a 2-qubit gate on qubit q.
        if xx == 2:
            # Sample the gate
            r = _np.random.randint(0, len(twoQgates_remaining_on_q))
            sampled_layer.append(twoQgates_remaining_on_q[r])

            # Find the label of the other qubit in the sampled gate.
            other_qubit = twoQgates_remaining_on_q[r].qubits[0]
            if other_qubit == q:
                other_qubit = twoQgates_remaining_on_q[r].qubits[1]

            # Delete the gates on this other qubit from the 1-qubit gate list.
            ll = len(oneQgates_available)
            for i in range(0, ll):
                if other_qubit in oneQgates_available[ll - 1 - i].qubits:
                    del oneQgates_available[ll - 1 - i]

            # Delete the gates on this other qubit from the 2-qubit gate list.
            ll = len(twoQgates_available)
            for i in range(0, ll):
                if other_qubit in twoQgates_available[ll - 1 - i].qubits:
                    del twoQgates_available[ll - 1 - i]

            # Delete this other qubit from remaining qubits list.
            del remaining_qubits[remaining_qubits.index(other_qubit)]

            # We have assigned gates to 2 of the remaining qubits.
            num_qubits_used += 2

    return sampled_layer


def circuit_layer_by_co2Qgates(pspec, qubit_labels, co2Qgates, co2Qgatesprob='uniform', twoQprob=1.0,
                               oneQgatenames='all', modelname='clifford'):
    """
    Samples a random circuit layer using the specified list of "compatible two-qubit gates"
    (co2Qgates). That is, the user inputs a list (`co2Qgates`) specifying 2-qubit gates that are
    "compatible" -- meaning that they can be implemented simulatenously -- and a distribution
    over the different compatible sets, and a layer is sampled from this via:

    1. Pick a set of compatible two-qubit gates from the list `co2Qgates`, according to the
    distribution specified by `co2Qgatesprob`.
    2. For each 2-qubit gate in the chosen set of compatible gates, with probability `twoQprob`
    add this gate to the layer.
    3. Uniformly sample 1-qubit gates for any qubits that don't yet have a gate on them,
    from those 1-qubit gates specified by `oneQgatenames`.

    For example, consider 4 qubits with linear connectivity. a valid `co2Qgates` list is
    co2Qgates = [[,],[Label(Gcphase,(0,1)),Label(Gcphase,(2,3))]] which consists of an
    element containing zero 2-qubit gates and an element containing  two 2-qubit gates
    that can be applied in parallel. In this example there are 5 possible sets of compatible
    2-qubit gates:

    1. [,] (zero 2-qubit gates)
    2. [Label(Gcphase,(0,1)),] (one of the three 2-qubit gate)
    3. [Label(Gcphase,(1,2)),] (one of the three 2-qubit gate)
    4. [Label(Gcphase,(2,3)),] (one of the three 2-qubit gate)
    5. [Label(Gcphase,(0,1)), Label(Gcphase,(2,3)),] (the only compatible pair of 2-qubit gates).

    The list of compatible two-qubit gates `co2Qgates` can be any list containing anywhere
    from 1 to all 5 of these lists.

    In order to allow for convenient sampling of some commonly useful distributions,
    `co2Qgates` can be a list of lists of lists of compatible 2-qubit gates ("nested" sampling).
    In this case, a list of lists of compatible 2-qubit gates is picked according to the distribution
    `co2Qgatesprob`, and then one of the sublists of compatible 2-qubit gates in the selected list is
    then chosen uniformly at random. For example, this is useful for sampling a layer containing one
    uniformly random 2-qubit gate with probability p and a layer of 1-qubit gates with probability
    1-p. Here, we can specify `co2Qgates` as [[],[[the 1st 2Q-gate,],[the 2nd 2Q-gate,], ...]] and
    set `twoQprob=1` and `co2Qgatesprob  = [1-p,p].

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit layer is being sampled for. Unless
       `qubit_labels` is not None, a circuit layer is sampled over all the qubits in `pspec`.

    qubit_labels : list
        If not None, a list of the qubits to sample the circuit layer for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit layer is sampled to act on all the qubits
        in `pspec`.

    co2Qgates : list
        This is either:

            1. A list of lists of 2-qubit gate Labels that can be applied in parallel.
            2. A list of lists of lists of 2-qubit gate Labels that can be applied in parallel.

        In case (1) each list in `co2Qgates` should contain 2-qubit gates, in the form of Labels,
        that can be applied in parallel and act only on the qubits in `pspec` if `qubit_labels` is None,
        or act only on the qubits in  `qubit_labels` if `qubit_labels` is not None.  The sampler then picks
        one of these compatible sets of gates (with probability specified by `co2Qgatesprob`, and converts
        this into a circuit layer by applying the 2-qubit gates it contains with the user-specified
        probability `twoQprob`, and augmenting these 2-qubit gates with 1-qubit gates on all other qubits.

        In case (2) a sublist of lists is sampled from `co2Qgates` according to `co2Qgatesprob` and then we
        proceed as in case (1) but as though `co2Qgatesprob` is the uniform distribution.

    co2Qgatesprob : str or list of floats
        If a list, they are unnormalized probabilities to sample each of the elements of `co2Qgates`. So it
        is a list of non-negative floats of the same length as `co2Qgates`. If 'uniform', then the uniform
        distribution is used.

    twoQprob : float, optional
        The probability for each two-qubit gate to be applied to a pair of qubits, after a
        set of compatible 2-qubit gates has been chosen. The expected number of 2-qubit
        gates in a layer is `twoQprob` times the expected number of 2-qubit gates in a
        set of compatible 2-qubit gates sampled according to `co2Qgatesprob`.

    oneQgatenames : 'all' or list of strs, optional
        If not 'all', a list of the names of the 1-qubit gates to be sampled from when applying
        a 1-qubit gate to a qubit. If this is 'all', the full set of 1-qubit gate names is
        extracted from the ProcessorSpec.

    modelname : str, optional
        Only used if oneQgatenames is 'all'. Specifies which of the `pspec.models` to use to
        extract the model. The `clifford` default is suitable for Clifford or direct RB,
        but will not use any non-Clifford gates in the model.

    Returns
    -------
    list of gates
        A list of gate Labels that defines a "complete" circuit layer (there is one and
        only one gate acting on each qubit).
    """
    assert(modelname == 'clifford'), "This function currently assumes sampling from a Clifford model!"
    # Pick the sector.
    if isinstance(co2Qgatesprob, str):
        assert(co2Qgatesprob == 'uniform'), "If `co2Qgatesprob` is a string it must be 'uniform!'"
        twoqubitgates_or_nestedco2Qgates = co2Qgates[_np.random.randint(0, len(co2Qgates))]
    else:
        co2Qgatesprob = _np.array(co2Qgatesprob) / _np.sum(co2Qgatesprob)
        x = list(_np.random.multinomial(1, co2Qgatesprob))
        twoqubitgates_or_nestedco2Qgates = co2Qgates[x.index(1)]

    # The special case where the selected co2Qgates contains no gates or co2Qgates.
    if len(twoqubitgates_or_nestedco2Qgates) == 0:
        twoqubitgates = twoqubitgates_or_nestedco2Qgates
    # If it's a nested sector, sample uniformly from the nested co2Qgates.
    elif type(twoqubitgates_or_nestedco2Qgates[0]) == list:
        twoqubitgates = twoqubitgates_or_nestedco2Qgates[_np.random.randint(0, len(twoqubitgates_or_nestedco2Qgates))]
    # If it's not a list of "co2Qgates" (lists) then this is the list of gates to use.
    else:
        twoqubitgates = twoqubitgates_or_nestedco2Qgates

    # Prep the sampling variables
    sampled_layer = []
    if qubit_labels is not None:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
        remaining_qubits = list(qubit_labels[:])  # copy this list
    else:
        remaining_qubits = pspec.qubit_labels[:]  # copy this list

    # Go through the 2-qubit gates in the sector, and apply each one with probability twoQprob
    for i in range(0, len(twoqubitgates)):
        if _np.random.binomial(1, twoQprob) == 1:
            gate = twoqubitgates[i]
            # If it's a nested co2Qgates:
            sampled_layer.append(gate)
            # Delete the qubits that have been assigned a gate.
            del remaining_qubits[remaining_qubits.index(gate.qubits[0])]
            del remaining_qubits[remaining_qubits.index(gate.qubits[1])]

    # Go through the qubits which don't have a 2-qubit gate assigned to them, and pick a 1-qubit gate
    for i in range(0, len(remaining_qubits)):

        qubit = remaining_qubits[i]

        # If the 1-qubit gate names are specified, use these.
        if oneQgatenames != 'all':
            possibleops = [_lbl.Label(name, (qubit,)) for name in oneQgatenames]

        # If the 1-qubit gate names are not specified, find the available 1-qubit gates
        else:
            if modelname == 'clifford':
                possibleops = pspec.clifford_ops_on_qubits[(qubit,)]
            else:
                possibleops = pspec.models[modelname].get_primitive_op_labels()
                l = len(possibleops)
                for j in range(0, l):
                    if possibleops[l - j].number_of_qubits != 1:
                        del possibleops[l - j]
                    else:
                        if possibleops[l - j].qubits[0] != qubit:
                            del possibleops[l - j]

        gate = possibleops[_np.random.randint(0, len(possibleops))]
        sampled_layer.append(gate)

    return sampled_layer


def circuit_layer_of_oneQgates(pspec, qubit_labels=None, oneQgatenames='all', pdist='uniform',
                               modelname='clifford'):
    """
    Samples a random circuit layer containing only 1-qubit gates. The allowed
    1-qubit gates are specified by `oneQgatenames`, and the 1-qubit gates are
    sampled independently and uniformly.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit layer is being sampled for. Unless
       `qubit_labels` is not None, a circuit layer is sampled over all the qubits in `pspec`.

    qubit_labels : list, optional
        If not None, a list of the qubits to sample the circuit layer for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit layer is sampled to acton all the qubits
        in `pspec`.

    oneQgatenames : 'all' or list of strs, optional
        If not 'all', a list of the names of the 1-qubit gates to be sampled from when applying
        a 1-qubit gate to a qubit. If this is 'all', the full set of 1-qubit gate names is
        extracted from the ProcessorSpec.

    pdist : 'uniform' or list of floats, optional
        If a list, they are unnormalized probabilities to sample each of the 1-qubit gates
        in the list `oneQgatenames`. If this is not 'uniform', then oneQgatename` must not
        be 'all' (it must be a list so that it is unambigious which probability correpsonds
        to which gate). So if not 'uniform', `pdist` is a list of non-negative floats of the
        same length as `oneQgatenames`. If 'uniform', then the uniform distribution over
        the gates is used.

    modelname : str, optional
        Only used if oneQgatenames is 'all'. Specifies which of the `pspec.models` to use to
        extract the model. The `clifford` default is suitable for Clifford or direct RB,
        but will not use any non-Clifford gates in the model.

    Returns
    -------
    list of gates
        A list of gate Labels that defines a "complete" circuit layer (there is one and
        only one gate acting on each qubit).
    """
    if qubit_labels is not None:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
        qubits = list(qubit_labels[:])  # copy this list
    else:
        qubits = list(pspec.qubit_labels[:])  # copy this list

    sampled_layer = []

    if isinstance(pdist, str): assert(pdist == 'uniform'), "If pdist is not a list or numpy.array it must be 'uniform'"

    if oneQgatenames == 'all':
        assert(pdist == 'uniform'), "If `oneQgatenames` = 'all', pdist must be 'uniform'"
        if modelname == 'clifford':
            for i in qubits:
                try:
                    gate = pspec.clifford_ops_on_qubits[(i,)][_np.random.randint(
                        0, len(pspec.clifford_ops_on_qubits[(i,)]))]
                    sampled_layer.append(gate)
                except:
                    raise ValueError("There are no 1Q Clifford gates on qubit {}!".format(i))
        else: raise ValueError("Currently, 'modelname' must be 'clifford'")

    else:
        # A basic check for the validity of pdist.
        if not isinstance(pdist, str):
            assert(len(pdist) == len(oneQgatenames)), "The pdist probability distribution is invalid!"

        # Find out how many 1-qubit gate names there are
        num_oneQgatenames = len(oneQgatenames)

        # Sample a gate for each qubit.
        for i in qubits:

            # If 'uniform', then sample according to the uniform dist.
            if isinstance(pdist, str): sampled_gatename = oneQgatenames[_np.random.randint(0, num_oneQgatenames)]
            # If not 'uniform', then sample according to the user-specified dist.
            else:
                pdist = _np.array(pdist) / sum(pdist)
                x = list(_np.random.multinomial(1, pdist))
                sampled_gatename = oneQgatenames[x.index(1)]
            # Add sampled gate to the layer.
            sampled_layer.append(_lbl.Label(sampled_gatename, i))

    return sampled_layer


def random_circuit(pspec, length, qubit_labels=None, sampler='Qelimination', samplerargs=[], addlocal=False, lsargs=[]):
    """
    Samples a random circuit of the specified length (or ~ twice this length), using layers
    independently sampled according to the specified sampling distribution.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for. This is always
       handed to the sampler, as the first argument of the sampler function. Unless
       `qubit_labels` is not None, the circuit is sampled over all the qubits in `pspec`.

    length : int
        If `addlocal` is False, this is the length of the sampled circuit. If `addlocal is
        True the length of the circuits is 2*length+1 with odd-indexed layers sampled according
        to the sampler specified by `sampler`, and the the zeroth layer + the even-indexed
        layers consisting of random 1-qubit gates (with the sampling specified by `lsargs`)

    qubit_labels : list, optional
        If not None, a list of the qubits to sample the circuit for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit is sampled to act on all the qubits
        in `pspec`.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates. If this is a
        function, it should be a function that takes as the first argument a ProcessorSpec, and
        returns a random circuit layer as a list of gate Label objects. Note that the default
        'Qelimination' is not necessarily the most useful in-built sampler, but it is the only
        sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec` and `samplerargs` lists the
        remaining arguments handed to the sampler. For some in-built samplers this is not
        optional.

    addlocal : bool, optional
        If False, the circuit sampled is of length `length` and each layer is independently
        sampled according to the sampler specified by `sampler`. If True, the circuit sampled
        is of length 2*`length`+1 where: the zeroth + all even layers are consisting of
        independently random 1-qubit gates (with the sampling specified by `lsargs`); the
        odd-indexed layers are independently sampled according to `sampler`. So `length`+1
        layers consist only of 1-qubit gates, and `length` layers are sampled according to
        `sampler`.

    lsargs : list, optional
        A list of arguments that are handed to the 1-qubit gate layers sampler
        rb.sampler.circuit_layer_of_oneQgates for the alternating 1-qubit-only layers that are
        included in the circuit if `addlocal` is True. This argument is not used if `addlocal`
        is false. Note that `pspec` is used as the first, and only required, argument of
        rb.sampler.circuit_layer_of_oneQgates. If `lsargs` = [] then all available 1-qubit gates
        are uniformly sampled from. To uniformly sample from only a subset of the available
        1-qubit gates (e.g., the Paulis to Pauli-frame-randomize) then `lsargs` should be a
        1-element list consisting of a list of the relevant gate names (e.g., `lsargs` = ['Gi,
        'Gxpi, 'Gypi', 'Gzpi']).

    Returns
    -------
    Circuit
        A random circuit of length `length` (if not addlocal) or length 2*`length`+1 (if addlocal)
        with layers independently sampled using the specified sampling distribution.
    """
    if isinstance(sampler, str):

        if sampler == 'pairingQs': sampler = circuit_layer_by_pairing_qubits
        elif sampler == 'Qelimination': sampler = circuit_layer_by_Qelimination
        elif sampler == 'co2Qgates':
            sampler = circuit_layer_by_co2Qgates
            assert(len(samplerargs) >= 1), \
                ("The samplerargs must at least a 1-element list with the first element "
                 "the 'co2Qgates' argument of the co2Qgates sampler.")
        elif sampler == 'edgegrab':
            sampler = circuit_layer_by_edgegrab
            assert(len(samplerargs) >= 1), \
                ("The samplerargs must at least a 1-element list")
        elif sampler == 'local': sampler = circuit_layer_of_oneQgates
        else: raise ValueError("Sampler type not understood!")

    if qubit_labels is not None:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
        qubits = list(qubit_labels[:])  # copy this list
    else:
        qubits = list(pspec.qubit_labels[:])  # copy this list

    # Initialize an empty circuit, to populate with sampled layers.
    circuit = _cir.Circuit(layer_labels=[], line_labels=qubits, editable=True)

    # If we are not add layers of random local gates between the layers, sample 'length' layers
    # according to the sampler `sampler`.
    if not addlocal:
        for i in range(0, length):
            layer = sampler(pspec, qubit_labels, *samplerargs)
            circuit.insert_layer(layer, 0)

    # If we are adding layers of random local gates between the layers.
    if addlocal:
        for i in range(0, 2 * length + 1):
            local = not bool(i % 2)
            # For odd layers, we uniformly sample the specified type of local gates.
            if local:
                layer = circuit_layer_of_oneQgates(pspec, qubit_labels, *lsargs)
            # For even layers, we sample according to the given distribution
            else:
                layer = sampler(pspec, qubit_labels, *samplerargs)
            circuit.insert_layer(layer, 0)

    circuit.done_editing()
    return circuit


def simultaneous_random_circuit(pspec, length, structure='1Q', sampler='Qelimination', samplerargs=[], addlocal=False,
                                lsargs=[]):
    """
    Generates a random circuit of the specified length.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler).

    length : int
        The length of the circuit. Todo: update for varying length in different subsets.

    structure : str or tuple, optional
        todo.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates.
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is
        the only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    addlocal : bool, optional
        Whether to follow each layer in the circuit, sampled according to `sampler` with
        a layer of 1-qubit gates. If this is True then the length of the circuit is double
        the requested length.

    lsargs : list, optional
        Only used if addlocal is True. A list of optional arguments handed to the 1Q gate
        layer sampler circuit_layer_by_oneQgate(). Specifies how to sample 1Q-gate layers.


    Returns
    -------
    Circuit
        A random circuit sampled as specified.

    Tuple
        A length-n tuple of floats in [0,1], corresponding to the error-free *marginalized* probabilities
        for the "1" outcome of a computational basis measurement at the end of this circuit, with the standard
        input state (with the outcomes ordered to be the same as the wires in the circuit).
    """
    if isinstance(structure, str):
        assert(structure == '1Q'), "The only default `structure` option is the string '1Q'"
        structure = tuple([(q,) for q in pspec.qubit_labels])
        n = pspec.number_of_qubits
    else:
        assert(isinstance(structure, list) or isinstance(structure, tuple)
               ), "If not a string, `structure` must be a list or tuple."
        qubits_used = []
        for qubit_labels in structure:
            assert(isinstance(qubit_labels, list) or isinstance(
                qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
            qubits_used = qubits_used + list(qubit_labels)
            assert(len(set(qubits_used)) == len(qubits_used)
                   ), "The qubits in the tuples/lists of `structure must all be unique!"

        assert(set(qubits_used).issubset(set(pspec.qubit_labels))
               ), "The qubits to benchmark must all be in the ProcessorSpec `pspec`!"
        n = len(qubits_used)

    # Creates a empty circuit over no wires
    circuit = _cir.Circuit(num_lines=0, editable=True)

    s_rc_dict = {}
    p_rc_dict = {}
    circuit_dict = {}

    if isinstance(length, int):
        length_per_subset = [length for i in range(len(structure))]
    else:
        length_per_subset = length
        assert(len(length) == len(structure)), "If `length` is a list it must be the same length as `structure`"

    for ssQs_ind, qubit_labels in enumerate(structure):
        qubit_labels = tuple(qubit_labels)
        # Sample a random circuit of "native gates" over this set of qubits, with the
        # specified sampling.
        subset_circuit = random_circuit(pspec=pspec, length=length_per_subset[ssQs_ind], qubit_labels=qubit_labels,
                                        sampler=sampler, samplerargs=samplerargs, addlocal=addlocal, lsargs=lsargs)
        circuit_dict[qubit_labels] = subset_circuit
        # find the symplectic matrix / phase vector this circuit implements.
        s_rc_dict[qubit_labels], p_rc_dict[qubit_labels] = _symp.symplectic_rep_of_clifford_circuit(
            subset_circuit, pspec=pspec)
        # Tensors this circuit with the current circuit
        circuit.tensor_circuit(subset_circuit)

    circuit.done_editing()

    # Find the expected outcome of the circuit.
    s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(circuit, pspec=pspec)
    s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
    s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
    idealout = []
    for qubit_labels in structure:
        subset_idealout = []
        for q in qubit_labels:
            qind = circuit.line_labels.index(q)
            measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, qind)
            subset_idealout.append(measurement_out[1])
        idealout.append(tuple(subset_idealout))
    idealout = tuple(idealout)

    return circuit, idealout


def _get_setting(l, circuitindex, substructure, depths, circuits_per_length, structure):

    lind = depths.index(l)
    settingDict = {}

    for s in structure:
        if s in substructure:
            settingDict[s] = len(depths) + lind * circuits_per_length + circuitindex
        else:
            settingDict[s] = lind

    return settingDict


def simultaneous_random_circuits_experiment(pspec, depths, circuits_per_length, structure='1Q', sampler='Qelimination',
                                            samplerargs=[], addlocal=False, lsargs=[], set_isolated=True,
                                            setcomplement_isolated=False,
                                            descriptor='A set of simultaneous random circuits', verbosity=1):
    """
    Generates a set of simultaneous random circuits of the specified depths.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler).

    depths : int
        Todo : update (needs to include list option)
        The set of depths for the circuits.

    circuits_per_length : int
        The number of (possibly) different circuits sampled at each length.

    structure : str or tuple.
        Defines the "structure" of the simultaneous circuit. TODO : more details.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates.
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is the
        only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    addlocal : bool, optional
        Whether to follow each layer in the "core" circuits, sampled according to `sampler` with
        a layer of 1-qubit gates.

    lsargs : list, optional
        Only used if addlocal is True. A list of optional arguments handed to the 1Q gate
        layer sampler circuit_layer_by_oneQgate(). Specifies how to sample 1Q-gate layers.

    set_isolated : bool, optional
        Todo

    setcomplement_isolated : bool, optional
        Todo

    descriptor : str, optional
        A description of the experiment being generated. Stored in the output dictionary.

    verbosity : int, optional
        If > 0 the number of circuits generated so far is shown.

    Returns
    -------
    dict
        A dictionary containing the generated random circuits, the error-free outputs of the circuit,
        and the specification used to generate the circuits. The keys are:

        - 'circuits'. A dictionary of the sampled circuits. The circuit with key(l,k) is the kth circuit
        at length l.

        - 'probs'. A dictionary of the error-free *marginalized* probabilities for the "1" outcome of
        a computational basis measurement at the end of each circuit, with the standard input state.
        The ith element of this tuple corresponds to this probability for the qubit on the ith wire of
        the output circuit.

        - 'qubitordering'. The ordering of the qubits in the 'target' tuples.

        - 'spec'. A dictionary containing all of the parameters handed to this function, except `pspec`.
        This then specifies how the circuits where generated.
    """
    experiment_dict = {}
    experiment_dict['spec'] = {}
    experiment_dict['spec']['depths'] = depths
    experiment_dict['spec']['circuits_per_length'] = circuits_per_length
    experiment_dict['spec']['sampler'] = sampler
    experiment_dict['spec']['samplerargs'] = samplerargs
    experiment_dict['spec']['addlocal'] = addlocal
    experiment_dict['spec']['lsargs'] = lsargs
    experiment_dict['spec']['descriptor'] = descriptor
    experiment_dict['spec']['createdby'] = 'extras.rb.sample.simultaneous_random_circuits_experiment'

    if isinstance(structure, str):
        assert(structure == '1Q'), "The only default `structure` option is the string '1Q'"
        structure = tuple([(q,) for q in pspec.qubit_labels])
    else:
        assert(isinstance(structure, list) or isinstance(structure, tuple)), \
            "If not a string, `structure` must be a list or tuple."
        qubits_used = []
        for qubit_labels in structure:
            assert(isinstance(qubit_labels, list) or isinstance(
                qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
            qubits_used = qubits_used + list(qubit_labels)
            assert(len(set(qubits_used)) == len(qubits_used)), \
                "The qubits in the tuples/lists of `structure must all be unique!"

        assert(set(qubits_used).issubset(set(pspec.qubit_labels))), \
            "The qubits to benchmark must all be in the ProcessorSpec `pspec`!"

    experiment_dict['spec']['structure'] = structure
    experiment_dict['circuits'] = {}
    experiment_dict['probs'] = {}
    experiment_dict['settings'] = {}

    for lnum, l in enumerate(depths):
        if verbosity > 0:
            print('- Sampling {} circuits at length {} ({} of {} depths)'.format(circuits_per_length, l,
                                                                                 lnum + 1, len(depths)))
            print('  - Number of circuits sampled = ', end='')
        for j in range(circuits_per_length):
            circuit, idealout = simultaneous_random_circuit(pspec, l, structure=structure, sampler=sampler,
                                                            samplerargs=samplerargs, addlocal=addlocal, lsargs=lsargs)

            if (not set_isolated) and (not setcomplement_isolated):
                experiment_dict['circuits'][l, j] = circuit
                experiment_dict['probs'][l, j] = idealout
                experiment_dict['settings'][l, j] = {
                    s: len(depths) + lnum * circuits_per_length + j for s in tuple(structure)}
            else:
                experiment_dict['circuits'][l, j] = {}
                experiment_dict['probs'][l, j] = {}
                experiment_dict['settings'][l, j] = {}
                experiment_dict['circuits'][l, j][tuple(structure)] = circuit
                experiment_dict['probs'][l, j][tuple(structure)] = idealout
                experiment_dict['settings'][l, j][tuple(structure)] = _get_setting(l, j, structure, depths,
                                                                                   circuits_per_length, structure)
            if set_isolated:
                for subset_ind, subset in enumerate(structure):
                    subset_circuit = circuit.copy(editable=True)
                    #print(subset)
                    for q in circuit.line_labels:
                        if q not in subset:
                            #print(subset_circuit, q)
                            subset_circuit.replace_with_idling_line(q)
                    subset_circuit.done_editing()
                    experiment_dict['circuits'][l, j][(tuple(subset),)] = subset_circuit
                    experiment_dict['probs'][l, j][(tuple(subset),)] = idealout[subset_ind]
                    # setting = {}
                    # for s in structure:
                    #     if s in subset:
                    #         setting[s] =  len(depths) + lnum*circuits_per_length + j
                    #     else:
                    #         setting[s] =  lnum
                    experiment_dict['settings'][l, j][(tuple(subset),)] = _get_setting(l, j, (tuple(subset),), depths,
                                                                                       circuits_per_length, structure)
                    # print(subset)
                    # print(_get_setting(l, j, subset, depths, circuits_per_length, structure))

            if setcomplement_isolated:
                for subset_ind, subset in enumerate(structure):
                    subsetcomplement_circuit = circuit.copy(editable=True)
                    for q in circuit.line_labels:
                        if q in subset:
                            subsetcomplement_circuit.replace_with_idling_line(q)
                    subsetcomplement_circuit.done_editing()
                    subsetcomplement = list(_copy.copy(structure))
                    subsetcomplement_idealout = list(_copy.copy(idealout))
                    del subsetcomplement[subset_ind]
                    del subsetcomplement_idealout[subset_ind]
                    subsetcomplement = tuple(subsetcomplement)
                    subsetcomplement_idealout = tuple(subsetcomplement_idealout)
                    experiment_dict['circuits'][l, j][subsetcomplement] = subsetcomplement_circuit
                    experiment_dict['probs'][l, j][subsetcomplement] = subsetcomplement_idealout

                    # for s in structure:
                    #     if s in subsetcomplement:
                    #         setting[s] =  len(depths) + lnum*circuits_per_length + j
                    #     else:
                    #         setting[s] =  lnum
                    experiment_dict['settings'][l, j][subsetcomplement] = _get_setting(l, j, subsetcomplement, depths,
                                                                                       circuits_per_length, structure)

            if verbosity > 0: print(j + 1, end=',')
        if verbosity > 0: print('')

    return experiment_dict


def exhaustive_independent_random_circuits_experiment(pspec, allowed_depths, circuits_per_subset, structure='1Q',
                                                      sampler='Qelimination', samplerargs=[], descriptor='',
                                                      verbosity=1):
    """
    Todo

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler).

    allowed_depths :
        Todo
        .
    total_circuits_per_subset : int
        Todo

    structure : str or tuple.
        Defines the "structure" of the simultaneous circuit. TODO : more details.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates.
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is the
        only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    descriptor : str, optional
        A description of the experiment being generated. Stored in the output dictionary.

    Returns
    -------
    dict

    """
    experiment_dict = {}
    experiment_dict['spec'] = {}
    experiment_dict['spec']['allowed_depths'] = allowed_depths
    experiment_dict['spec']['circuits_per_subset'] = circuits_per_subset
    experiment_dict['spec']['sampler'] = sampler
    experiment_dict['spec']['samplerargs'] = samplerargs
    experiment_dict['spec']['descriptor'] = descriptor

    if isinstance(structure, str):
        assert(structure == '1Q'), "The only default `structure` option is the string '1Q'"
        structure = tuple([(q,) for q in pspec.qubit_labels])
    else:
        assert(isinstance(structure, list) or isinstance(structure, tuple)), \
            "If not a string, `structure` must be a list or tuple."
        qubits_used = []
        for qubit_labels in structure:
            assert(isinstance(qubit_labels, list) or isinstance(
                qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
            qubits_used = qubits_used + list(qubit_labels)
            assert(len(set(qubits_used)) == len(qubits_used)), \
                "The qubits in the tuples/lists of `structure must all be unique!"

        assert(set(qubits_used).issubset(set(pspec.qubit_labels))), \
            "The qubits to benchmark must all be in the ProcessorSpec `pspec`!"

    experiment_dict['spec']['structure'] = structure
    experiment_dict['circuits'] = {}
    experiment_dict['probs'] = {}

    if circuits_per_subset**len(structure) >> 10000:
        print("Warning: {} circuits are going to be generated by this function!".format(
            circuits_per_subset**len(structure)))

    circuits = {}

    for ssQs_ind, qubit_labels in enumerate(structure):
        circuits[qubit_labels] = []
        for i in range(circuits_per_subset):
            l = allowed_depths[_np.random.randint(len(allowed_depths))]
            circuits[qubit_labels].append(random_circuit(pspec, l, qubit_labels=qubit_labels,
                                                         sampler=sampler, samplerargs=samplerargs))

    experiment_dict['subset_circuits'] = circuits

    parallel_circuits = {}
    it = [range(circuits_per_subset) for i in range(len(structure))]
    for setting_comb in _itertools.product(*it):
        pcircuit = _cir.Circuit(num_lines=0, editable=True)
        for ssQs_ind, qubit_labels in enumerate(structure):
            pcircuit.tensor_circuit(circuits[qubit_labels][setting_comb[ssQs_ind]])
            pcircuit.done_editing()
            parallel_circuits[setting_comb] = pcircuit

    experiment_dict['circuits'] = parallel_circuits

    return experiment_dict


def direct_rb_circuit(pspec, length, qubit_labels=None, sampler='Qelimination', samplerargs=[], addlocal=False,
                      lsargs=[], randomizeout=True, cliffordtwirl=True, conditionaltwirl=True, citerations=20,
                      compilerargs=[], partitioned=False):
    """
    Generates a "direct randomized benchmarking" (DRB) circuit, which is the protocol introduced in
    arXiv:1807.07975 (2018). The length of the "core" sequence is given by `length` and may be any
    integer >= 0. An n-qubit DRB circuit consists of (1) a circuit the prepares a uniformly random
    stabilizer state; (2) a length-l circuit (specified by `length`) consisting of circuit layers sampled
    according to some user-specified distribution (specified by `sampler`), (3) a circuit that maps the
    output of the preceeding circuit to a computational basis state. See arXiv:1807.07975 (2018) for further
    details.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned DRB circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler for the "core" of the DRB circuit). Unless
       `qubit_labels` is not None, the circuit is sampled over all the qubits in `pspec`.

    length : int
        The "direct RB length" of the circuit, which is closely related to the circuit depth. It
        must be an integer >= 0. Unless `addlocal` is True, it is the depth of the "core" random
        circuit, sampled according to `sampler`, specified in step (2) above. If `addlocal` is True,
        each layer in the "core" circuit sampled according to "sampler` is followed by a layer of
        1-qubit gates, with sampling specified by `lsargs` (and the first layer is proceeded by a
        layer of 1-qubit gates), and so the circuit of step (2) is length 2*`length` + 1.

    qubit_labels : list, optional
        If not None, a list of the qubits to sample the circuit for. This is a subset of
        `pspec.qubit_labels`. If None, the circuit is sampled to act on all the qubits
        in `pspec`.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates [which is not
        a valid form of sampling for n-qubit DRB, but is not explicitly forbidden in this function].
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is
        the only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    addlocal : bool, optional
        Whether to follow each layer in the "core" circuit, sampled according to `sampler` with
        a layer of 1-qubit gates.

    lsargs : list, optional
        Only used if addlocal is True. A list of optional arguments handed to the 1Q gate
        layer sampler circuit_layer_by_oneQgate(). Specifies how to sample 1Q-gate layers.

    randomizeout : bool, optional
        If False, the ideal output of the circuit (the "success" or "survival" outcome) is the all-zeros
        bit string. If True, the ideal output of the circuit is randomized to a uniformly random bit-string.
        This setting is useful for, e.g., detecting leakage/loss/measurement-bias etc.

    cliffordtwirl : bool, optional
        Wether to begin the circuit with a sequence that generates a random stabilizer state. For
        standard DRB this should be set to True. There are a variety of reasons why it is better
        to have this set to True.

    conditionaltwirl : bool, optional
        DRB only requires that the initial/final sequences of step (1) and (3) create/measure
        a uniformly random / particular stabilizer state, rather than implement a particular unitary.
        step (1) and (3) can be achieved by implementing a uniformly random Clifford gate and the
        unique inversion Clifford, respectively. This is implemented if `conditionaltwirl` is False.
        However, steps (1) and (3) can be implemented much more efficiently than this: the sequences
        of (1) and (3) only need to map a particular input state to a particular output state,
        if `conditionaltwirl` is True this more efficient option is chosen -- this is option corresponds
        to "standard" DRB. (the term "conditional" refers to the fact that in this case we essentially
        implementing a particular Clifford conditional on a known input).

    citerations : int, optional
        Some of the stabilizer state / Clifford compilation algorithms in pyGSTi (including the default
        algorithms) are  randomized, and the lowest-cost circuit is chosen from all the circuit generated
        in the iterations of the algorithm. This is the number of iterations used. The time required to
        generate a DRB circuit is linear in `citerations`. Lower-depth / lower 2-qubit gate count
        compilations of steps (1) and (3) are important in order to successfully implement DRB on as many
        qubits as possible.

    compilerargs : list, optional
        A list of arguments that are handed to the compile_stabilier_state/measurement()functions (or the
        compile_clifford() function if `conditionaltwirl `is False). This includes all the optional
        arguments of these functions *after* the `iterations` option (set by `citerations`). For most
        purposes the default options will be suitable (or at least near-optimal from the compilation methods
        in-built into pyGSTi). See the docstrings of these functions for more information.

    partitioned : bool, optional
        If False, a single circuit is returned consisting of the full circuit. If True, three circuits
        are returned in a list consisting of: (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1).

    Returns
    -------
    Circuit or list of Circuits
        If partioned is False, a random DRB circuit sampled as specified. If partioned is True, a list of
        three circuits consisting of (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1) [except in the case of cliffordtwirl=False, when it is a list of two circuits].

    Tuple
        A length-n tuple of integers in [0,1], corresponding to the error-free outcome of the
        circuit. Always all zeros if `randomizeout` is False. The ith element of the tuple
        corresponds to the error-free outcome for the qubit labelled by: the ith element of
        `qubit_labels`, if `qubit_labels` is not None; the ith element of `pspec.qubit_labels`, otherwise.
        In both cases, the ith element of the tuple corresponds to the error-free outcome for the
        qubit on the ith wire of the output circuit.
    """
    if qubit_labels is not None: n = len(qubit_labels)
    else: n = pspec.number_of_qubits
    # Sample a random circuit of "native gates".
    circuit = random_circuit(pspec=pspec, length=length, qubit_labels=qubit_labels, sampler=sampler,
                             samplerargs=samplerargs, addlocal=addlocal, lsargs=lsargs)
    # find the symplectic matrix / phase vector this "native gates" circuit implements.
    s_rc, p_rc = _symp.symplectic_rep_of_clifford_circuit(circuit, pspec=pspec)

    # If we are clifford twirling, we do an initial random circuit that is either a uniformly random
    # cliffor or creates a uniformly random stabilizer state from the standard input.
    if cliffordtwirl:
        # Sample a uniformly random Clifford.
        s_initial, p_initial = _symp.random_clifford(n)
        # Find the composite action of this uniformly random clifford and the random circuit.
        s_composite, p_composite = _symp.compose_cliffords(s_initial, p_initial, s_rc, p_rc)
        # If conditionaltwirl we do a stabilizer prep (a conditional Clifford).
        if conditionaltwirl:
            initial_circuit = _cmpl.compile_stabilizer_state(s_initial, p_initial, pspec, qubit_labels, citerations,
                                                             *compilerargs)
        # If not conditionaltwirl, we do a full random Clifford.
        else: initial_circuit = _cmpl.compile_clifford(s_initial, p_initial, pspec, qubit_labels, citerations,
                                                       *compilerargs)
    # If we are not Clifford twirling, we just copy the effect of the random circuit as the effect
    # of the "composite" prep + random circuit (as here the prep circuit is the null circuit).
    else:
        s_composite = _copy.deepcopy(s_rc)
        p_composite = _copy.deepcopy(p_rc)

    if conditionaltwirl:
        # If we want to randomize the expected output then randomize the p vector, otherwise
        # it is left as p. Note that, unlike with compile_clifford, we don't invert (s,p)
        # before handing it to the stabilizer measurement function.
        if randomizeout: p_for_measurement = _symp.random_phase_vector(s_composite, n)
        else: p_for_measurement = p_composite
        inversion_circuit = _cmpl.compile_stabilizer_measurement(s_composite, p_for_measurement, pspec, qubit_labels,
                                                                 citerations, *compilerargs)
    else:
        # Find the Clifford that inverts the circuit so far. We
        s_inverse, p_inverse = _symp.inverse_clifford(s_composite, p_composite)
        # If we want to randomize the expected output then randomize the p_inverse vector, otherwise
        # do not.
        if randomizeout: p_for_inversion = _symp.random_phase_vector(s_inverse, n)
        else: p_for_inversion = p_inverse
        # Compile the Clifford.
        inversion_circuit = _cmpl.compile_clifford(s_inverse, p_for_inversion, pspec, qubit_labels,
                                                   citerations, *compilerargs)
    if cliffordtwirl:
        full_circuit = initial_circuit.copy(editable=True)
        full_circuit.append_circuit(circuit)
        full_circuit.append_circuit(inversion_circuit)
    else:
        full_circuit = circuit.copy(editable=True)
        full_circuit.append_circuit(inversion_circuit)

    full_circuit.done_editing()

    # Find the expected outcome of the circuit.
    s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(full_circuit, pspec=pspec)
    if conditionaltwirl:  # s_out is not always the identity with a conditional twirl, only conditional on prep/measure.
        assert(_np.array_equal(s_out[:n, n:], _np.zeros((n, n), int))), "Compiler has failed!"
    else: assert(_np.array_equal(s_out, _np.identity(2 * n, int))), "Compiler has failed!"

    # Find the ideal output of the circuit.
    s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
    s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
    idealout = []
    for q in range(0, n):
        measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, q)
        bit = measurement_out[1]
        assert(bit == 0 or bit == 1), "Ideal output is not a computational basis state!"
        if not randomizeout:
            assert(bit == 0), "Ideal output is not the all 0s computational basis state!"
        idealout.append(int(measurement_out[1]))
    idealout = tuple(idealout)
    full_circuit.done_editing()

    if not partitioned: outcircuit = full_circuit
    else:
        if cliffordtwirl: outcircuit = [initial_circuit, circuit, inversion_circuit]
        else: outcircuit = [circuit, inversion_circuit]

    return outcircuit, idealout


def simultaneous_direct_rb_circuit(pspec, length, structure='1Q', sampler='Qelimination', samplerargs=[],
                                   addlocal=False, lsargs=[], randomizeout=True, cliffordtwirl=True,
                                   conditionaltwirl=True, citerations=20, compilerargs=[], partitioned=False):
    """
    Generates a simultansous "direct randomized benchmarking" (DRB) circuit, where DRB is the protocol introduced in
    arXiv:1807.07975 (2018). An n-qubit DRB circuit consists of (1) a circuit the prepares a uniformly random
    stabilizer state; (2) a length-l circuit (specified by `length`) consisting of circuit layers sampled
    according to some user-specified distribution (specified by `sampler`), (3) a circuit that maps the
    output of the preceeding circuit to a computational basis state. See arXiv:1807.07975 (2018) for further
    details. Todo : what SDRB is.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned DRB circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler for the "core" of the DRB circuit). Unless
       `qubit_labels` is not None, the circuit is sampled over all the qubits in `pspec`.

    length : int
        The "direct RB length" of the circuit, which is closely related to the circuit depth. It
        must be an integer >= 0. Unless `addlocal` is True, it is the depth of the "core" random
        circuit, sampled according to `sampler`, specified in step (2) above. If `addlocal` is True,
        each layer in the "core" circuit sampled according to "sampler` is followed by a layer of
        1-qubit gates, with sampling specified by `lsargs` (and the first layer is proceeded by a
        layer of 1-qubit gates), and so the circuit of step (2) is length 2*`length` + 1.

    structure : str or tuple, optional
        todo.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates [which is not
        a valid form of sampling for n-qubit DRB, but is not explicitly forbidden in this function].
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is
        the only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    addlocal : bool, optional
        Whether to follow each layer in the "core" circuit, sampled according to `sampler` with
        a layer of 1-qubit gates.

    lsargs : list, optional
        Only used if addlocal is True. A list of optional arguments handed to the 1Q gate
        layer sampler circuit_layer_by_oneQgate(). Specifies how to sample 1Q-gate layers.

    randomizeout : bool, optional
        If False, the ideal output of the circuit (the "success" or "survival" outcome) is the all-zeros
        bit string. If True, the ideal output of the circuit is randomized to a uniformly random bit-string.
        This setting is useful for, e.g., detecting leakage/loss/measurement-bias etc.

    cliffordtwirl : bool, optional
        Wether to begin the circuit with a sequence that generates a random stabilizer state. For
        standard DRB this should be set to True. There are a variety of reasons why it is better
        to have this set to True.

    conditionaltwirl : bool, optional
        DRB only requires that the initial/final sequences of step (1) and (3) create/measure
        a uniformly random / particular stabilizer state, rather than implement a particular unitary.
        step (1) and (3) can be achieved by implementing a uniformly random Clifford gate and the
        unique inversion Clifford, respectively. This is implemented if `conditionaltwirl` is False.
        However, steps (1) and (3) can be implemented much more efficiently than this: the sequences
        of (1) and (3) only need to map a particular input state to a particular output state,
        if `conditionaltwirl` is True this more efficient option is chosen -- this is option corresponds
        to "standard" DRB. (the term "conditional" refers to the fact that in this case we essentially
        implementing a particular Clifford conditional on a known input).

    citerations : int, optional
        Some of the stabilizer state / Clifford compilation algorithms in pyGSTi (including the default
        algorithms) are  randomized, and the lowest-cost circuit is chosen from all the circuit generated
        in the iterations of the algorithm. This is the number of iterations used. The time required to
        generate a DRB circuit is linear in `citerations`. Lower-depth / lower 2-qubit gate count
        compilations of steps (1) and (3) are important in order to successfully implement DRB on as many
        qubits as possible.

    compilerargs : list, optional
        A list of arguments that are handed to the compile_stabilier_state/measurement()functions (or the
        compile_clifford() function if `conditionaltwirl `is False). This includes all the optional
        arguments of these functions *after* the `iterations` option (set by `citerations`). For most
        purposes the default options will be suitable (or at least near-optimal from the compilation methods
        in-built into pyGSTi). See the docstrings of these functions for more information.

    partitioned : bool, optional
        If False, a single circuit is returned consisting of the full circuit. If True, three circuits
        are returned in a list consisting of: (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1).

    Returns
    -------
    Circuit or list of Circuits
        If partioned is False, a random DRB circuit sampled as specified. If partioned is True, a list of
        three circuits consisting of (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1) [except in the case of cliffordtwirl=False, when it is a list of two circuits].

    Tuple
        A length-n tuple of integers in [0,1], corresponding to the error-free outcome of the
        circuit. Always all zeros if `randomizeout` is False. The ith element of the tuple
        corresponds to the error-free outcome for the qubit labelled by: the ith element of
        `qubit_labels`, if `qubit_labels` is not None; the ith element of `pspec.qubit_labels`, otherwise.
        In both cases, the ith element of the tuple corresponds to the error-free outcome for the
        qubit on the ith wire of the output circuit.
    """
    if isinstance(structure, str):
        assert(structure == '1Q'), "The only default `structure` option is the string '1Q'"
        structure = tuple([(q,) for q in pspec.qubit_labels])
        n = pspec.number_of_qubits
    else:
        assert(isinstance(structure, list) or isinstance(structure, tuple)
               ), "If not a string, `structure` must be a list or tuple."
        qubits_used = []
        for qubit_labels in structure:
            assert(isinstance(qubit_labels, list) or isinstance(
                qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
            qubits_used = qubits_used + list(qubit_labels)
            assert(len(set(qubits_used)) == len(qubits_used)
                   ), "The qubits in the tuples/lists of `structure must all be unique!"

        assert(set(qubits_used).issubset(set(pspec.qubit_labels))
               ), "The qubits to benchmark must all be in the ProcessorSpec `pspec`!"
        n = len(qubits_used)

    for qubit_labels in structure:
        subgraph = pspec.qubitgraph.subgraph(list(qubit_labels))
        assert(subgraph.are_glob_connected(list(qubit_labels))
               ), "Each subset of qubits in `structure` must be connected!"

    # Creates a empty circuit over no wires
    circuit = _cir.Circuit(num_lines=0, editable=True)

    s_rc_dict = {}
    p_rc_dict = {}
    circuit_dict = {}

    for qubit_labels in structure:
        qubit_labels = tuple(qubit_labels)
        # Sample a random circuit of "native gates" over this set of qubits, with the
        # specified sampling.
        subset_circuit = random_circuit(pspec=pspec, length=length, qubit_labels=qubit_labels, sampler=sampler,
                                        samplerargs=samplerargs, addlocal=addlocal, lsargs=lsargs)
        circuit_dict[qubit_labels] = subset_circuit
        # find the symplectic matrix / phase vector this circuit implements.
        s_rc_dict[qubit_labels], p_rc_dict[qubit_labels] = _symp.symplectic_rep_of_clifford_circuit(
            subset_circuit, pspec=pspec)
        # Tensors this circuit with the current circuit
        circuit.tensor_circuit(subset_circuit)

    # Creates empty circuits over no wires
    inversion_circuit = _cir.Circuit(num_lines=0, editable=True)
    if cliffordtwirl:
        initial_circuit = _cir.Circuit(num_lines=0, editable=True)

    for qubit_labels in structure:
        qubit_labels = tuple(qubit_labels)
        subset_n = len(qubit_labels)
        # If we are clifford twirling, we do an initial random circuit that is either a uniformly random
        # cliffor or creates a uniformly random stabilizer state from the standard input.
        if cliffordtwirl:

            # Sample a uniformly random Clifford.
            s_initial, p_initial = _symp.random_clifford(subset_n)
            # Find the composite action of this uniformly random clifford and the random circuit.
            s_composite, p_composite = _symp.compose_cliffords(s_initial, p_initial, s_rc_dict[qubit_labels],
                                                               p_rc_dict[qubit_labels])

            # If conditionaltwirl we do a stabilizer prep (a conditional Clifford).
            if conditionaltwirl:
                subset_initial_circuit = _cmpl.compile_stabilizer_state(s_initial, p_initial, pspec, qubit_labels,
                                                                        citerations, *compilerargs)
            # If not conditionaltwirl, we do a full random Clifford.
            else:
                subset_initial_circuit = _cmpl.compile_clifford(s_initial, p_initial, pspec, qubit_labels, citerations,
                                                                *compilerargs)

            initial_circuit.tensor_circuit(subset_initial_circuit)

        # If we are not Clifford twirling, we just copy the effect of the random circuit as the effect
        # of the "composite" prep + random circuit (as here the prep circuit is the null circuit).
        else:
            s_composite = _copy.deepcopy(s_rc_dict[qubit_labels])
            p_composite = _copy.deepcopy(p_rc_dict[qubit_labels])

        if conditionaltwirl:
            # If we want to randomize the expected output then randomize the p vector, otherwise
            # it is left as p. Note that, unlike with compile_clifford, we don't invert (s,p)
            # before handing it to the stabilizer measurement function.
            if randomizeout: p_for_measurement = _symp.random_phase_vector(s_composite, subset_n)
            else: p_for_measurement = p_composite
            subset_inversion_circuit = _cmpl.compile_stabilizer_measurement(s_composite, p_for_measurement, pspec,
                                                                            qubit_labels, citerations, *compilerargs)
        else:
            # Find the Clifford that inverts the circuit so far. We
            s_inverse, p_inverse = _symp.inverse_clifford(s_composite, p_composite)
            # If we want to randomize the expected output then randomize the p_inverse vector, otherwise
            # do not.
            if randomizeout: p_for_inversion = _symp.random_phase_vector(s_inverse, subset_n)
            else: p_for_inversion = p_inverse
            # Compile the Clifford.
            subset_inversion_circuit = _cmpl.compile_clifford(s_inverse, p_for_inversion, pspec, qubit_labels,
                                                              citerations, *compilerargs)

        inversion_circuit.tensor_circuit(subset_inversion_circuit)

    inversion_circuit.done_editing()

    if cliffordtwirl:
        full_circuit = initial_circuit.copy(editable=True)
        full_circuit.append_circuit(circuit)
        full_circuit.append_circuit(inversion_circuit)
    else:
        full_circuit = _copy.deepcopy(circuit)
        full_circuit.append_circuit(inversion_circuit)

    full_circuit.done_editing()

    # Find the expected outcome of the circuit.
    s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(full_circuit, pspec=pspec)
    if conditionaltwirl:  # s_out is not always the identity with a conditional twirl, only conditional on prep/measure.
        assert(_np.array_equal(s_out[:n, n:], _np.zeros((n, n), int))), "Compiler has failed!"
    else: assert(_np.array_equal(s_out, _np.identity(2 * n, int))), "Compiler has failed!"

    # Find the ideal output of the circuit.
    s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
    s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
    idealout = []
    for qubit_labels in structure:
        subset_idealout = []
        for q in qubit_labels:
            qind = circuit.line_labels.index(q)
            measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, qind)
            bit = measurement_out[1]
            assert(bit == 0 or bit == 1), "Ideal output is not a computational basis state!"
            if not randomizeout:
                assert(bit == 0), "Ideal output is not the all 0s computational basis state!"
            subset_idealout.append(int(bit))
        idealout.append(tuple(subset_idealout))
    idealout = tuple(idealout)

    if not partitioned: outcircuit = full_circuit
    else:
        if cliffordtwirl: outcircuit = [initial_circuit, circuit, inversion_circuit]
        else: outcircuit = [circuit, inversion_circuit]

    return outcircuit, idealout


def simultaneous_direct_rb_experiment(pspec, depths, circuits_per_length, structure='1Q', sampler='Qelimination',
                                      samplerargs=[], addlocal=False, lsargs=[], randomizeout=False, cliffordtwirl=True,
                                      conditionaltwirl=True, citerations=20, compilerargs=[], partitioned=False,
                                      set_isolated=True, setcomplement_isolated=False,
                                      descriptor='A set of simultaneous DRB experiments', verbosity=1):
    """
    Generates a simultaneous "direct randomized benchmarking" (DRB) experiments, where DRB is the protocol introduced in
    arXiv:1807.07975 (2018). The

    An n-qubit DRB circuit consists of (1) a circuit the prepares a uniformly random stabilizer state;
    (2) a length-l circuit (specified by `length`) consisting of circuit layers sampled according to
    some user-specified distribution (specified by `sampler`), (3) a circuit that maps the output of
    the preceeding circuit to a computational basis state. See arXiv:1807.07975 (2018) for further
    details. In simultaneous DRB ...... TODO.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned DRB circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`. Note that `pspec`
       is always handed to the sampler, as the first argument of the sampler function (this is only
       of importance when not using an in-built sampler for the "core" of the DRB circuit). Unless
       `qubit_labels` is not None, the circuit is sampled over all the qubits in `pspec`.

    depths : int
        The set of "direct RB depths" for the circuits. The DRB depths must be integers >= 0.
        Unless `addlocal` is True, the DRB length is the depth of the "core" random circuit,
        sampled according to `sampler`, specified in step (2) above. If `addlocal` is True,
        each layer in the "core" circuit sampled according to "sampler` is followed by a layer of
        1-qubit gates, with sampling specified by `lsargs` (and the first layer is proceeded by a
        layer of 1-qubit gates), and so the circuit of step (2) is length 2*`length` + 1.

    circuits_per_length : int
        The number of (possibly) different DRB circuits sampled at each length.

    structure : str or tuple.
        Defines the "structure" of the simultaneous DRB experiment. TODO : more details.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates [which is not
        a valid form of sampling for n-qubit DRB, but is not explicitly forbidden in this function].
        If `sampler` is a function, it should be a function that takes as the first argument a
        ProcessorSpec, and returns a random circuit layer as a list of gate Label objects. Note that
        the default 'Qelimination' is not necessarily the most useful in-built sampler, but it is the
        only sampler that requires no parameters beyond the ProcessorSpec *and* works for arbitrary
        connectivity devices. See the docstrings for each of these samplers for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec`, the second argument is `qubit_labels`,
        and `samplerargs` lists the remaining arguments handed to the sampler. This is not
        optional for some choices of `sampler`.

    addlocal : bool, optional
        Whether to follow each layer in the "core" circuits, sampled according to `sampler` with
        a layer of 1-qubit gates.

    lsargs : list, optional
        Only used if addlocal is True. A list of optional arguments handed to the 1Q gate
        layer sampler circuit_layer_by_oneQgate(). Specifies how to sample 1Q-gate layers.

    randomizeout : bool, optional
        If False, the ideal output of the circuits (the "success" or "survival" outcome) is the all-zeros
        bit string. If True, the ideal output of each circuit is randomized to a uniformly random bit-string.
        This setting is useful for, e.g., detecting leakage/loss/measurement-bias etc.

    cliffordtwirl : bool, optional
        Wether to begin the circuitas with a sequence that generates a random stabilizer state. For
        standard DRB this should be set to True. There are a variety of reasons why it is better
        to have this set to True.

    conditionaltwirl : bool, optional
        DRB only requires that the initial/final sequences of step (1) and (3) create/measure
        a uniformly random / particular stabilizer state, rather than implement a particular unitary.
        step (1) and (3) can be achieved by implementing a uniformly random Clifford gate and the
        unique inversion Clifford, respectively. This is implemented if `conditionaltwirl` is False.
        However, steps (1) and (3) can be implemented much more efficiently than this: the sequences
        of (1) and (3) only need to map a particular input state to a particular output state,
        if `conditionaltwirl` is True this more efficient option is chosen -- this is option corresponds
        to "standard" DRB. (the term "conditional" refers to the fact that in this case we essentially
        implementing a particular Clifford conditional on a known input).

    citerations : int, optional
        Some of the stabilizer state / Clifford compilation algorithms in pyGSTi (including the default
        algorithms) are  randomized, and the lowest-cost circuit is chosen from all the circuits generated
        in the iterations of the algorithm. This is the number of iterations used. The time required to
        generate a DRB circuit is linear in `citerations`. Lower-depth / lower 2-qubit gate count
        compilations of steps (1) and (3) are important in order to successfully implement DRB on as many
        qubits as possible.

    compilerargs : list, optional
        A list of arguments that are handed to the compile_stabilier_state/measurement()functions (or the
        compile_clifford() function if `conditionaltwirl `is False). This includes all the optional
        arguments of these functions *after* the `iterations` option (set by `citerations`). For most
        purposes the default options will be suitable (or at least near-optimal from the compilation methods
        in-built into pyGSTi). See the docstrings of these functions for more information.

    partitioned : bool, optional
        If False, each circuit is returned as a single full circuit. If True, each circuit is returned as
        a list of three circuits consisting of: (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1).

    set_isolated : bool, optional
        Todo

    setcomplement_isolated : bool, optional
        Todo

    descriptor : str, optional
        A description of the experiment being generated. Stored in the output dictionary.

    verbosity : int, optional
        If > 0 the number of circuits generated so far is shown.

    Returns
    -------
    Circuit or list of Circuits
        If partioned is False, a random DRB circuit sampled as specified. If partioned is True, a list of
        three circuits consisting of (1) the stabilizer-prep circuit, (2) the core random circuit,
        (3) the pre-measurement circuit. In that case the full circuit is obtained by appended (2) to (1)
        and then (3) to (1).

    Tuple
        A length-n tuple of integers in [0,1], corresponding to the error-free outcome of the
        circuit. Always all zeros if `randomizeout` is False. The ith element of the tuple
        corresponds to the error-free outcome for the qubit labelled by: the ith element of
        `qubit_labels`, if `qubit_labels` is not None; the ith element of `pspec.qubit_labels`, otherwise.
        In both cases, the ith element of the tuple corresponds to the error-free outcome for the
        qubit on the ith wire of the output circuit.

    Returns
    -------
    dict
        A dictionary containing the generated RB circuits, the error-free outputs of the circuit,
        and the specification used to generate the circuits. The keys are:

        - 'circuits'. A dictionary of the sampled circuits. The circuit with key(l,k) is the kth circuit
        at DRB length l.

        - 'idealout'. A dictionary of the error-free outputs of the circuits as tuples. The tuple with
        key(l,k) is the error-free output of the (l,k) circuit. The ith element of this tuple corresponds
        to the error-free outcome for the qubit on the ith wire of the output circuit and/or the ith element
        of the list at the key 'qubitordering'. These tuples will all be (0,0,0,...) when `randomizeout` is
        False

        - 'qubitordering'. The ordering of the qubits in the 'idealout' tuples.

        - 'spec'. A dictionary containing all of the parameters handed to this function, except `pspec`.
        This then specifies how the circuits where generated.
    """

    experiment_dict = {}
    experiment_dict['spec'] = {}
    experiment_dict['spec']['depths'] = depths
    experiment_dict['spec']['circuits_per_length'] = circuits_per_length
    experiment_dict['spec']['sampler'] = sampler
    experiment_dict['spec']['samplerargs'] = samplerargs
    experiment_dict['spec']['addlocal'] = addlocal
    experiment_dict['spec']['lsargs'] = lsargs
    experiment_dict['spec']['randomizeout'] = randomizeout
    experiment_dict['spec']['cliffordtwirl'] = cliffordtwirl
    experiment_dict['spec']['conditionaltwirl'] = conditionaltwirl
    experiment_dict['spec']['citerations'] = citerations
    experiment_dict['spec']['compilerargs'] = compilerargs
    experiment_dict['spec']['partitioned'] = partitioned
    experiment_dict['spec']['descriptor'] = descriptor
    experiment_dict['spec']['createdby'] = 'extras.rb.sample.simultaneous_direct_rb_experiment'

    if isinstance(structure, str):
        assert(structure == '1Q'), "The only default `structure` option is the string '1Q'"
        structure = tuple([(q,) for q in pspec.qubit_labels])
    else:
        assert(isinstance(structure, list) or isinstance(structure, tuple)), \
            "If not a string, `structure` must be a list or tuple."
        qubits_used = []
        for qubit_labels in structure:
            assert(isinstance(qubit_labels, list) or isinstance(
                qubit_labels, tuple)), "SubsetQs must be a list or a tuple!"
            qubits_used = qubits_used + list(qubit_labels)
            assert(len(set(qubits_used)) == len(qubits_used)), \
                "The qubits in the tuples/lists of `structure must all be unique!"

        assert(set(qubits_used).issubset(set(pspec.qubit_labels))), \
            "The qubits to benchmark must all be in the ProcessorSpec `pspec`!"

    experiment_dict['spec']['structure'] = structure
    experiment_dict['circuits'] = {}
    experiment_dict['target'] = {}
    experiment_dict['settings'] = {}

    for qubit_labels in structure:
        subgraph = pspec.qubitgraph.subgraph(list(qubit_labels))
        assert(subgraph.are_glob_connected(list(qubit_labels))
               ), "Each subset of qubits in `structure` must be connected!"

    for lnum, l in enumerate(depths):
        if verbosity > 0:
            print('- Sampling {} circuits at DRB length {} ({} of {} depths)'.format(circuits_per_length, l,
                                                                                     lnum + 1, len(depths)))
            print('  - Number of circuits sampled = ', end='')
        for j in range(circuits_per_length):
            circuit, idealout = simultaneous_direct_rb_circuit(pspec, l, structure=structure, sampler=sampler,
                                                               samplerargs=samplerargs, addlocal=addlocal,
                                                               lsargs=lsargs, randomizeout=randomizeout,
                                                               cliffordtwirl=cliffordtwirl,
                                                               conditionaltwirl=conditionaltwirl,
                                                               citerations=citerations, compilerargs=compilerargs,
                                                               partitioned=partitioned)

            if (not set_isolated) and (not setcomplement_isolated):
                experiment_dict['circuits'][l, j] = circuit
                experiment_dict['target'][l, j] = idealout

            else:
                experiment_dict['circuits'][l, j] = {}
                experiment_dict['target'][l, j] = {}
                experiment_dict['settings'][l, j] = {}
                experiment_dict['circuits'][l, j][tuple(structure)] = circuit
                experiment_dict['target'][l, j][tuple(structure)] = idealout
                experiment_dict['settings'][l, j][tuple(structure)] = _get_setting(l, j, structure, depths,
                                                                                   circuits_per_length, structure)

            if set_isolated:
                for subset_ind, subset in enumerate(structure):
                    subset_circuit = circuit.copy(editable=True)
                    for q in circuit.line_labels:
                        if q not in subset:
                            subset_circuit.replace_with_idling_line(q)
                    subset_circuit.done_editing()
                    experiment_dict['circuits'][l, j][(tuple(subset),)] = subset_circuit
                    experiment_dict['target'][l, j][(tuple(subset),)] = (idealout[subset_ind],)
                    experiment_dict['settings'][l, j][(tuple(subset),)] = _get_setting(l, j, (tuple(subset),), depths,
                                                                                       circuits_per_length, structure)

            if setcomplement_isolated:
                for subset_ind, subset in enumerate(structure):
                    subsetcomplement_circuit = circuit.copy(editable=True)
                    for q in circuit.line_labels:
                        if q in subset:
                            subsetcomplement_circuit.replace_with_idling_line(q)
                    subsetcomplement_circuit.done_editing()
                    subsetcomplement = list(_copy.copy(structure))
                    subsetcomplement_idealout = list(_copy.copy(idealout))
                    del subsetcomplement[subset_ind]
                    del subsetcomplement_idealout[subset_ind]
                    subsetcomplement = tuple(subsetcomplement)
                    subsetcomplement_idealout = tuple(subsetcomplement_idealout)
                    experiment_dict['circuits'][l, j][subsetcomplement] = subsetcomplement_circuit
                    experiment_dict['target'][l, j][subsetcomplement] = subsetcomplement_idealout
                    experiment_dict['settings'][l, j][subsetcomplement] = _get_setting(l, j, subsetcomplement, depths,
                                                                                       circuits_per_length, structure)

            if verbosity > 0: print(j + 1, end=',')
        if verbosity > 0: print('')

    return experiment_dict


def clifford_rb_circuit(pspec, length, qubit_labels=None, randomizeout=False, citerations=20, compilerargs=[]):
    """
    Generates a "Clifford randomized benchmarking" (CRB) circuit, which is the current-standard
    RB protocol defined in "Scalable and robust randomized benchmarking of quantum processes",
    Magesan et al. PRL 106 180504 (2011). This consists of a sequence of `length`+1 uniformly random
    n-qubit Clifford gates followed by the unique inversion Clifford, with all the Cliffords compiled
    into the "native" gates of a device as specified by `pspec`. The circuit output by this function will
    respect the connectivity of the device, as encoded into `pspec` (see the ProcessorSpec object docstring
    for how to construct the relevant `pspec`).

    Note the convention that the the output Circuit consists of `length+2` Clifford gates, rather than the
    more usual convention of defining the "CRB length" to be the number of Clifford gates - 1. This is for
    consistency with the other RB functions in pyGSTi: in all RB-circuit-generating functions in pyGSTi
    length zero corresponds to the minimum-length circuit allowed by the protocol. Note that changing the
    "RB depths" by a constant additive factor is irrelevant for fitting purposes (except that it changes
    the obtained "SPAM" fit parameter).

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for, which defines the
       "native" gate-set and the connectivity of the device. The returned CRB circuit will be over
       the gates in `pspec`, and will respect the connectivity encoded by `pspec`.

    length : int
        The "CRB length" of the circuit -- an integer >= 0 --  which is the number of Cliffords in the
        circuit - 2 *before* each Clifford is compiled into the native gate-set.

    qubit_labels : list, optional
        If not None, a list of the qubits that the RB circuit is to be sampled for. This should
        be all or a subset of the qubits in the device specified by the ProcessorSpec `pspec`.
        If None, it is assumed that the RB circuit should be over all the qubits. Note that the
        ordering of this list is the order of the ``wires'' in the returned circuit, but is otherwise
        irrelevant. If desired, a circuit that explicitly idles on the other qubits can be obtained
        by using methods of the Circuit object.

    randomizeout : bool, optional
        If False, the ideal output of the circuit (the "success" or "survival" outcome) is the all-zeros
        bit string. This is probably considered to be the "standard" in CRB. If True, the ideal output
        of the circuit is randomized to a uniformly random bit-string. This setting is useful for, e.g.,
        detecting leakage/loss/measurement-bias etc.

    citerations : int, optional
        Some of the Clifford compilation algorithms in pyGSTi (including the default algorithm) are
        randomized, and the lowest-cost circuit is chosen from all the circuit generated in the
        iterations of the algorithm. This is the number of iterations used. The time required to
        generate a CRB circuit is linear in `citerations` * (`length`+2). Lower-depth / lower 2-qubit
        gate count compilations of the Cliffords are important in order to successfully implement
        CRB on more qubits.

    compilerargs : list, optional
        A list of arguments that are handed to compile_clifford() function, which includes all the
        optional arguments of compile_clifford() *after* the `iterations` option (set by `citerations`).
        In order, this list should be values for:
            - algorithm : str. A string that specifies the compilation algorithm. The default in
                compile_clifford() will always be whatever we consider to be the 'best' all-round
                algorith,
            - aargs : list. A list of optional arguments for the particular compilation algorithm.
            - costfunction : 'str' or function. The cost-function from which the "best" compilation
                for a Clifford is chosen from all `citerations` compilations. The default costs a
                circuit as 10x the num. of 2-qubit gates in the circuit + 1x the depth of the circuit.
            - prefixpaulis : bool. Whether to prefix or append the Paulis on each Clifford.
            - paulirandomize : bool. Whether to follow each layer in the Clifford circuit with a
                random Pauli on each qubit (compiled into native gates). I.e., if this is True the
                native gates are Pauli-randomized. When True, this prevents any coherent errors adding
                (on average) inside the layers of each compiled Clifford, at the cost of increased
                circuit depth. Defaults to False.
        For more information on these options, see the compile_clifford() docstring.

    Returns
    -------
    Circuit
        A random CRB circuit over the "native" gate-set specified.

    Tuple
        A length-n tuple of integers in [0,1], corresponding to the error-free outcome of the
        circuit. Always all zeros if `randomizeout` is False. The ith element of the tuple
        corresponds to the error-free outcome for the qubit labelled by: the ith element of
        `qubit_labels`, if `qubit_labels` is not None; the ith element of `pspec.qubit_labels`, otherwise.
        In both cases, the ith element of the tuple corresponds to the error-free outcome for the
        qubit on the ith wire of the output circuit.
    """
    # Find the labels of the qubits to create the circuit for.
    if qubit_labels is not None: qubits = qubit_labels[:]  # copy this list
    else: qubits = pspec.qubit_labels[:]  # copy this list
    # The number of qubits the circuit is over.
    n = len(qubits)

    # Initialize the identity circuit rep.
    s_composite = _np.identity(2 * n, int)
    p_composite = _np.zeros((2 * n), int)
    # Initialize an empty circuit
    full_circuit = _cir.Circuit(layer_labels=[], line_labels=qubits, editable=True)

    # Sample length+1 uniformly random Cliffords (we want a circuit of length+2 Cliffords, in total), compile
    # them, and append them to the current circuit.
    for i in range(0, length + 1):

        s, p = _symp.random_clifford(n)
        circuit = _cmpl.compile_clifford(s, p, pspec, qubit_labels=qubit_labels, iterations=citerations, *compilerargs)
        # Keeps track of the current composite Clifford
        s_composite, p_composite = _symp.compose_cliffords(s_composite, p_composite, s, p)
        full_circuit.append_circuit(circuit)

    # Find the symplectic rep of the inverse clifford
    s_inverse, p_inverse = _symp.inverse_clifford(s_composite, p_composite)

    # If we want to randomize the expected output then randomize the p_inverse vector, so that
    # the final bit of circuit will only invert the preceeding circuit up to a random Pauli.
    if randomizeout: p_for_inversion = _symp.random_phase_vector(s_inverse, n)
    else: p_for_inversion = p_inverse

    # Compile the inversion circuit
    inversion_circuit = _cmpl.compile_clifford(s_inverse, p_for_inversion, pspec, qubit_labels=qubit_labels,
                                               iterations=citerations, *compilerargs)
    full_circuit.append_circuit(inversion_circuit)
    full_circuit.done_editing()
    # Find the expected outcome of the circuit.
    s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(full_circuit, pspec=pspec)
    # Check the output is the identity up to Paulis.
    assert(_np.array_equal(s_out[:n, n:], _np.zeros((n, n), int)))
    # Find the ideal-out of the circuit, as a bit-string.
    s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
    s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
    idealout = []
    for q in range(n):
        measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, q)
        # This is the probability of the 0 outcome (it is a float)
        bit = measurement_out[1]
        assert(_np.allclose(bit, 0.) or _np.allclose(bit, 1.)), "Ideal output is not a computational basis state!"
        if not randomizeout: assert(_np.allclose(bit, 0.)), "Ideal output is not the all 0s computational basis state!"
        idealout.append(round(measurement_out[1]))
    # Convert ideal-out to a tuple, so that it is imutable
    idealout = tuple(idealout)

    full_circuit.done_editing()
    return full_circuit, idealout


def pauli_layer_as_compiled_circuit(pspec, qubit_labels=None, keepidle=False):
    """
    Samples a uniformly random n-qubit Pauli and then converts
    it to the native gate-set of `pspec`.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device.

    qubit_labels : list, optional
        If not None, a list of a subset of the qubits from `pspec` that
        the pauli circuit should act on.

    keepidle : bool, optional
        Whether to always have the circuit at-least depth 1.

    Returns
    -------
    Circuit
        A circuit corresponding to a uniformly random n-qubit Pauli.
    """
    if qubit_labels is not None: qubits = qubit_labels[:]  # copy this list
    else: qubits = pspec.qubit_labels[:]  # copy this list
    n = len(qubits)

    # The hard-coded notation for that Pauli operators
    paulis = ['I', 'X', 'Y', 'Z']

    # Samples a random Pauli layer
    r = _np.random.randint(0, 4, size=n)
    pauli_layer_std_lbls = [_lbl.Label(paulis[r[q]], (qubits[q],)) for q in range(n)]
    # Converts the layer to a circuit, and changes to the native model.
    pauli_circuit = _cir.Circuit(layer_labels=pauli_layer_std_lbls, line_labels=qubits).parallelize()
    pauli_circuit = pauli_circuit.copy(editable=True)
    pauli_circuit.change_gate_library(pspec.compilations['absolute'])
    if keepidle:
        if pauli_circuit.depth() == 0:
            pauli_circuit.insert_layer([_lbl.Label(())], 0)

    pauli_circuit.done_editing()
    return pauli_circuit


def oneQclifford_layer_as_compiled_circuit(pspec, qubit_labels=None):
    """
    Samples a uniformly random layer of 1-qubit Cliffords on all
    the qubits, and then converts it to the native gate-set of `pspec`.
    That is, an independent and uniformly random 1-qubit Clifford is
    sampled for each qubit.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device.

    qubit_labels : list, optional
        If not None, a list of a subset of the qubits from `pspec` that
        the circuit should act on.

    Returns
    -------
    Circuit
        A circuit corresponding to an independent, uniformly random 1-qubit
        Clifford gate on each qubit.
    """
    if qubit_labels is not None:
        n = len(qubit_labels)
        qubits = qubit_labels[:]  # copy this list
    else:
        n = pspec.number_of_qubits
        qubits = pspec.qubit_labels[:]  # copy this list

    # The hard-coded notation for the 1Q clifford operators
    oneQcliffords = ['C' + str(i) for i in range(24)]

    r = _np.random.randint(0, 24, size=n)

    oneQclifford_layer_std_lbls = [_lbl.Label(oneQcliffords[r[q]], (qubits[q],)) for q in range(n)]
    oneQclifford_circuit = _cir.Circuit(layer_labels=oneQclifford_layer_std_lbls, line_labels=qubits).parallelize()
    oneQclifford_circuit = oneQclifford_circuit.copy(editable=True)
    oneQclifford_circuit.change_gate_library(pspec.compilations['absolute'])
    oneQclifford_circuit.done_editing()

    if len(oneQclifford_circuit) == 0:
        oneQclifford_circuit = _cir.Circuit(layer_labels='[]', line_labels=qubits)

    return oneQclifford_circuit


def mirror_rb_circuit(pspec, length, qubit_labels=None, sampler='Qelimination', samplerargs=[], localclifford=True,
                      paulirandomize=True):
    """
    Generates a "mirror randomized benchmarking" (MRB) circuit, for the case of Clifford gates and with the option
    of Pauli-randomization and Clifford-twirling. This RB method is currently in development; this docstring will
    be updated in the future with further information on this technique.

    To implement mirror RB it is necessary for U^(-1) to in the gate-set for every U in the gate-set.

    Parameters
    ----------
    pspec : ProcessorSpec
       The ProcessorSpec for the device that the circuit is being sampled for. The `pspec` is always
       handed to the sampler, as the first argument of the sampler function.

    length : int
        The "mirror RB length" of the circuit, which is closely related to the circuit depth. It
        must be an even integer, and can be zero.

        - If `localclifford` and `paulirandomize` are False, this is the depth of the sampled circuit.
          The first length/2 layers are all sampled independently according to the sampler specified by
          `sampler`. The remaining half of the circuit is the "inversion" circuit that is determined
          by the first half.

        - If `paulirandomize` is True and `localclifford` is False, the depth of the circuits is
          2*length+1 with odd-indexed layers sampled according to the sampler specified by `sampler, and
          the the zeroth layer + the even-indexed layers consisting of random 1-qubit Pauli gates.

        - If `paulirandomize` and `localclifford` are True, the depth of the circuits is
          2*length+1 + X where X is a random variable (between 0 and normally <= ~12-16) that accounts for
          the depth from the layer of random 1-qubit Cliffords at the start and end of the circuit.

        - If `paulirandomize` is False and `localclifford` is True, the depth of the circuits is
          length + X where X is a random variable (between 0 and normally <= ~12-16) that accounts for
          the depth from the layer of random 1-qubit Cliffords at the start and end of the circuit.

    qubit_labels : list, optional
        If not None, a list of the qubits that the RB circuit is to be sampled for. This should
        be all or a subset of the qubits in the device specified by the ProcessorSpec `pspec`.
        If None, it is assumed that the RB circuit should be over all the qubits. Note that the
        ordering of this list is the order of the ``wires'' in the returned circuit, but is otherwise
        irrelevant.

    sampler : str or function, optional
        If a string, this should be one of: {'pairingQs', 'Qelimination', 'co2Qgates', 'local'}.
        Except for 'local', this corresponds to sampling layers according to the sampling function
        in rb.sampler named circuit_layer_by* (with * replaced by 'sampler'). For 'local', this
        corresponds to sampling according to rb.sampler.circuit_layer_of_oneQgates [which is not
        a valid option for n-qubit MRB -- it results in sim. 1-qubit MRB -- but it is not explicitly
        forbidden by this function]. If `sampler` is a function, it should be a function that takes
        as the first argument a ProcessorSpec, and returns a random circuit layer as a list of gate
        Label objects. Note that the default 'Qelimination' is not necessarily the most useful
        in-built sampler, but it is the only sampler that requires no parameters beyond the ProcessorSpec
        *and* works for arbitrary connectivity devices. See the docstrings for each of these samplers
        for more information.

    samplerargs : list, optional
        A list of arguments that are handed to the sampler function, specified by `sampler`.
        The first argument handed to the sampler is `pspec` and `samplerargs` lists the
        remaining arguments handed to the sampler.

    localclifford: bool, optional
        Whether to start the circuit with uniformly random 1-qubit Cliffords and all of the
        qubits (compiled into the native gates of the device).

    paulirandomize: bool, optional
        Whether to have uniformly random Pauli operators on all of the qubits before and
        after all of the layers in the "out" and "back" random circuits. At length 0 there
        is a single layer of random Pauli operators (in between two layers of 1-qubit Clifford
        gates if `localclifford` is True); at length l there are 2l+1 Pauli layers as there
        are

    Returns
    -------
    Circuit
        A random MRB circuit, sampled as specified, of depth:

            - `length`, if not paulirandomize and not local clifford.
            - 2*`length`+1 if paulirandomize and not local clifford.
            - `length` + X, if not paulirandomize and local clifford, where X is a random variable
              that accounts for the depth from the layers of random 1-qubit Cliffords (X = 2 if the 1
              qubit Clifford gates are "native" gates in the ProcessorSpec).
            - 2*`length`+1 + X, if paulirandomize and local clifford, where X is a random variable
              that accounts for the depth from the layers of random 1-qubit Cliffords (X = 2 if the 1
              qubit Clifford gates are "native" gates in the ProcessorSpec).

    Tuple
        A length-n tuple of integers in [0,1], corresponding to the error-free outcome of the
        circuit. Always all zeros if `randomizeout` is False. The ith element of the tuple
        corresponds to the error-free outcome for the qubit labelled by: the ith element of
        `qubit_labels`, if `qubit_labels` is not None; the ith element of `pspec.qubit_labels`, otherwise.
        In both cases, the ith element of the tuple corresponds to the error-free outcome for the
        qubit on the ith wire of the output circuit.
    """
    assert(length % 2 == 0), "The mirror rb length `length` must be even!"
    random_natives_circuit_length = length // 2

    if qubit_labels is not None:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)
               ), "If not None, `qubit_labels` must be a list!"
        qubit_labels = list(qubit_labels)
        n = len(qubit_labels)
    else:
        n = pspec.number_of_qubits

    # Check that the inverse of every gate is in the model:
    for gname in pspec.root_gate_names:
        assert(gname in list(pspec.gate_inverse.keys())), \
            "%s gate does not have an inverse in the gate-set! MRB is not possible!" % gname

    # Find a random circuit according to the sampling specified; this is the "out" circuit.
    circuit = random_circuit(pspec, random_natives_circuit_length, qubit_labels=qubit_labels,
                             sampler=sampler, samplerargs=samplerargs)
    circuit = circuit.copy(editable=True)
    # Copy the circuit, to create the "back" circuit from the "out" circuit.
    circuit_inv = circuit.copy(editable=True)
    # First we reverse the circuit; then we'll replace each gate with its inverse.
    circuit_inv.reverse()
    # Go through the circuit and replace every gate with its inverse, stored in the pspec. If the circuits
    # are length 0 this is skipped.
    circuit_inv.map_names_inplace(pspec.gate_inverse)

    # If we are Pauli randomizing, we add a indepedent uniformly random Pauli layer, as a compiled circuit, after
    # every layer in the "out" and "back" circuits. If the circuits are length 0 we do nothing here.
    if paulirandomize:
        for i in range(random_natives_circuit_length):
            pauli_circuit = pauli_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels, keepidle=True)
            circuit.insert_circuit(pauli_circuit, random_natives_circuit_length - i)
            pauli_circuit = pauli_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels, keepidle=True)
            circuit_inv.insert_circuit(pauli_circuit, random_natives_circuit_length - i)

    # We then append the "back" circuit to the "out" circuit. At length 0 this will be a length 0 circuit.
    circuit.append_circuit(circuit_inv)

    # If we Pauli randomize, There should also be a random Pauli at the start of this circuit; so we add that. If we
    # have a length 0 circuit we now end up with a length 1 circuit (or longer, if compiled Paulis). So, there is always
    # a random Pauli.
    if paulirandomize:
        pauli_circuit = pauli_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels, keepidle=True)
        circuit.insert_circuit(pauli_circuit, 0)

    # If we start with a random layer of 1-qubit Cliffords, we sample this here.
    if localclifford:
        # Sample a compiled 1Q Cliffords layer
        oneQclifford_circuit_out = oneQclifford_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels)
        # Generate the inverse in the same way as before (note that this will not be the same in some
        # circumstances as finding the inverse Cliffords and using the compilations for those. It doesn't
        # matter much which we do).
        oneQclifford_circuit_back = oneQclifford_circuit_out.copy(editable=True)
        oneQclifford_circuit_back.reverse()
        oneQclifford_circuit_back.map_names_inplace(pspec.gate_inverse)

        # Put one these 1Q clifford circuits at the start and one at then end.
        circuit.append_circuit(oneQclifford_circuit_out)
        circuit.prefix_circuit(oneQclifford_circuit_back)

    circuit.done_editing()

    # The full circuit should be, up to a Pauli, the identity.
    s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(circuit, pspec=pspec)
    assert(_np.array_equal(s_out, _np.identity(2 * n, int)))

    # Find the error-free output.
    s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
    s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
    idealout = []

    for q in range(n):
        measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, q)
        bit = measurement_out[1]
        assert(bit == 0 or bit == 1), "Ideal output is not a computational basis state!"
        if not paulirandomize:
            assert(bit == 0), "Ideal output is not the all 0s computational basis state!"
        idealout.append(int(measurement_out[1]))
    idealout = tuple(idealout)

    return circuit, idealout


def oneQ_generalized_rb_sequence(m, group_or_model, inverse=True, random_pauli=False, interleaved=None,
                                 group_inverse_only=False, group_prep=False, compilation=None,
                                 generated_group=None, model_to_group_labels=None, seed=None, randState=None):
    """
    Makes a random 1-qubit RB sequence, with RB over an arbitrary group and with a range of other
    options that allow circuits for many types of RB to be generated, including:

    - Clifford RB
    - Direct RB
    - Interleaved Clifford or direct RB
    - Unitarity Clifford or direct RB

    The function can in-principle be used beyond 1-qubit RB, but it relies on explicit matrix representation
    of a group, which is infeasble for, e.g., the many-qubit Clifford group.

    Note that this function has *not* been carefully tested. This will be rectified in the future,
    or this function will be replaced.

    Parameters
    ----------
    m : int
        The number of random gates in the sequence.

    group_or_model : Model or MatrixGroup
        Which Model of MatrixGroup to create the random sequence for. If
        inverse is true and this is a Model, the Model gates must form
        a group (so in this case it requires the *target model* rather than
        a noisy model). When inverse is true, the MatrixGroup for the model
        is generated. Therefore, if inverse is true and the function is called
        multiple times, it will be much faster if the MatrixGroup is provided.

    inverse: Bool, optional
        If true, the random sequence is followed by its inverse gate. The model
        must form a group if this is true. If it is true then the sequence
        returned is length m+1 (2m+1) if interleaved is False (True).

    interleaved: Str, optional
        If not None, then a oplabel string. When a oplabel string is provided,
        every random gate is followed by this gate. So the returned sequence is of
        length 2m+1 (2m) if inverse is True (False).

    group_prep: bool, optional
        If group_inverse_only is True and inverse is True, setting this to true
        creates a "group pre-twirl". Does nothing otherwise (which should be changed
        at some point).

    seed : int, optional
        Seed for random number generator; optional.

    randState : numpy.random.RandomState, optional
        A RandomState object to generate samples from. Can be useful to set
        instead of `seed` if you want reproducible distribution samples across
        multiple random function calls but you don't want to bother with
        manually incrementing seeds between those calls.

    Returns
    -------
    Circuit
        The random operation sequence of length:
        m if inverse = False, interleaved = None
        m + 1 if inverse = True, interleaved = None
        2m if inverse = False, interleaved not None
        2m + 1 if inverse = True, interleaved not None
    """
    assert hasattr(group_or_model, 'gates') or hasattr(group_or_model,
                                                       'product'), 'group_or_model must be a MatrixGroup of Model'
    group = None
    model = None
    if hasattr(group_or_model, 'gates'):
        model = group_or_model
    if hasattr(group_or_model, 'product'):
        group = group_or_model

    if randState is None:
        rndm = _np.random.RandomState(seed)  # ok if seed is None
    else:
        rndm = randState

    if (inverse) and (not group_inverse_only):
        if model:
            group = _rbobjs.MatrixGroup(group_or_model.operations.values(),
                                        group_or_model.operations.keys())

        rndm_indices = rndm.randint(0, len(group), m)
        if interleaved:
            interleaved_index = group.label_indices[interleaved]
            interleaved_indices = interleaved_index * _np.ones((m, 2), int)
            interleaved_indices[:, 0] = rndm_indices
            rndm_indices = interleaved_indices.flatten()

        random_string = [group.labels[i] for i in rndm_indices]
        effective_op = group.product(random_string)
        inv = group.get_inv(effective_op)
        random_string.append(inv)

    if (inverse) and (group_inverse_only):
        assert (model is not None), "gateset_or_group should be a Model!"
        assert (compilation is not None), "Compilation of group elements to model needs to be specified!"
        assert (generated_group is not None), "Generated group needs to be specified!"
        if model_to_group_labels is None:
            model_to_group_labels = {}
            for gate in model.get_primitive_op_labels():
                assert(gate in generated_group.labels), "model labels are not in \
                the generated group! Specify a model_to_group_labels dictionary."
                model_to_group_labels = {'gate': 'gate'}
        else:
            for gate in model.get_primitive_op_labels():
                assert(gate in model_to_group_labels.keys()), "model to group labels \
                are invalid!"
                assert(model_to_group_labels[gate] in generated_group.labels), "model to group labels \
                are invalid!"

        opLabels = model.get_primitive_op_labels()
        rndm_indices = rndm.randint(0, len(opLabels), m)
        if interleaved:
            interleaved_index = opLabels.index(interleaved)
            interleaved_indices = interleaved_index * _np.ones((m, 2), int)
            interleaved_indices[:, 0] = rndm_indices
            rndm_indices = interleaved_indices.flatten()

        # This bit of code is a quick hashed job. Needs to be checked at somepoint
        if group_prep:
            rndm_group_index = rndm.randint(0, len(generated_group))
            prep_random_string = compilation[generated_group.labels[rndm_group_index]]
            prep_random_string_group = [generated_group.labels[rndm_group_index], ]

        random_string = [opLabels[i] for i in rndm_indices]
        random_string_group = [model_to_group_labels[opLabels[i]] for i in rndm_indices]
        # This bit of code is a quick hashed job. Needs to be checked at somepoint
        if group_prep:
            random_string = prep_random_string + random_string
            random_string_group = prep_random_string_group + random_string_group
        #print(random_string)
        inversion_group_element = generated_group.get_inv(generated_group.product(random_string_group))

        # This bit of code is a quick hash job, and only works when the group is the 1-qubit Cliffords
        if random_pauli:
            pauli_keys = ['Gc0', 'Gc3', 'Gc6', 'Gc9']
            rndm_index = rndm.randint(0, 4)

            if rndm_index == 0 or rndm_index == 3:
                bitflip = False
            else:
                bitflip = True
            inversion_group_element = generated_group.product([inversion_group_element, pauli_keys[rndm_index]])

        inversion_sequence = compilation[inversion_group_element]
        random_string.extend(inversion_sequence)

    if not inverse:
        if model:
            opLabels = model.get_primitive_op_labels()
            rndm_indices = rndm.randint(0, len(opLabels), m)
            if interleaved:
                interleaved_index = opLabels.index(interleaved)
                interleaved_indices = interleaved_index * _np.ones((m, 2), int)
                interleaved_indices[:, 0] = rndm_indices
                rndm_indices = interleaved_indices.flatten()
            random_string = [opLabels[i] for i in rndm_indices]

        else:
            rndm_indices = rndm.randint(0, len(group), m)
            if interleaved:
                interleaved_index = group.label_indices[interleaved]
                interleaved_indices = interleaved_index * _np.ones((m, 2), int)
                interleaved_indices[:, 0] = rndm_indices
                rndm_indices = interleaved_indices.flatten()
            random_string = [group.labels[i] for i in rndm_indices]

    if not random_pauli:
        return _objs.Circuit(random_string)
    if random_pauli:
        return _objs.Circuit(random_string), bitflip


def random_germ(pspec, depths, interactingQs_density, qubit_labels):
    """
    todo.
    """
    if qubit_labels is None:
        qubits = list(pspec.qubit_labels[:])  # copy this list
    else:
        qubits = list(qubit_labels[:])  # copy this list

    width = len(qubits)

    germcircuit = _cir.Circuit(layer_labels=[], line_labels=qubits, editable=True)

#     germlength = {}
#     for q in qubits:
#         glp = 0
#         while _np.random.binomial(1, 0.2) == 1:
#             glp += 1
#         germlength[q] = 2 ** glp

#     circleng = max(list(germlength.values()))
#     #print(circleng)
#     subgerm = {}
#     poweredsubgerm = {}

    rand = _np.random.rand()
    if rand < 4 / 8:
        max_subgerm_depth = 1
    elif rand < 6 / 8:
        max_subgerm_depth = 2
    elif rand < 7 / 8:
        max_subgerm_depth = 4
    else:
        max_subgerm_depth = 8

    if interactingQs_density > 0:
        required_num_2Q_locations = max_subgerm_depth * width * interactingQs_density
        R = int(_np.ceil(2 / required_num_2Q_locations))
    else:
        R = 1

    germ_depth = R * max_subgerm_depth

    #print(max_subgerm_depth, R, germ_depth)

    # gcirclenpower = 0
    # while _np.random.binomial(1, 0.5) == 1:
    #     gcirclenpower += 1

    # if interactingQs_density > 0:
    #     logw = int(_np.floor(_np.log2(len(qubits))))
    #     log2 = int(_np.log2(1 / interactingQs_density))

    #     mingermlengthpower = min(0, 1 + log2 - logw)
    #     #int(_np.ceil(_np.log2(1 / (len(qubits) * interactingQs_density * 0.5))))
    # else:
    #     mingermlengthpower = 0

    # gcirclenpower = max(gcirclenpower, mingermlengthpower)
    # print(mingermlengthpower, gcirclenpower)

    subgerm_depth = {}
    for q in qubits:
        subgerm_depth_power = 0
        while (_np.random.binomial(1, 0.5) == 1) and (2 ** subgerm_depth_power < max_subgerm_depth):
            subgerm_depth_power += 1
        subgerm_depth[q] = 2 ** subgerm_depth_power

    #print(2**gcirclenpower)
    #print(germlength)
    #circleng = 2**gcirclenpower  #max(list(germlength.values()))
    #print(circleng)
    #print(circleng)
    subgerm = {}
    repeated_subgerm = {}

    for q in qubits:
        subgerm[q] = []
        possibleops = pspec.clifford_ops_on_qubits[(q,)]
        subgerm[q] = [possibleops[_np.random.randint(0, len(possibleops))] for l in range(subgerm_depth[q])]
        repeated_subgerm[q] = (germ_depth // subgerm_depth[q]) * subgerm[q]

    for l in range(germ_depth):
        layer = [repeated_subgerm[q][l] for q in qubits]
        germcircuit.insert_layer(layer, 0)

    #tempgermcircuit = germcircuit.copy()

    if interactingQs_density > 0:

        assert(germ_depth * width * interactingQs_density >= 2)
        #while len(germcircuit) * len(qubits) * interactingQs_density * 0.5 < 1:
        #
        #    germcircuit.append_circuit(tempgermcircuit)

        #print(len(qubits))
        num2Qtoadd = int(_np.floor(germ_depth * width * interactingQs_density / 2))
        #print(num2Qtoadd)

        edgelistdict = {}
        for l in range(len(germcircuit)):

            # Prep the sampling variables.
            edgelist = pspec.qubitgraph.edges()
            edgelist = [e for e in edgelist if all([q in qubits for q in e])]
            selectededges = []

            # Go through until all qubits have been assigned a gate.
            while len(edgelist) > 0:

                edge = edgelist[_np.random.randint(0, len(edgelist))]
                selectededges.append(edge)
                # Delete all edges containing these qubits.
                edgelist = [e for e in edgelist if not any([q in e for q in edge])]

            edgelistdict[l] = selectededges

        edge_and_depth_list = []
        for l in edgelistdict.keys():
            edge_and_depth_list += [(l, edge) for edge in edgelistdict[l]]

        #print(edgelistdict)
        for i in range(num2Qtoadd):

            # OLD VERSION
            # #print(i)
            # depthposition = list(edgelistdict.keys())[_np.random.randint(0, len(edgelistdict))]
            # edgeind = _np.random.randint(0, len(edgelistdict[depthposition]))
            # edge = edgelistdict[depthposition][edgeind]
            # del edgelistdict[depthposition][edgeind]
            # if len(edgelistdict[depthposition]) == 0:
            #     #print('removing depth {}'.format(depthposition))
            #     del edgelistdict[depthposition]

            sampind = _np.random.randint(0, len(edge_and_depth_list))
            (depthposition, edge) = edge_and_depth_list[sampind]
            del edge_and_depth_list[sampind]

            # The two-qubit gates on that edge.
            possibleops = pspec.clifford_ops_on_qubits[edge]
            op = possibleops[_np.random.randint(0, len(possibleops))]

            newlayer = []
            newlayer = [op] + [gate for gate in germcircuit[depthposition] if gate.qubits[0] not in edge]
            #print(newlayer)
            germcircuit.delete_layers(depthposition)
            germcircuit.insert_layer(newlayer, depthposition)

        germcircuit.done_editing()
        #newgermcircuit = _cir.Circuit(layer_labels=[], line_labels=qubits, editable=True)
        #for layer in germcircuit:
        #    newgermcircuit.insert_layer(layer,0)

    return germcircuit


def random_germpower_circuits(pspec, depths, interactingQs_density, qubit_labels, fixed_versus_depth=False):

    #import numpy as _np
    #from pygsti.objects import circuit as _cir

    if qubit_labels is None:
        qubits = list(pspec.qubit_labels[:])  # copy this list
    else:
        qubits = list(qubit_labels[:])  # copy this list

    if fixed_versus_depth:
        germcircuit = random_germ(pspec, depths, interactingQs_density, qubit_labels)
    else:
        germcircuits = []

    circs = []
    #germpowers = []
    for length in depths:
        gdepth = 0
        fullcircuit = _cir.Circuit(layer_labels=[], line_labels=qubits, editable=True)
        if not fixed_versus_depth:
            germcircuit = random_germ(pspec, depths, interactingQs_density, qubit_labels)
            germcircuits.append(germcircuit)
        while len(fullcircuit) < length:
            fullcircuit.append_circuit(germcircuit)
            gdepth += 1

        while len(fullcircuit) > length:
            fullcircuit.delete_layers(len(fullcircuit) - 1)

        circs.append(fullcircuit)
        #germpowers.append(gdepth)

    aux = {  # 'germ_powers': germpowers,
        #'subgerm_depth': subgerm_depth,
        #'max_subgerm_depth': max_subgerm_depth
    }

    if fixed_versus_depth:
        aux['germ'] = germcircuit
    else:
        aux['germ'] = germcircuits

    return circs, aux


def random_germpower_mirror_circuits(pspec, depths, qubit_labels=None, localclifford=True, paulirandomize=True,
                                     interactingQs_density=1 / 8, fixed_versus_depth=False):
    """
    length : consistent with RB length.
    """
    from pygsti.tools import symplectic as _symp

    import numpy as _np
    #assert(length % 2 == 0), "The mirror rb length `length` must be even!"

    if qubit_labels is not None:
        assert(isinstance(qubit_labels, list) or isinstance(qubit_labels, tuple)
               ), "If not None, `qubit_labels` must be a list!"
        qubit_labels = list(qubit_labels)
        n = len(qubit_labels)
    else:
        n = pspec.number_of_qubits

    # Check that the inverse of every gate is in the model:
    for gname in pspec.root_gate_names:
        assert(gname in list(pspec.gate_inverse.keys())), \
            "%s gate does not have an inverse in the gate-set! MRB is not possible!" % gname

    circuits, aux = random_germpower_circuits(pspec, depths, interactingQs_density=interactingQs_density,
                                              qubit_labels=qubit_labels, fixed_versus_depth=fixed_versus_depth)

    if paulirandomize:
        pauli_circuit = pauli_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels, keepidle=True)

    if localclifford:
        # Sample a compiled 1Q Cliffords layer
        oneQclifford_circuit_out = oneQclifford_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels)
        # Generate the inverse in the same way as before (note that this will not be the same in some
        # circumstances as finding the inverse Cliffords and using the compilations for those. It doesn't
        # matter much which we do).
        oneQclifford_circuit_back = oneQclifford_circuit_out.copy(editable=True)
        oneQclifford_circuit_back.reverse()
        oneQclifford_circuit_back.map_names_inplace(pspec.gate_inverse)

    circlist = []
    outlist = []

    for circuit in circuits:
        circuit = circuit.copy(editable=True)
        circuit_inv = circuit.copy(editable=True)
        circuit_inv.reverse()
        circuit_inv.map_names_inplace(pspec.gate_inverse)

        if paulirandomize:
            # If .....
            if not fixed_versus_depth:
                pauli_circuit = pauli_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels, keepidle=True)

            circuit.append_circuit(pauli_circuit)
            circuit.append_circuit(circuit_inv)

        # If we start with a random layer of 1-qubit Cliffords, we sample this here.
        if localclifford:
            # If .....
            if not fixed_versus_depth:
                # Sample a compiled 1Q Cliffords layer
                oneQclifford_circuit_out = oneQclifford_layer_as_compiled_circuit(pspec, qubit_labels=qubit_labels)
                # Generate the inverse in the same way as before (note that this will not be the same in some
                # circumstances as finding the inverse Cliffords and using the compilations for those. It doesn't
                # matter much which we do).
                oneQclifford_circuit_back = oneQclifford_circuit_out.copy(editable=True)
                oneQclifford_circuit_back.reverse()
                oneQclifford_circuit_back.map_names_inplace(pspec.gate_inverse)

            # Put one these 1Q clifford circuits at the start and one at then end.
            circuit.append_circuit(oneQclifford_circuit_out)
            circuit.prefix_circuit(oneQclifford_circuit_back)

        circuit.done_editing()
        circlist.append(circuit)

        # The full circuit should be, up to a Pauli, the identity.
        s_out, p_out = _symp.symplectic_rep_of_clifford_circuit(circuit, pspec=pspec)
        assert(_np.array_equal(s_out, _np.identity(2 * n, int)))

        # Find the error-free output.
        s_inputstate, p_inputstate = _symp.prep_stabilizer_state(n, zvals=None)
        s_outstate, p_outstate = _symp.apply_clifford_to_stabilizer_state(s_out, p_out, s_inputstate, p_inputstate)
        idealout = []

        for q in range(n):
            measurement_out = _symp.pauli_z_measurement(s_outstate, p_outstate, q)
            bit = measurement_out[1]
            assert(bit == 0 or bit == 1), "Ideal output is not a computational basis state!"
            if not paulirandomize:
                assert(bit == 0), "Ideal output is not the all 0s computational basis state!"
            idealout.append(int(measurement_out[1]))
        idealout = tuple(idealout)

        outlist.append(idealout)

    #return circuit, idealout
    return circlist, outlist, aux


def random_germpower_mirror_circuit_experiment(pspec, depths, circuits_per_length, qubit_labels=None,
                                               sampler='edgegrab', samplerargs=[1 / 4], localclifford=True,
                                               paulirandomize=True, fixed_versus_depth=False, descriptor=''):

    assert(sampler == 'edgegrab'), "The germ must be selected with edgegrab sampling!"
    experiment_dict = {}
    experiment_dict['spec'] = {}
    experiment_dict['spec']['depths'] = depths
    experiment_dict['spec']['circuits_per_length'] = circuits_per_length
    experiment_dict['spec']['qubit_labels'] = qubit_labels
    experiment_dict['spec']['sampler'] = sampler
    experiment_dict['spec']['samplerargs'] = samplerargs
    experiment_dict['spec']['localclifford'] = localclifford
    experiment_dict['spec']['paulirandomize'] = paulirandomize
    experiment_dict['spec']['descriptor'] = descriptor
    if qubit_labels is not None: experiment_dict['qubitordering'] = tuple(qubit_labels)
    else: experiment_dict['qubitordering'] = tuple(pspec.qubit_labels)
    experiment_dict['circuits'] = {}
    experiment_dict['target'] = {}
    experiment_dict['germs'] = {}
    #experiment_dict['germ_powers'] = {}
    #experiment_dict['subgerm_depths'] = {}
    #experiment_dict['max_subgerm_depth'] = {}

    circlist = {}
    outlist = {}
    aux = {}
    for j in range(circuits_per_length):
        circlist[j], outlist[j], aux[j] = random_germpower_mirror_circuits(pspec, depths, qubit_labels=qubit_labels,
                                                                           localclifford=localclifford,
                                                                           paulirandomize=paulirandomize,
                                                                           interactingQs_density=samplerargs[0],
                                                                           fixed_versus_depth=fixed_versus_depth)

    #print(aux[0])
    #for l in depths:
    for lind in range(len(depths)):
        for j in range(circuits_per_length):
            #c, iout = random_germpower_mirror_circuit(pspec, l, qubit_labels=qubit_labels,
            #                            localclifford=localclifford, paulirandomize=paulirandomize,
            #                           interactingQs_density=samplerargs[0])
            #             experiment_dict['circuits'][l, j] = c
            #             experiment_dict['target'][l, j] = iout
            experiment_dict['circuits'][depths[lind], j] = circlist[j][lind]
            experiment_dict['target'][depths[lind], j] = outlist[j][lind]
            if fixed_versus_depth:
                experiment_dict['germs'][depths[lind], j] = aux[j]['germ']
            else:
                experiment_dict['germs'][depths[lind], j] = aux[j]['germ'][lind]
            #experiment_dict['germ_powers'][depths[lind], j] = aux[j]['germ_powers'][lind]
            #experiment_dict['subgerm_depths'][depths[lind], j] = aux[j]['subgerm_depth']
            #experiment_dict['max_subgerm_depth'][depths[lind], j] = aux[j]['max_subgerm_depth']

    return experiment_dict


# Future : possibly add this back in, but only if the other function it is a wrap-around
# for has been tested.
# def oneQ_generalized_rb_experiment(m_list, K_m, group_or_model, inverse=True,
#                               interleaved = None, alias_maps=None, seed=None,
#                               randState=None):
#     """
#     Makes a list of random RB sequences.

#     Parameters
#     ----------
#     m_list : list or array of ints
#         The set of depths for the random sequences (with the total
#         number of Cliffords in each sequence given by m_list + 1). Minimal
#         allowed length is therefore 1 (a random CLifford followed by its
#         inverse).

#     clifford_group : MatrixGroup
#         Which Clifford group to use.

#     K_m : int or dict
#         If an integer, the fixed number of Clifford sequences to be sampled at
#         each length m.  If a dictionary, then a mapping from Clifford
#         sequence length m to number of Cliffords to be sampled at that length.

#     alias_maps : dict of dicts, optional
#         If not None, a dictionary whose keys name other gate-label-sets, e.g.
#         "primitive" or "canonical", and whose values are "alias" dictionaries
#         which map the clifford labels (defined by `clifford_group`) to those
#         of the corresponding gate-label-set.  For example, the key "canonical"
#         might correspond to a dictionary "clifford_to_canonical" for which
#         (as one example) clifford_to_canonical['Gc1'] == ('Gy_pi2','Gy_pi2').

#     seed : int, optional
#         Seed for random number generator; optional.

#     randState : numpy.random.RandomState, optional
#         A RandomState object to generate samples from. Can be useful to set
#         instead of `seed` if you want reproducible distribution samples across
#         multiple random function calls but you don't want to bother with
#         manually incrementing seeds between those calls.

#     Returns
#     -------
#     dict or list
#         If `alias_maps` is not None, a dictionary of lists-of-circuit-lists
#         whose keys are 'clifford' and all of the keys of `alias_maps` (if any).
#         Values are lists of `Circuit` lists, one for each K_m value.  If
#         `alias_maps` is None, then just the list-of-lists corresponding to the
#         clifford operation labels is returned.
#     """

#     if randState is None:
#         rndm = _np.random.RandomState(seed) # ok if seed is None
#     else:
#         rndm = randState

#     assert hasattr(group_or_model, 'gates') or hasattr(group_or_model,
#            'product'), 'group_or_model must be a MatrixGroup or Model'


#     if inverse:
#         if hasattr(group_or_model, 'gates'):
#             group_or_model = _rbobjs.MatrixGroup(group_or_model.operations.values(),
#                                   group_or_model.operations.keys())
#     if isinstance(K_m,int):
#         K_m_dict = {m : K_m for m in m_list }
#     else: K_m_dict = K_m
#     assert hasattr(K_m_dict, 'keys'),'K_m must be a dict or int!'

#     string_lists = {'uncompiled': []} # Circuits with uncompiled labels
#     if alias_maps is not None:
#         for gstyp in alias_maps.keys(): string_lists[gstyp] = []

#     for m in m_list:
#         K = K_m_dict[m]
#         strs_for_this_m = [ create_random_circuit(m, group_or_model,
#             inverse=inverse,interleaved=interleaved,randState=rndm) for i in range(K) ]
#         string_lists['uncompiled'].append(strs_for_this_m)
#         if alias_maps is not None:
#             for gstyp,alias_map in alias_maps.items():
#                 string_lists[gstyp].append(
#                     _cnst.translate_circuit_list(strs_for_this_m,alias_map))

#     if alias_maps is None:
#         return string_lists['uncompiled'] #only list of lists is uncompiled one
#     else:
#         return string_lists #note we also return this if alias_maps == {}
