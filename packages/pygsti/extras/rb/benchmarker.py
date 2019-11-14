""" Encapsulates RB results and dataset objects """
from __future__ import division, print_function, absolute_import, unicode_literals
#***************************************************************************************************
# Copyright 2015, 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 or in the LICENSE file in the root pyGSTi directory.
#***************************************************************************************************

import numpy as _np
import copy as _copy
import warnings as _warnings
from itertools import cycle as _cycle
from . import analysis as _analysis
from . import dataset as _dataset
from ...objects import oplessmodel as _oplessmodel
from ...objects import dataset as _stdds
from ...objects import multidataset as _multids
from ...objects import datacomparator as _dcomp


class Benchmarker(object):
    """
    todo

    """
    def __init__(self, specs, ds=None, summary_data=None, predicted_summary_data=None,
                 dstype='standard', success_outcome='success', success_key='target',
                 dscomparator=None):
        """
        todo

        dstype : ('success-fail', 'standard')

        specs: dictionary of (name, RBSpec) key-value pairs. The names are arbitrary

        """
        if ds is not None:
            assert(dstype in ('success-fail', 'standard', 'dict')), "Unknown format for the dataset!"
            self.dstype = dstype
            if self.dstype == 'success-fail' or self.dstype == 'dict':
                self.success_outcome = success_outcome
            else:
                self.success_outcome = None
            if self.dstype == 'standard' or self.dstype == 'dict':
                self.success_key = success_key
            else:
                self.success_key = None

            if dstype == 'dict':
                assert('standard' in ds.keys() and 'success-fail' in ds.keys())
                self.multids = ds
            else:
                self.multids = {}
                if isinstance(ds, _stdds.DataSet):
                    self.multids[self.dstype] = _multids.MultiDataSet()
                    self.multids[self.dstype].add_dataset(0, ds)
                elif isinstance(ds, list):
                    self.multids[self.dstype] = _multids.MultiDataSet()
                    for i, subds in enumerate(ds):
                        self.multids[self.dstype].add_dataset(i, ds)
                elif isinstance(ds, _multids.MultiDataSet):
                    self.multids[self.dstype] = ds
                else:
                    raise ValueError("If specified, `ds` must be a DataSet, a list of DataSets,"
                                     + " a MultiDataSet or a dictionary of MultiDataSets!")

            self.numpasses = len(self.multids[list(self.multids.keys())[0]])
        else:
            assert(summary_data is not None), "Must specify one or more DataSets or a summary data dict!"
            self.multids = None
            self.success_outcome = None
            self.success_key = None
            self

        self.dscomparator = _copy.deepcopy(dscomparator)

        self._specs = tuple(specs.values())
        self._speckeys = tuple(specs.keys())

        if summary_data is None:
            self.pass_summary_data = {}
            self.global_summary_data = {}
            self.aux = {}
        else:
            assert(isinstance(summary_data, dict)), "The summary data must be a dictionary"
            self.pass_summary_data = summary_data['pass'].copy()
            self.global_summary_data = summary_data['global'].copy()
            self.aux = summary_data.get('aux', {}).copy()
            if self.multids is None:
                arbqubits =  self._specs[0].get_structure()[0]
                arbkey = list(self.pass_summary_data[0][arbqubits].keys())[0]
                arbdepth = list(self.pass_summary_data[0][arbqubits][arbkey].keys())[0]
                self.numpasses = len(self.pass_summary_data[0][arbqubits][arbkey][arbdepth])

        if predicted_summary_data is None:
            self.predicted_summary_data = {}
        else:
            self.predicted_summary_data = predicted_summary_data.copy()

    def get_volumetric_benchmark_data(self, depths, widths='all', datatype='success_probabilities', 
                                      statistic='mean', specs=None,  aggregate=True,  rescaler='auto'):

        assert(statistic in ('max', 'mean', 'min', 'dist'))

        if isinstance(widths, str):
            assert(widths == 'all')
        else:
            assert(isinstance(widths, list) or isinstance(widths, tuple))

        if specs is None:  # If we're not given a filter, we use all of the data.
            specs = {i: [qs for qs in spec.get_structure()] for i, spec in enumerate(self._specs)}

        width_to_spec = {}
        for i, structure in specs.items():
            for qs in structure:
                w = len(qs)
                if widths == 'all' or w in widths:
                    if w not in width_to_spec:
                        width_to_spec[w] = (i, qs)
                    else:
                        raise ValueError("There are multiple qubit subsets of size {} benchmarked! Cannot have specs as None!".format(w))

        if widths == 'all':
            widths = list(width_to_spec.keys())
            widths.sort()
        else:
            assert(set(widths) == set(list(width_to_spec.keys())))

        if isinstance(rescaler, str):
            if rescaler == 'auto':
                if datatype == 'success_probabilities': 
                    def rescale_function(data, width):
                        return list((_np.array(data) - 1 / 2**width) / (1 - 1 / 2**width))
                else:
                    def rescale_function(data, width):
                        return data
            elif rescale == 'none':
                
                def rescale_function(data, width):
                    return data

            else:
                raise ValueError("Unknown rescaling option!")

        else:
            rescale_function = rescaler

        # if samecircuitpredictions:
        #     predvb = {d: {} for d in depths}
        # else:
        #     predvb = None

        qs = self._specs[0].get_structure()[0]  # An arbitrary key 
        if datatype in self.pass_summary_data[0][qs].keys():
            datadict = self.pass_summary_data
            globaldata = False 
        elif datatype in self.global_summary_data[0][qs].keys():
            datadict = self.global_summary_data
            globaldata = True
        else:
            raise ValueError("Unknown datatype!")

        if aggregate or globaldata:
            vb = {d: {} for d in depths}
            fails = {d: {} for d in depths}
        else:
            vb = [{d: {} for d in depths} for i in range(self.numpasses)]
            fails = [{d: {} for d in depths} for i in range(self.numpasses)]

        if len(self.predicted_summary_data) > 0:
            arbkey = list(self.predicted_summary_data.keys())[0]
            dopredictions = datatype in self.predicted_summary_data[arbkey][0][qs].keys()
            if dopredictions:
                pkeys = self.predicted_summary_data.keys()
                predictedvb = {pkey: {d: {} for d in depths} for pkey in pkeys}
            else:
                predictedvb = {pkey: None for pkey in self.predicted_summary_data.keys()}

        for w in widths:
            (i, qs) = width_to_spec[w]
            data = datadict[i][qs][datatype]
            if dopredictions:
                preddata = {pkey: self.predicted_summary_data[pkey][i][qs][datatype] for pkey in pkeys}
            for d in depths:
                if d in data.keys():
                    
                    dline = data[d]
 
                    if globaldata:

                        failcount = _np.sum(_np.isnan(dline))
                        fails[d][w] = (len(dline) - failcount, failcount)

                        if statistic == 'dist':
                            vb[d][w] = rescale_function(dline, w)
                        else:
                            if not _np.isnan(rescale_function(dline, w)).all():
                                if statistic == 'max':
                                    vb[d][w] = _np.nanmax(rescale_function(dline,w))
                                elif statistic == 'mean':
                                    vb[d][w] = _np.nanmean(rescale_function(dline,w))
                                elif statistic == 'min':
                                    vb[d][w] = _np.nanmin(rescale_function(dline,w))
                            else:
                                vb[d][w] = _np.nan

                    else:
                        failline = [(len(dpass) - _np.sum(_np.isnan(dpass)), _np.sum(_np.isnan(dpass))) for dpass in dline]

                        if statistic == 'max':
                            vbdataline = [_np.nanmax(rescale_function(dpass,w)) if not _np.isnan(rescale_function(dpass,w)).all() else _np.nan for dpass in dline]
                        elif statistic == 'mean':
                            vbdataline = [_np.nanmean(rescale_function(dpass,w)) if not _np.isnan(rescale_function(dpass,w)).all() else _np.nan for dpass in dline]
                        elif statistic == 'min':
                            vbdataline = [_np.nanmin(rescale_function(dpass,w)) if not _np.isnan(rescale_function(dpass,w)).all() else _np.nan for dpass in dline]
                        elif statistic == 'dist':
                            vbdataline = [rescale_function(dpass, w) for dpass in dline]

                        if not aggregate:
                            for i in range(len(vb)):
                                vb[i][d][w] = vbdataline[i]
                                fails[i][d][w] = failline[i]

                        if aggregate:

                            successcount = 0
                            failcount = 0
                            for (successcountpass, failcountpass) in failline:
                                successcount += successcountpass
                                failcount += failcountpass
                                fails[d][w] = (successcount, failcount)

                            if statistic == 'dist':
                                vb[d][w] = [item for sublist in vbdataline for item in sublist]
                            else:
                                if not _np.isnan(vbdataline).all():
                                    if statistic == 'max':
                                        vb[d][w] = _np.nanmax(vbdataline)
                                    elif statistic == 'mean':
                                        vb[d][w] = _np.nanmean(vbdataline)
                                    elif statistic == 'min':
                                        vb[d][w] = _np.nanmin(vbdataline)
                                else:
                                    vb[d][w] = _np.nan

                    # Repeat the process for the predictions, but with simpler code as don't have to deal with passes or NaNs.
                    if dopredictions:
                        pdline = {pkey: preddata[pkey][d] for pkey in pkeys}
                        for pkey in pkeys:
                            if statistic == 'dist':
                                predictedvb[pkey][d][w] = rescale_function(pdline[pkey], w)
                            if statistic == 'max':
                                predictedvb[pkey][d][w] = _np.max(rescale_function(pdline[pkey], w))
                            if statistic == 'mean':
                                predictedvb[pkey][d][w] = _np.mean(rescale_function(pdline[pkey], w))
                            if statistic == 'min':
                                predictedvb[pkey][d][w] = _np.min(rescale_function(pdline[pkey], w))

        out = {'data': vb, 'fails': fails, 'predictions': predictedvb}
        
        return out
       

    def get_flattened_data(self, specs=None, aggregate=True):

        flattened_data = {}

        if specs is None:
            specs = self.filter_experiments()

        qubits = self._specs[0].get_structure()[0]  # An arbitrary key in the dict of the summary data.
        if aggregate:
            flattened_data = {dtype: [] for dtype in self.pass_summary_data[0][qubits].keys()}
        else:
            flattened_data = {dtype: [[] for i in range(self.numpasses)] for dtype in self.pass_summary_data[0][qubits].keys()}
        flattened_data.update({dtype: [] for dtype in self.global_summary_data[0][qubits].keys()})
        flattened_data.update({dtype: [] for dtype in self.aux[0][qubits].keys()})
        flattened_data.update({'predictions':{pkey: {'success_probabilities': []} for pkey in self.predicted_summary_data.keys()}})

        for specind, structure in specs.items():
            for qubits in structure:
                for dtype, data in self.pass_summary_data[specind][qubits].items():
                    for depth, dataline in data.items():
                        #print(specind, qubits, dtype, depth)
                        if aggregate:
                            aggregatedata = _np.array(dataline[0])
                            # print(aggregatedata)
                            # print(type(aggregatedata))
                            # print(type(aggregatedata[0]))
                            for i in range(1, self.numpasses):
                                # print(dataline[i])
                                # print(type(dataline[i]))
                                # print(type(dataline[i][0]))
                                aggregatedata = aggregatedata + _np.array(dataline[i])
                            flattened_data[dtype] += list(aggregatedata)
                        else:
                            for i in range(self.numpasses):
                                flattened_data[dtype][i] += dataline[i]

                for dtype, data in self.global_summary_data[specind][qubits].items():
                    for depth, dataline in data.items():
                        flattened_data[dtype] += dataline
                for dtype, data in self.aux[specind][qubits].items():
                    for depth, dataline in data.items():
                        flattened_data[dtype] += dataline
                for pkey in self.predicted_summary_data.keys():
                    if 'success_probabilities' in self.predicted_summary_data[pkey][specind][qubits].keys():
                        for depth, dataline in self.predicted_summary_data[pkey][specind][qubits]['success_probabilities'].items():
                            flattened_data['predictions'][pkey]['success_probabilities'] += dataline
                    else:
                        for (depth, dataline1), dataline2 in zip(self.predicted_summary_data[pkey][specind][qubits]['success_counts'].items(), 
                                                               self.predicted_summary_data[pkey][specind][qubits]['total_counts'].values()):
                            flattened_data['predictions'][pkey]['success_probabilities'] += list(_np.array(dataline1) / _np.array(dataline2))

        #  Only do this if we've not already stored the success probabilities in the benchamrker.
        if ('success_counts' in flattened_data) and ('total_counts' in flattened_data) and ('success_probabilities' not in flattened_data):
            if aggregate:
                flattened_data['success_probabilities'] = [sc / tc if tc > 0 else _np.nan for sc, tc in zip(flattened_data['success_counts'], flattened_data['total_counts'])]
            else:
                flattened_data['success_probabilities'] = [[sc / tc if tc > 0 else _np.nan for sc, tc in zip(scpass, tcpass)] for scpass, tcpass in zip(flattened_data['success_counts'], flattened_data['total_counts'])]

        return flattened_data

    def test_pass_stability(self, formatdata=False, verbosity=1):

        assert(self.multids is not None), "Can only run the stability analysis if a MultiDataSet is contained in this Benchmarker!"

        if not formatdata:
            assert('success-fail' in self.multids.keys()), "Must have generated/imported a success-fail format DataSet!"
        else:
            if 'success-fail' not in self.multids.keys():
                if verbosity > 0:
                    print("No success/fail dataset found, so first creating this dataset from the full data...", end='')
                self.generate_success_or_fail_dataset()
                if verbosity > 0:
                    print("complete.")

        if len(self.multids['success-fail']) > 1:
            self.dscomparator = _dcomp.DataComparator(self.multids['success-fail'], allow_bad_circuits=True)
            self.dscomparator.implement(verbosity=verbosity)

    def generate_success_or_fail_dataset(self, overwrite=False):
        """
        """

        assert('standard' in self.multids.keys())
        if not overwrite:
            assert('success-fail' not in self.multids.keys())

        sfmultids = _multids.MultiDataSet()

        for ds_ind, ds in self.multids['standard'].items():
            sfds = _stdds.DataSet(outcomeLabels=['success', 'fail'], collisionAction=ds.collisionAction)
            for circ, dsrow in ds.items(stripOccurrenceTags=True):
                scounts = dsrow[ dsrow.aux[self.success_key] ]
                tcounts = dsrow.total
                sfds.add_count_dict(circ, {'success': scounts, 'fail': tcounts - scounts}, aux=dsrow.aux)

            sfds.done_adding_data()
            sfmultids.add_dataset(ds_ind, sfds)

        self.multids['success-fail'] = sfmultids

    # def get_all_data(self):

    #     for circ 

    def get_summary_data(self, datatype, specindex, qubits=None):

        spec = self._specs[specindex]
        structure = spec.get_structure()
        if len(structure) == 1:
            if qubits is None:
                qubits = structure[0]

        assert(qubits in structure), "Invalid choice of qubits for this spec!"

        return self.pass_summary_data[specindex][qubits][datatype]

    #def getauxillary_data(self, datatype, specindex, qubits=None):

    #def get_predicted_summary_data(self, prediction, datatype, specindex, qubits=None):


    def create_summary_data(self, predictions={}, verbosity=2, auxtypes=[]):
        """
        todo
        """
        assert(self.multids is not None), "Cannot generate summary data without a DataSet!"
        assert('standard' in self.multids.keys()), "Currently only works for standard dataset!"
        useds = 'standard'
        # We can't use the success-fail dataset if there's any simultaneous benchmarking. Not in
        # it's current format anyway.

        summarydata = {}
        aux = {}
        globalsummarydata = {}
        predsummarydata = {}
        predds = None
        preddskey = None
        for pkey in predictions.keys():
            predsummarydata[pkey] = {}
            if isinstance(predictions[pkey], _stdds.DataSet):
                assert(predds is None), "Can't have two DataSet predictions!"
                predds = predictions[pkey]
                preddskey = pkey
            else:
                assert(isinstance(predictions[pkey], _oplessmodel.SuccessFailModel)), "If not a DataSet must be an ErrorRatesModel!"

        datatypes = ['success_counts', 'total_counts', 'hamming_distance_counts', 'success_probabilities']
        if self.dscomparator is not None:
            stabdatatypes = ['tvds', 'pvals', 'jsds', 'llrs', 'sstvds']
        else:
            stabdatatypes = []

        #preddtypes = ('success_probabilities', )
        auxtypes = ['twoQgate_count', 'depth', 'target', 'width', 'circuit_index'] + auxtypes

        def get_datatype(datatype, dsrow, circ, target, qubits):

            if datatype == 'success_counts':
                return _analysis.marginalized_success_counts(dsrow, circ, target, qubits)
            elif datatype == 'total_counts':
                return dsrow.total
            elif datatype == 'hamming_distance_counts':
                return _analysis.marginalized_hamming_distance_counts(dsrow, circ, target, qubits)
            elif datatype == 'success_probabilities':
                sc = _analysis.marginalized_success_counts(dsrow, circ, target, qubits)
                tc = dsrow.total
                if tc == 0:
                    return _np.nan
                else:
                    return sc / tc 
            else:
                raise ValueError("Unknown data type!")

        numpasses = len(self.multids[useds].keys())

        for ds_ind in self.multids[useds].keys():

            if verbosity > 0:
                print(" - Processing data from pass {} of {}. Percent complete:".format(ds_ind + 1, len(self.multids[useds])))
   
            #circuits = {}
            numcircuits = len(self.multids[useds][ds_ind].keys())
            percent = 0

            if preddskey is None or ds_ind > 0:
                iterator = zip(self.multids[useds][ds_ind].items(stripOccurrenceTags=True),
                               self.multids[useds].auxInfo.values(), _cycle(zip([None, ], [None, ])))
            else:
                iterator = zip(self.multids[useds][ds_ind].items(stripOccurrenceTags=True),
                               self.multids[useds].auxInfo.values(),
                               predds.items(stripOccurrenceTags=True))

            for i, ((circ, dsrow), auxdict, (pcirc, pdsrow)) in enumerate(iterator):

                if pcirc is not None:
                    if not circ == pcirc:
                        print('-{}-'.format(i))
                        pdsrow = predds[circ]
                        _warnings.warn("Predicted DataSet is ordered differently to the main DataSet!"
                                       + "Reverting to potentially slow dictionary hashing!")

                if verbosity > 0:
                    if _np.floor(100 * i / numcircuits) >= percent:
                        percent += 1
                        if percent in (1, 26, 51, 76):
                            print("\n    {},".format(percent), end='')
                        else:
                            print("{},".format(percent), end='')
                        if percent == 100:
                            print('')

                speckeys = auxdict['spec']
                try:
                    depth = auxdict['depth']
                except:
                    depth = auxdict['length']
                target = auxdict['target']

                if isinstance(speckeys, str):
                    speckeys = [speckeys]

                for speckey in speckeys:
                    specind = self._speckeys.index(speckey)
                    spec = self._specs[specind]
                    structure = spec.get_structure()

                    # If we've not yet encountered this specind, we create the required dictionaries to store the
                    # summary data from the circuits associated with that spec.
                    if specind not in summarydata.keys():

                        assert(ds_ind == 0)
                        summarydata[specind] = {qubits: {datatype: {} for datatype in datatypes} for qubits in structure}
                        aux[specind] = {qubits: {auxtype: {} for auxtype in auxtypes} for qubits in structure}

                        # Only do predictions on the first pass dataset.
                        for pkey in predictions.keys():
                            predsummarydata[pkey][specind] = {}
                            for pkey in predictions.keys():
                                if pkey == preddskey:
                                    predsummarydata[pkey][specind] = {qubits: {datatype: {} for datatype in datatypes} for qubits in structure}
                                else:
                                    predsummarydata[pkey][specind] = {qubits: {'success_probabilities': {}} for qubits in structure}

                        globalsummarydata[specind] = {qubits: {datatype: {} for datatype in stabdatatypes} for qubits in structure}

                    # If we've not yet encountered this depth, we create the list where the data for that depth
                    # is stored.
                    for qubits in structure:
                        if depth not in summarydata[specind][qubits][datatypes[0]].keys():

                            assert(ds_ind == 0)
                            for datatype in datatypes:
                                summarydata[specind][qubits][datatype][depth] = [[] for i in range(numpasses)]
                            for auxtype in auxtypes:
                                aux[specind][qubits][auxtype][depth] = []

                            for pkey in predictions.keys():
                                if pkey == preddskey:
                                    for datatype in datatypes:
                                        predsummarydata[pkey][specind][qubits][datatype][depth] = []
                                else:
                                    predsummarydata[pkey][specind][qubits]['success_probabilities'][depth] = []

                            for datatype in stabdatatypes:
                                globalsummarydata[specind][qubits][datatype][depth] = []

                    for qubits_ind, qubits in enumerate(structure):
                        for datatype in datatypes:
                            x = get_datatype(datatype, dsrow, circ, target, qubits)
                            summarydata[specind][qubits][datatype][depth][ds_ind].append(x)
                            # Only do predictions on the first pass dataset.
                            if preddskey is not None and ds_ind == 0:
                                x = get_datatype(datatype, pdsrow, circ, target, qubits)
                                predsummarydata[preddskey][specind][qubits][datatype][depth].append(x)

                        # Only do predictions and aux on the first pass dataset.
                        if ds_ind == 0:
                            for auxtype in auxtypes:
                                if auxtype == 'twoQgate_count':
                                    auxdata = circ.twoQgate_count()
                                elif auxtype == 'depth':
                                    auxdata = circ.depth()
                                elif auxtype == 'target':
                                    auxdata = target
                                elif auxtype == 'circuit_index':
                                    auxdata = i
                                elif auxtype == 'width':
                                    auxdata = len(qubits)
                                else:
                                    auxdata = auxdict.get(auxtype, None)

                                aux[specind][qubits][auxtype][depth].append(auxdata)

                            for pkey, predmodel in predictions.items():
                                if pkey != preddskey:
                                    if set(circ.line_labels) != set(qubits):
                                        trimmedcirc = circ.copy(editable=True)
                                        for q in circ.line_labels:
                                            if q not in qubits:
                                                trimmedcirc.delete_lines(q)
                                    else:
                                        trimmedcirc = circ

                                    predsp = predmodel.probs(trimmedcirc)[('success',)]
                                    predsummarydata[pkey][specind][qubits]['success_probabilities'][depth].append(predsp)

                            for datatype in stabdatatypes:
                                if datatype == 'tvds':
                                    x = self.dscomparator.tvds.get(circ, _np.nan)
                                elif datatype == 'pvals':
                                    x = self.dscomparator.pVals.get(circ, _np.nan)
                                elif datatype == 'jsds':
                                    x = self.dscomparator.jsds.get(circ, _np.nan)
                                elif datatype == 'llrs':
                                    x = self.dscomparator.llrs.get(circ, _np.nan)
                                globalsummarydata[specind][qubits][datatype][depth].append(x)

            if verbosity > 0:
                print('')

        #  Record the data in the object at the end.
        self.predicted_summary_data = predsummarydata
        self.pass_summary_data = summarydata
        self.global_summary_data = globalsummarydata
        self.aux = aux

    # def create_summary_data(self, datatype='adjusted', addaux=True, storecircuits=False, predictions={}, verbosity=2):
    #     """

    #     """
    #     # if method == 'simple':
    #     #     if specindices is None:
    #     #         specindices = range(len(self._specs))

    #     #     for specind in specindices:
    #     #         spec = self._specs[specind]

    #     #         if specind not in self._summary_data.keys():

    #     #             if verbosity > 0:
    #     #                 print(" - Creating summary data {} of {} ...".format(specind + 1, len(specindices)), end='')
    #     #             if verbosity > 1: print("")

    #     #             if addaux:
    #     #                 raise NotImplementedError("The slow version of this function does"
    #     #                                           + "not allow adding aux currently!")
    #     #             if storecircuits:
    #     #                 raise NotImplementedError("The slow version of this function does"
    #     #                                           + "not allow storing the circuits!")

    #     #             if len(predictions) > 0:
    #     #                 raise NotImplementedError("The slow version of this function does"
    #     #                                           + "not allow error rate predictions!")

    #     #             self._summary_data[specind] = _dataset.create_summary_datasets(self.ds, spec, datatype=datatype,
    #     #                                                                            verbosity=verbosity)

    #     #             if verbosity == 1: print("complete.")

    #     #         else:
    #     #             if verbosity > 0:
    #     #                 print(" - Summary data already extant for {} of {}".format(specind + 1, len(specindices)))

    #     #elif method == 'fast':
    #     #    assert(specindices is None), "The 'fast' method cannot format a subset of the data!"

    #     predsummarydata = {}
    #     predds = None
    #     preddskey = None
    #     for pkey in predictions.keys():
    #         predsummarydata[pkey] = {}
    #         if isinstance(predictions[pkey], _stdds.DataSet):
    #             assert(predds is None), "Can't have two DataSet predictions!"
    #             predds = predictions[pkey]
    #             preddskey = pkey
    #         else:
    #             assert(isinstance(predictions[pkey], _erm.ErrorRatesModel)), "If not a DataSet must be an ErrorRatesModel!"

    #     for ds_ind in self.multids.keys():

    #         summarydata = {}
    #         aux = {}
    #         circuits = {}
    #         numcircuits = len(self.multids[ds_ind].keys())
    #         percent = 0

    #         if preddskey is None:
    #             for i, ((circ, dsrow), (auxcirc, auxdict)) in enumerate(zip(self.multids[ds_ind].items(), self.multids.auxInfo.items())):

    #                 assert(circ == auxcirc)
    #                 #print(i, end=',')
    #                 if verbosity > 0:
    #                     if _np.floor(100 * i / numcircuits) >= percent:
    #                         percent += 1
    #                         print("{} percent complete".format(percent))

    #                 # specindices = self.ds.auxInfo[circ]['specindices']
    #                 # length = self.ds.auxInfo[circ]['length']
    #                 # target = self.ds.auxInfo[circ]['target']
    #                 speckeys = auxdict['spec']
    #                 length = auxdict['length']
    #                 target = auxdict['target']
    #                 if isinstance(speckeys, str):
    #                     speckeys = [speckeys]

    #                 for speckey in speckeys:
    #                     specind = self._speckeys.index(speckey)
    #                     spec = self._specs[specind]
    #                     structure = spec.get_structure()

    #                     if specind not in summarydata.keys():

    #                         summarydata[specind] = {}
    #                         aux[specind] = {}
    #                         if storecircuits:
    #                             circuits[specind] = {}
    #                         else:
    #                             circuits[specind] = None

    #                         for pkey in predictions.keys():
    #                             predsummarydata[pkey][specind] = {}

    #                         for qubits in structure:
    #                             summarydata[specind][qubits] = {}
    #                             summarydata[specind][qubits]['success_counts'] = {}
    #                             summarydata[specind][qubits]['total_counts'] = {}
    #                             summarydata[specind][qubits]['hamming_distance_counts'] = {}
    #                             aux[specind][qubits] = {}
    #                             if addaux:
    #                                 aux[specind][qubits]['twoQgate_count'] = {}
    #                                 aux[specind][qubits]['depth'] = {}
    #                                 aux[specind][qubits]['target'] = {}
    #                             for pkey in predictions.keys():
    #                                 predsummarydata[pkey][specind][qubits] = {}
    #                                 predsummarydata[pkey][specind][qubits]['success_probabilities'] = {}

    #                     for qubits in structure:
    #                         if length not in summarydata[specind][qubits]['success_counts'].keys():
    #                             summarydata[specind][qubits]['success_counts'][length] = []
    #                             summarydata[specind][qubits]['total_counts'][length] = []
    #                             summarydata[specind][qubits]['hamming_distance_counts'][length] = []
    #                             if addaux:
    #                                 aux[specind][qubits]['twoQgate_count'][length] = []
    #                                 aux[specind][qubits]['depth'][length] = []
    #                                 aux[specind][qubits]['target'][length] = []
    #                             if storecircuits:
    #                                 circuits[specind][length] = []
    #                             for pkey in predictions.keys():
    #                                 predsummarydata[pkey][specind][qubits]['success_probabilities'][length] = []

    #                     #dsrow = self.ds[circ]
    #                     for qubits_ind, qubits in enumerate(structure):
    #                         if datatype == 'raw':
    #                             summarydata[specind][qubits]['success_counts'][length].append(_analysis.marginalized_success_counts(dsrow, circ, target, qubits))
    #                             summarydata[specind][qubits]['total_counts'][length].append(dsrow.total)
    #                         elif datatype == 'adjusted':
    #                             summarydata[specind][qubits]['hamming_distance_counts'][length].append(_analysis.marginalized_hamming_distance_counts(dsrow, circ, target, qubits))

    #                         if addaux:
    #                             aux[specind][qubits]['twoQgate_count'][length].append(circ.twoQgate_count())
    #                             aux[specind][qubits]['depth'][length].append(circ.depth())
    #                             aux[specind][qubits]['target'][length].append(target)                            
    #                         if storecircuits and qubits_ind == 0:
    #                             circuits[specind][length].append(circ)
    #                         for pkey, predmodel in predictions.items():
    #                             if pkey != preddskey:
    #                                 if set(circ.line_labels) != set(qubits):
    #                                     trimmedcirc = circ.copy(editable=True)
    #                                     for q in circ.line_labels:
    #                                         if q not in qubits:
    #                                             trimmedcirc.delete_lines(q)
    #                                 else:
    #                                     trimmedcirc = circ
    #                                 predsp = predmodel.success_prob(trimmedcirc)
    #                                 predsummarydata[pkey][specind][qubits]['success_probabilities'][length].append(predsp)

    #         elif preddskey is not None:
    #             assert(False), "This part of the code needs fixing for multi-pass data!"
                
    #         #     for i, ((circ, dsrow), (auxcirc, auxdict), (pcirc, pdsrow)) in enumerate(zip(self.ds.items(), self.ds.auxInfo.items(), predds.items())):

    #         #         assert(circ == auxcirc)
    #         #         if not circ == pcirc:
    #         #             pdsrow = predds[circ]
    #         #             print("Predicted DataSet is ordered differently to the main DataSet! Reverting to potentially slow dictionary hashing!")
    #         #         #print(i, end=',')
    #         #         if verbosity > 0:
    #         #             if _np.floor(100 * i / numcircuits) >= percent:
    #         #                 percent += 1
    #         #                 print("{} percent complete".format(percent))

    #         #         # specindices = self.ds.auxInfo[circ]['specindices']
    #         #         # length = self.ds.auxInfo[circ]['length']
    #         #         # target = self.ds.auxInfo[circ]['target']
    #         #         specindices = auxdict['specindices']
    #         #         length = auxdict['length']
    #         #         target = auxdict['target']

    #         #         for specind in specindices:
    #         #             spec = self._specs[specind]
    #         #             structure = spec.get_structure()

    #         #             if specind not in summarydata.keys():

    #         #                 summarydata[specind] = {}
    #         #                 aux[specind] = {}
    #         #                 if storecircuits:
    #         #                     circuits[specind] = {}
    #         #                 else:
    #         #                     circuits[specind] = None

    #         #                 for pkey in predictions.keys():
    #         #                     predsummarydata[pkey][specind] = {}

    #         #                 for qubits in structure:
    #         #                     summarydata[specind][qubits] = {}
    #         #                     summarydata[specind][qubits]['success_counts'] = {}
    #         #                     summarydata[specind][qubits]['total_counts'] = {}
    #         #                     summarydata[specind][qubits]['hamming_distance_counts'] = {}
    #         #                     aux[specind][qubits] = {}
    #         #                     if addaux:
    #         #                         aux[specind][qubits]['twoQgate_count'] = {}
    #         #                         aux[specind][qubits]['depth'] = {}
    #         #                         aux[specind][qubits]['target'] = {}

    #         #                     for pkey in predictions.keys():
    #         #                         predsummarydata[pkey][specind][qubits] = {}
    #         #                         if pkey != preddskey:
    #         #                             predsummarydata[pkey][specind][qubits]['success_probabilities'] = {}
    #         #                         else:
    #         #                             predsummarydata[pkey][specind][qubits]['success_counts'] = {}
    #         #                             predsummarydata[pkey][specind][qubits]['total_counts'] = {}
    #         #                             predsummarydata[pkey][specind][qubits]['hamming_distance_counts'] = {}

    #         #             for qubits in structure:
    #         #                 if length not in summarydata[specind][qubits]['success_counts'].keys():
    #         #                     summarydata[specind][qubits]['success_counts'][length] = []
    #         #                     summarydata[specind][qubits]['total_counts'][length] = []
    #         #                     summarydata[specind][qubits]['hamming_distance_counts'][length] = []
    #         #                     if addaux:
    #         #                         aux[specind][qubits]['twoQgate_count'][length] = []
    #         #                         aux[specind][qubits]['depth'][length] = []
    #         #                         aux[specind][qubits]['target'][length] = []
    #         #                     if storecircuits:
    #         #                         circuit[specind][length] = []
    #         #                     for pkey in predictions.keys():
    #         #                         if pkey != preddskey:
    #         #                             predsummarydata[pkey][specind][qubits]['success_probabilities'][length] = []
    #         #                         else:
    #         #                             predsummarydata[pkey][specind][qubits]['success_counts'][length] = []
    #         #                             predsummarydata[pkey][specind][qubits]['total_counts'][length] = []
    #         #                             predsummarydata[pkey][specind][qubits]['hamming_distance_counts'][length] = []

    #         #             #dsrow = self.ds[circ]
    #         #             for qubits_ind, qubits in enumerate(structure):
    #         #                 if datatype == 'raw':
    #         #                     summarydata[specind][qubits]['success_counts'][length].append(_analysis.marginalized_success_counts(dsrow, circ, target, qubits))
    #         #                     summarydata[specind][qubits]['total_counts'][length].append(dsrow.total)
    #         #                     predsummarydata[preddskey][specind][qubits]['success_counts'][length].append(_analysis.marginalized_success_counts(pdsrow, circ, target, qubits))
    #         #                     predsummarydata[preddskey][specind][qubits]['total_counts'][length].append(pdsrow.total)
    #         #                 elif datatype == 'adjusted':
    #         #                     summarydata[specind][qubits]['hamming_distance_counts'][length].append(_analysis.marginalized_hamming_distance_counts(dsrow, circ, target, qubits))
    #         #                     predsummarydata[preddskey][specind][qubits]['hamming_distance_counts'][length].append(_analysis.marginalized_hamming_distance_counts(pdsrow, circ, target, qubits))

    #         #                 if addaux:
    #         #                     aux[specind][qubits]['twoQgate_count'][length].append(circ.twoQgate_count())
    #         #                     aux[specind][qubits]['depth'][length].append(circ.depth())
    #         #                     aux[specind][qubits]['target'][length].append(target)
    #         #                 if storecircuits and qubits_ind == 0:
    #         #                     circuit[specind][length].append(circ)
    #         #                 for pkey, predmodel in predictions.items():
    #         #                     if pkey != preddskey:
    #         #                         if set(circ.line_labels) != set(qubits):
    #         #                             trimmedcirc = circ.copy(editable=True)
    #         #                             for q in circ.line_labels:
    #         #                                 if q not in qubits:
    #         #                                     trimmedcirc.delete_lines(q)
    #         #                         else:
    #         #                             trimmedcirc = circ
    #         #                         predsp = predmodel.success_prob(trimmedcirc)
    #         #                         predsummarydata[pkey][specind][qubits]['success_probabilities'][length].append(predsp)


    #         # if error_rates_model is not None:
    #         #     ermtype = error_rates_model.get_model_type()
    #         #     self.predicted_summary_data[ermtype] = {}

    #         print(summarydata.keys())

    #         for pkey in predictions.keys():
    #             self.predicted_summary_data[pkey] = {}

    #         for specind in summarydata.keys():
    #             spec = self._specs[specind]
    #             if storecircuits:
    #                 spec.add_circuits(circuits[specind])
    #             structure = spec.get_structure()
    #             if specind not in self._summary_data.keys():
    #                 self._summary_data[specind] = {}
    #             for pkey in predictions.keys():
    #                 self.predicted_summary_data[pkey][specind] = {}
    #             for qubits in structure:
    #                 if datatype == 'raw':
    #                     summarydata[specind][qubits]['hamming_distance_counts'] = None
    #                 elif datatype == 'adjusted':
    #                     summarydata[specind][qubits]['success_counts'] = None
    #                     summarydata[specind][qubits]['total_counts'] = None
    #                 if preddskey is not None:
    #                     if datatype == 'raw':
    #                         predsummarydata[preddskey][specind][qubits]['hamming_distance_counts'] = None
    #                     elif datatype == 'adjusted':
    #                         predsummarydata[preddskey][specind][qubits]['success_counts'] = None
    #                         predsummarydata[preddskey][specind][qubits]['total_counts'] = None

    #                 if qubits not in self._summary_data[specind].keys():
    #                     self._summary_data[specind][qubits] = {}
                    
    #                 self._summary_data[specind][qubits][ds_ind] = _dataset.RBSummaryDataset(len(qubits), success_counts=summarydata[specind][qubits]['success_counts'],
    #                                             total_counts=summarydata[specind][qubits]['total_counts'],
    #                                             hamming_distance_counts=summarydata[specind][qubits]['hamming_distance_counts'],
    #                                             aux=aux[specind][qubits])

    #                 for pkey in predictions.keys():
    #                     if pkey != preddskey:
    #                         self.predicted_summary_data[pkey][specind][qubits] = _dataset.RBSummaryDataset(len(qubits), success_counts=predsummarydata[pkey][specind][qubits]['success_probabilities'],
    #                                                 total_counts=None, hamming_distance_counts=None, finitecounts=False, aux=aux[specind][qubits])
    #                     else:    
    #                         self.predicted_summary_data[pkey][specind][qubits] = _dataset.RBSummaryDataset(len(qubits), success_counts=predsummarydata[pkey][specind][qubits]['success_counts'],
    #                                                 total_counts=predsummarydata[pkey][specind][qubits]['total_counts'],
    #                                                 hamming_distance_counts=predsummarydata[pkey][specind][qubits]['hamming_distance_counts'],
    #                                                 aux=aux[specind][qubits])

        #else:
            #    raise ValueError("Input `method` must be 'fast' or 'simple'!")

    def analyze(self, specindices=None, analysis='adjusted', bootstraps=200, verbosity=1):
        """
        todo

        todo: this partly ignores specindices
        """
        #self.create_summary_data(specindices=specindices, datatype=analysis, verbosity=verbosity)

        for i, rbdatadict in self._summary_data.items():
            #if not isinstance(rbdata, dict):
            #    self._rbresults[i] = rb.analysis.std_practice_analysis(rbdata)
            #else:
            #self._rbresults[i] = {}
            #for key in rbdata.items():
            if verbosity > 0:
                print('- Running analysis for {} of {}'.format(i, len(self._summary_data)))
            self._rbresults['adjusted'][i] = {}
            self._rbresults['raw'][i] = {}
            for j, (key, rbdata) in enumerate(rbdatadict.items()):
                if verbosity > 1:
                    print('   - Running analysis for qubits {} ({} of {})'.format(key, j, len(rbdatadict)))
                if analysis == 'all' or analysis == 'raw':
                    self._rbresults['raw'][i][key] = _analysis.std_practice_analysis(rbdata, bootstrap_samples=bootstraps, datatype='raw')
                if (analysis == 'all' and rbdata.datatype == 'hamming_distance_counts') or analysis == 'adjusted':
                    self._rbresults['adjusted'][i][key] = _analysis.std_practice_analysis(rbdata, bootstrap_samples=bootstraps, datatype='adjusted')

    def filter_experiments(self, numqubits=None, containqubits=None, onqubits=None, sampler=None,
                           twoQgateprob=None, prefilter=None, benchmarktype=None):
        """
        todo

        """

        kept = {}
        for i, spec in enumerate(self._specs):
            structures = spec.get_structure()
            for qubits in structures:

                keep = True

                if keep:
                    if benchmarktype is not None:
                        if spec.type != benchmarktype:
                            keep = False

                if keep:
                    if numqubits is not None:
                        if len(qubits) != numqubits:
                            keep = False

                if keep:
                    if containqubits is not None:
                        if not set(containqubits).issubset(qubits):
                            keep = False

                if keep:
                    if onqubits is not None:
                        if set(qubits) != set(onqubits):
                            keep = False

                if keep:
                    if sampler is not None:
                        if not spec._sampler == sampler:
                            keep = False

                if keep:
                    if twoQgateprob is not None:
                        if not _np.allclose(twoQgateprob, spec.get_twoQgate_rate()):
                            keep = False

                if keep:
                    if i not in kept.keys():
                        kept[i] = []
                    kept[i].append(qubits)

        if prefilter is not None:
            dellist = []
            for key in kept.keys():
                if key not in prefilter.keys():
                    dellist.append(key)
                else:
                    newlist = []
                    for qubits in kept[key]:
                        if qubits in prefilter[key]:
                            newlist.append(qubits)
                    if len(newlist) == 0:
                        dellist.append(key)
                    else:
                        kept[key] = newlist

            for key in dellist:
                del kept[key]

        return kept

        # for i, rbdata in self._adjusted_summary_data.items():
        #     #if not isinstance(rbdata, dict):
        #     #    self._rbresults[i] = rb.analysis.std_practice_analysis(rbdata)
        #     #else:
        #     #self._rbresults[i] = {}
        #     #for key in rbdata.items():
        #     self._adjusted_rbresults[i] = rb.analysis.std_practice_analysis(rbdata, bootstrap_samples=0, 
        #                                                                     asymptote=1/4**rbdata.number_of_qubits)


# class RBResults(object):
#     """
#     An object to contain the results of an RB analysis
#     """

#     def __init__(self, data, rtype, fits):
#         """
#         Initialize an RBResults object.

#         Parameters
#         ----------
#         data : RBSummaryDataset
#             The RB summary data that the analysis was performed for.

#         rtype : {'IE','AGI'}
#             The type of RB error rate, corresponding to different dimension-dependent
#             re-scalings of (1-p), where p is the RB decay constant in A + B*p^m.

#         fits : dict
#             A dictionary containing FitResults objects, obtained from one or more
#             fits of the data (e.g., a fit with all A, B and p as free parameters and
#             a fit with A fixed to 1/2^n).
#         """
#         self.data = data
#         self.rtype = rtype
#         self.fits = fits

#     def plot(self, fitkey=None, decay=True, success_probabilities=True, size=(8, 5), ylim=None, xlim=None,
#              legend=True, title=None, figpath=None):
#         """
#         Plots RB data and, optionally, a fitted exponential decay.

#         Parameters
#         ----------
#         fitkey : dict key, optional
#             The key of the self.fits dictionary to plot the fit for. If None, will
#             look for a 'full' key (the key for a full fit to A + Bp^m if the standard
#             analysis functions are used) and plot this if possible. It otherwise checks
#             that there is only one key in the dict and defaults to this. If there are
#             multiple keys and none of them are 'full', `fitkey` must be specified when
#             `decay` is True.

#         decay : bool, optional
#             Whether to plot a fit, or just the data.

#         success_probabilities : bool, optional
#             Whether to plot the success probabilities distribution, as a violin plot. (as well
#             as the *average* success probabilities at each length).

#         size : tuple, optional
#             The figure size

#         ylim, xlim : tuple, optional
#             The x and y limits for the figure.

#         legend : bool, optional
#             Whether to show a legend.

#         title : str, optional
#             A title to put on the figure.

#         figpath : str, optional
#             If specified, the figure is saved with this filename.
#         """

#         # Future : change to a plotly plot.
#         try: import matplotlib.pyplot as _plt
#         except ImportError: raise ValueError("This function requires you to install matplotlib!")

#         if decay and fitkey is None:
#             allfitkeys = list(self.fits.keys())
#             if 'full' in allfitkeys: fitkey = 'full'
#             else:
#                 assert(len(allfitkeys) == 1), \
#                     "There are multiple fits and none have the key 'full'. Please specify the fit to plot!"
#                 fitkey = allfitkeys[0]

#         _plt.figure(figsize=size)
#         _plt.plot(self.data.lengths, self.data.ASPs, 'o', label='Average success probabilities')

#         if decay:
#             lengths = _np.linspace(0, max(self.data.lengths), 200)
#             A = self.fits[fitkey].estimates['A']
#             B = self.fits[fitkey].estimates['B']
#             p = self.fits[fitkey].estimates['p']
#             _plt.plot(lengths, A + B * p**lengths,
#                       label='Fit, r = {:.2} +/- {:.1}'.format(self.fits[fitkey].estimates['r'],
#                                                               self.fits[fitkey].stds['r']))

#         if success_probabilities:
#             _plt.violinplot(list(self.data.success_probabilities), self.data.lengths, points=10, widths=1.,
#                             showmeans=False, showextrema=False, showmedians=False)  # , label='Success probabilities')

#         if title is not None: _plt.title(title)
#         _plt.ylabel("Success probability")
#         _plt.xlabel("RB sequence length $(m)$")
#         _plt.ylim(ylim)
#         _plt.xlim(xlim)

#         if legend: _plt.legend()

#         if figpath is not None: _plt.savefig(figpath, dpi=1000)
#         else: _plt.show()

#         return