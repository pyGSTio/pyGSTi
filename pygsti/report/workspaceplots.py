""" Classes corresponding to plots within a Workspace context."""
#***************************************************************************************************
# Copyright 2015, 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 or in the LICENSE file in the root pyGSTi directory.
#***************************************************************************************************

import numpy as _np
import scipy as _scipy
import warnings as _warnings
import collections as _collections

from scipy.stats import chi2 as _chi2

from .. import algorithms as _alg
from .. import tools as _tools
from .. import objects as _objs

from .workspace import WorkspacePlot
from .figure import ReportFigure
from . import colormaps as _colormaps
from . import plothelpers as _ph

#Plotly v3 changes heirarchy of graph objects
# Do this to avoid deprecation warning is plotly 3+
import plotly
import plotly.graph_objs as go
if int(plotly.__version__.split('.')[0]) >= 3:  # Plotly 3+
    go_XAxis = go.layout.XAxis
    go_YAxis = go.layout.YAxis
    go_Margin = go.layout.Margin
    go_Annotation = go.layout.Annotation
else:
    go_XAxis = go.XAxis
    go_YAxis = go.YAxis
    go_Margin = go.Margin
    go_Annotation = go.Annotation


#DEBUG
#import time as _time  #DEBUG TIMER
#from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

def color_boxplot(plt_data, colormap, colorbar=False, boxLabelSize=0,
                  prec=0, hoverLabelFn=None, hoverLabels=None):
    """
    Create a color box plot.

    Creates a plot.ly heatmap figure composed of colored boxes and
    possibly labels.

    Parameters
    ----------
    plt_data : numpy array
        A 2D array containing the values to be plotted.  None values will
        show up as white.

    colormap : Colormap
        The colormap used to determine box color.

    colorbar : bool, optional
        Whether or not to show the color scale bar.

    boxLabelSize : int, optional
        If greater than 0, display static labels on each box with font
        size equal to `boxLabelSize`.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Allowed values are:
          'compact' = round to nearest whole number using at most 3 characters
          'compacthp' = show as much precision as possible using at most 3 characters
          int >= 0 = fixed precision given by int
          int <  0 = number of significant figures given by -int

    hoverLabelFn : function, optional
        A function with signature `f(z,i,j)` where `z ==plt_data[i,j]` which
        computes the hover label for the each element of `plt_data`.  Cannot
        be used with `hoverLabels`.

    hoverLabels : list of lists, optional
        Strings specifying the hover labels for each element of `plt_data`.
        E.g. `hoverLabels[i,j]` is the string for the i-th row (y-value)
        and j-th column (x-value) of the plot.

    Returns
    -------
    plotly.Figure
    """

    masked_data = _np.ma.array(plt_data, mask=_np.isnan(plt_data))
    heatmapArgs = {'z': colormap.normalize(masked_data),
                   'colorscale': colormap.get_colorscale(),
                   'showscale': colorbar, 'hoverinfo': 'none',
                   'zmin': colormap.hmin, 'zmax': colormap.hmax}

    #if xlabels is not None: heatmapArgs['x'] = xlabels
    #if ylabels is not None: heatmapArgs['y'] = ylabels

    annotations = []
    if boxLabelSize:
        # Write values on colored squares
        for y in range(plt_data.shape[0]):
            for x in range(plt_data.shape[1]):
                if _np.isnan(plt_data[y, x]): continue
                annotations.append(
                    dict(
                        text=_ph._eformat(plt_data[y, x], prec),
                        x=x, y=y,
                        xref='x1', yref='y1',
                        font=dict(size=boxLabelSize,
                                  color=colormap.besttxtcolor(plt_data[y, x])),
                        showarrow=False)
                )

    if hoverLabelFn:
        assert(not hoverLabels), "Cannot specify hoverLabelFn and hoverLabels!"
        hoverLabels = []
        for y in range(plt_data.shape[0]):
            hoverLabels.append([hoverLabelFn(plt_data[y, x], y, x)
                                for x in range(plt_data.shape[1])])
    if hoverLabels:
        heatmapArgs['hoverinfo'] = 'text'
        heatmapArgs['text'] = hoverLabels

    trace = go.Heatmap(**heatmapArgs)
    #trace = dict(type='heatmapgl', **heatmapArgs)
    data = [trace]

    xaxis = go_XAxis(
        showgrid=False,
        zeroline=False,
        showline=True,
        ticks="",
        showticklabels=True,
        mirror=True,
        linewidth=2,
        range=[-0.5, plt_data.shape[1] - 0.5]
    )
    yaxis = go_YAxis(
        showgrid=False,
        zeroline=False,
        showline=True,
        ticks="",
        showticklabels=True,
        mirror=True,
        linewidth=2,
        range=[-0.5, plt_data.shape[0] - 0.5]
    )

    layout = go.Layout(
        xaxis=xaxis,
        yaxis=yaxis,
        annotations=annotations
    )

    fig = go.Figure(data=data, layout=layout)
    return ReportFigure(fig, colormap, plt_data, plt_data=plt_data)


def nested_color_boxplot(plt_data_list_of_lists, colormap,
                         colorbar=False, boxLabelSize=0, prec=0,
                         hoverLabelFn=None):
    """
    Creates a "nested" color box plot by tiling the plaquettes given
    by `plt_data_list_of_lists` onto a single heatmap.

    Parameters
    ----------
    plt_data_list_of_lists : list of lists of numpy arrays
        A complete square 2D list of lists, such that each element is a
        2D numpy array of the same size.

    colormap : Colormap
        The colormap used to determine box color.

    colorbar : bool, optional
        Whether or not to show the color scale bar.

    boxLabelSize : int, optional
        If greater than 0, display static labels on each box with font
        size equal to `boxLabelSize`.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Allowed values are:
          'compact' = round to nearest whole number using at most 3 characters
          'compacthp' = show as much precision as possible using at most 3 characters
          int >= 0 = fixed precision given by int
          int <  0 = number of significant figures given by -int

    hoverLabelFn : function, optional
        A function with signature `f(z,i,j)` where `z ==plt_data[i,j]` which
        computes the hover label for the each element of `plt_data`.  Cannot
        be used with `hoverLabels`.

    Returns
    -------
    plotly.Figure
    """

    #Assemble the single 2D grid to pass to color_boxplot
    # (assume a complete 2D rectangular list of lists, and that
    #  each element is a numpy array of the same size)
    if len(plt_data_list_of_lists) == 0 or len(plt_data_list_of_lists[0]) == 0: return

    elRows, elCols = plt_data_list_of_lists[0][0].shape  # nE,nr
    nRows = len(plt_data_list_of_lists)
    nCols = len(plt_data_list_of_lists[0])

    data = _np.zeros((elRows * nRows + (nRows - 1), elCols * nCols + (nCols - 1)))
    for i in range(1, nRows):
        data[(elRows + 1) * i - 1:(elRows + 1) * i, :] = _np.nan
    for j in range(1, nCols):
        data[:, (elCols + 1) * j - 1:(elCols + 1) * j] = _np.nan

    for i in range(nRows):
        for j in range(nCols):
            data[(elRows + 1) * i:(elRows + 1) * (i + 1) - 1, (elCols + 1)
                 * j:(elCols + 1) * (j + 1) - 1] = plt_data_list_of_lists[i][j]

    xtics = []; ytics = []
    for i in range(nRows): ytics.append(float((elRows + 1) * i) - 0.5 + 0.5 * float(elRows))
    for j in range(nCols): xtics.append(float((elCols + 1) * j) - 0.5 + 0.5 * float(elCols))

    if hoverLabelFn:
        hoverLabels = []
        for _ in range(elRows * nRows + (nRows - 1)):
            hoverLabels.append([""] * (elCols * nCols + (nCols - 1)))

        for i in range(nRows):
            for j in range(nCols):
                for ii in range(elRows):
                    for jj in range(elCols):
                        hoverLabels[(elRows + 1) * i + ii][(elCols + 1) * j + jj] = \
                            hoverLabelFn(plt_data_list_of_lists[i][j][ii][jj], i, j, ii, jj)
    else:
        hoverLabels = None

    fig = color_boxplot(data, colormap, colorbar, boxLabelSize,
                        prec, None, hoverLabels)

    #Layout updates: add tic marks (but not labels - leave that to user)
    fig.plotlyfig['layout']['xaxis'].update(tickvals=xtics)
    fig.plotlyfig['layout']['yaxis'].update(tickvals=ytics)
    return fig


def generate_boxplot(subMxs,
                     xlabels, ylabels, inner_xlabels, inner_ylabels,
                     xlabel, ylabel, inner_xlabel, inner_ylabel,
                     colormap, colorbar=False, boxLabels=True, prec=0, hoverInfo=True,
                     sumUp=False, invert=False, scale=1.0, bgcolor='white'):
    """
    A helper function for generating typical nested color box plots used in pyGSTi.

    Given the list-of-lists, `subMxs`, along with x and y labels for both the "outer"
    (i.e. the list-indices) and "inner" (i.e. the sub-matrix-indices) axes, this function
    will produce a nested color box plot with the option of summing over the inner axes
    or inverting (swapping) the inner and outer axes.

    Parameters
    ----------
    subMxs : list
        A list of lists of 2D numpy.ndarrays.  subMxs[iy][ix] specifies the matrix of values
        or sum (if sumUp == True) displayed in iy-th row and ix-th column of the plot.  NaNs
        indicate elements should not be displayed.

    x_labels, y_labels : list
        Labels for the outer x- and y-axis values.

    inner_x_labels, inner_y_labels : list
        Labels for the inner x- and y-axis values.

    xlabel, ylabel : str
        Outer X and Y axis labels.

    inner_xlabel, inner_ylabel : str
        Inner X and Y axis labels.

    colormap : Colormap
        The colormap used to determine box color.

    colorbar : bool, optional
        Whether or not to show the color scale bar.

    boxLabels : bool, optional
        Whether to display static value-labels over each box.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Allowed values are:
          'compact' = round to nearest whole number using at most 3 characters
          'compacthp' = show as much precision as possible using at most 3 characters
          int >= 0 = fixed precision given by int
          int <  0 = number of significant figures given by -int

    hoverInfo : bool or function, optional
        If a boolean, indicates whether to include interactive hover labels. If
        a function, then must take arguments `(val, iy, ix, iiy, iix)` if
        `sumUp == False` or `(val, iy, ix)` if `sumUp == True` and return a
        label string, where `val` is the box value, `ix` and `iy` index
        `xlabels` and `ylabels`, and `iix` and `iiy` index `inner_xlabels`
        and `inner_ylabels`.

    sumUp : bool, optional
        False displays each matrix element as it's own color box
        True sums the elements of each (x,y) matrix and displays
        a single color box for the sum.

    invert : bool, optional
        If True, invert the nesting order of the nested color box plot
        (applicable only when sumUp == False).  E.g. use inner_x_labels and
        inner_y_labels to label the x and y axes.

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    bgcolor : str, optional
        Background color for this plot.  Can be common color names, e.g.
        `"black"`, or string RGB values, e.g. `"rgb(255,128,0)"`.

    Returns
    -------
    plotly.Figure
    """
    nYs = len(subMxs)
    nXs = len(subMxs[0]) if nYs > 0 else 0

    nIYs = nIXs = 0
    for ix in range(nXs):
        for iy in range(nYs):
            if subMxs[iy][ix] is not None:
                nIYs, nIXs = subMxs[iy][ix].shape; break

    # flip so [0,0] el of original subMxs is at *top*-left (FLIP)
    subMxs = [[_np.flipud(subMx) for subMx in row] for row in subMxs]
    inner_ylabels = list(reversed(inner_ylabels))

    if invert:
        if sumUp:
            _warnings.warn("Cannot invert a summed-up plot.  Ignoring invert=True.")
        else:
            invertedSubMxs = []  # will be indexed as invertedSubMxs[inner-y][inner-x]
            for iny in range(nIYs):
                invertedSubMxs.append([])
                for inx in range(nIXs):
                    mx = _np.array([[subMxs[iy][ix][iny, inx] for ix in range(nXs)]
                                    for iy in range(nYs)], 'd')
                    invertedSubMxs[-1].append(mx)

            # flip the now-inverted mxs to counteract the flip that will occur upon
            # entering generate_boxplot again (with invert=False this time), since we
            # *don't* want the now-inner dimension (the germs) actually flipped (FLIP)
            invertedSubMxs = [[_np.flipud(subMx) for subMx in row] for row in invertedSubMxs]
            ylabels = list(reversed(ylabels))

            return generate_boxplot(invertedSubMxs,
                                    inner_xlabels, inner_ylabels,
                                    xlabels, ylabels, inner_xlabel, inner_ylabel, xlabel, ylabel,
                                    colormap, colorbar, boxLabels, prec, hoverInfo,
                                    sumUp, False, scale, bgcolor)

    def val_filter(vals):
        """filter to latex-ify operation sequences.  Later add filter as a possible parameter"""
        formatted_vals = []
        for val in vals:
            if isinstance(val, _objs.Circuit):
                if len(val) == 0:
                    #formatted_vals.append(r"$\{\}$")
                    formatted_vals.append(r"{}")
                else:
                    #formatted_vals.append( "$" + "\\cdot".join([("\\mathrm{%s}" % el) for el in val]) + "$" )
                    formatted_vals.append(val.str)
            else:
                formatted_vals.append(str(val))
        return formatted_vals

    def sum_up_mx(mx):
        """ Sum up `mx` in a NAN-ignoring way """
        flat_mx = mx.flatten()
        if any([_np.isnan(x) for x in flat_mx]):
            if all([_np.isnan(x) for x in flat_mx]):
                return _np.nan
            # replace NaNs with zeros for purpose of summing (when there's at least one non-NaN)
            return sum(_np.nan_to_num(flat_mx))
        else:
            return sum(flat_mx)

    #Setup and create plotting functions
    if sumUp:
        subMxSums = _np.array([[sum_up_mx(subMxs[iy][ix]) for ix in range(nXs)] for iy in range(nYs)], 'd')

        if hoverInfo is True:
            def hoverLabelFn(val, i, j):
                """ Standard hover labels """
                if _np.isnan(val): return ""
                return "%s: %s<br>%s: %s<br>%g" % \
                    (xlabel, str(xlabels[j]), ylabel, str(ylabels[i]), val)
        elif callable(hoverInfo):
            hoverLabelFn = hoverInfo
        else: hoverLabelFn = None

        boxLabelSize = 8 * scale if boxLabels else 0
        fig = color_boxplot(subMxSums, colormap, colorbar, boxLabelSize,
                            prec, hoverLabelFn)
        #update tickvals b/c color_boxplot doesn't do this (unlike nested_color_boxplot)
        if fig is not None:
            fig.plotlyfig['layout']['xaxis'].update(tickvals=list(range(nXs)))
            fig.plotlyfig['layout']['yaxis'].update(tickvals=list(range(nYs)))

        xBoxes = nXs
        yBoxes = nYs

    else:  # not summing up

        if hoverInfo is True:
            def hoverLabelFn(val, i, j, ii, jj):
                """ Standard hover labels """
                if _np.isnan(val): return ""
                return "%s: %s<br>%s: %s<br>%s: %s<br>%s: %s<br>%g" % \
                    (xlabel, str(xlabels[j]), ylabel, str(ylabels[i]),
                     inner_xlabel, str(inner_xlabels[jj]),
                     inner_ylabel, str(inner_ylabels[ii]), val)
        elif callable(hoverInfo):
            hoverLabelFn = hoverInfo
        else: hoverLabelFn = None

        boxLabelSize = 8 if boxLabels else 0  # do not scale (OLD: 8*scale)
        fig = nested_color_boxplot(subMxs, colormap, colorbar, boxLabelSize,
                                   prec, hoverLabelFn)

        xBoxes = nXs * (nIXs + 1) - 1
        yBoxes = nYs * (nIYs + 1) - 1

    #assert(fig is not None), "No data to display!"
    if fig is not None:  # i.e., if there was data to plot
        pfig = fig.plotlyfig
        if xlabel: pfig['layout']['xaxis'].update(title=xlabel,
                                                  titlefont={'size': 12 * scale, 'color': "black"})
        if ylabel: pfig['layout']['yaxis'].update(title=ylabel,
                                                  titlefont={'size': 12 * scale, 'color': "black"})
        if xlabels:
            pfig['layout']['xaxis'].update(tickmode="array",
                                           ticktext=val_filter(xlabels),
                                           tickfont={'size': 10 * scale, 'color': "black"})
        if ylabels:
            pfig['layout']['yaxis'].update(tickmode="array",
                                           ticktext=val_filter(ylabels),
                                           tickfont={'size': 10 * scale, 'color': "black"})

        #Set plot size and margins
        lmargin = rmargin = tmargin = bmargin = 20
        if xlabel: bmargin += 30
        if ylabel: lmargin += 30
        if xlabels:
            max_xl = max([len(xl) for xl in pfig['layout']['xaxis']['ticktext']])
            if max_xl > 0: bmargin += max_xl * 5
        if ylabels:
            max_yl = max([len(yl) for yl in pfig['layout']['yaxis']['ticktext']])
            if max_yl > 0: lmargin += max_yl * 5
        if colorbar: rmargin = 100

        #make sure there's enough margin for hover tooltips
        if 10 * xBoxes < 200: rmargin = max(200 - 10 * xBoxes, rmargin)
        if 10 * yBoxes < 200: bmargin = max(200 - 10 * xBoxes, bmargin)

        width = lmargin + 10 * xBoxes + rmargin
        height = tmargin + 10 * yBoxes + bmargin

        width *= scale
        height *= scale
        lmargin *= scale
        rmargin *= scale
        tmargin *= scale
        bmargin *= scale

        pfig['layout'].update(width=width,
                              height=height,
                              margin=go_Margin(l=lmargin, r=rmargin, b=bmargin, t=tmargin),
                              plot_bgcolor=bgcolor)

    else:  # fig is None => use a "No data to display" placeholder figure
        trace = go.Heatmap(z=_np.zeros((10, 10), 'd'),
                           colorscale=[[0, 'white'], [1, 'black']],
                           showscale=False, zmin=0, zmax=1, hoverinfo='none')
        layout = go.Layout(
            width=100, height=100,
            annotations=[go_Annotation(x=5, y=5, text="NO DATA", showarrow=False,
                                       font={'size': 20, 'color': "black"},
                                       xref='x', yref='y')],
            xaxis=dict(showline=False, zeroline=False,
                       showticklabels=False, showgrid=False,
                       ticks=""),
            yaxis=dict(showline=False, zeroline=False,
                       showticklabels=False, showgrid=False,
                       ticks="")
        )
        fig = ReportFigure(go.Figure(data=[trace], layout=layout),
                           None, "No data!")

    return fig


def circuit_color_boxplot(circuit_structure, subMxs, colormap,
                          colorbar=False, boxLabels=True, prec='compact', hoverInfo=True,
                          sumUp=False, invert=False, scale=1.0, bgcolor="white", addl_hover_subMxs=None):
    """
    A wrapper around :func:`generate_boxplot` for creating color box plots
    when the structure of the operation sequences is contained in  a
    `CircuitStructure` object.

    Parameters
    ----------
    circuit_structure : CircuitStructure
        Specifies a set of operation sequences along with their outer and inner x,y
        structure, e.g. fiducials, germs, and maximum lengths.

    subMxs : list
        A list of lists of 2D numpy.ndarrays.  subMxs[iy][ix] specifies the matrix of values
        or sum (if sumUp == True) displayed in iy-th row and ix-th column of the plot.  NaNs
        indicate elements should not be displayed.

    colormap : Colormap
        The colormap used to determine box color.

    colorbar : bool, optional
        Whether or not to show the color scale bar.

    boxLabels : bool, optional
        Whether to display static value-labels over each box.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Allowed values are:
          'compact' = round to nearest whole number using at most 3 characters
          'compacthp' = show as much precision as possible using at most 3 characters
          int >= 0 = fixed precision given by int
          int <  0 = number of significant figures given by -int

    hoverInfo : bool, optional
        Whether to incude interactive hover labels.

    sumUp : bool, optional
        False displays each matrix element as it's own color box
        True sums the elements of each (x,y) matrix and displays
        a single color box for the sum.

    invert : bool, optional
        If True, invert the nesting order of the nested color box plot
        (applicable only when sumUp == False).  E.g. use inner_x_labels and
        inner_y_labels to label the x and y axes.

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    bgcolor : str, optional
        Background color for this plot.  Can be common color names, e.g.
        `"black"`, or string RGB values, e.g. `"rgb(255,128,0)"`.

    addl_hover_subMxs : dict, optional
        If not None, a dictionary whose values are lists-of-lists in the same
        format as `subMxs` which specify additional values to add to the
        hover-info of the corresponding boxes.  The keys of this dictionary
        are used as labels within the hover-info text.

    Returns
    -------
    plotly.Figure
    """
    g = circuit_structure
    xvals = g.used_xvals()
    yvals = g.used_yvals()
    inner_xvals = g.minor_xvals()
    inner_yvals = g.minor_yvals()

    if addl_hover_subMxs is None:
        addl_hover_subMxs = {}

    # Note: invert == True case not handled yet, and the below hover label
    # routines assume L,germ structure in particular
    if hoverInfo and not invert and isinstance(g, _objs.LsGermsStructure):
        if sumUp:
            def hoverLabelFn(val, iy, ix):
                """ Standard hover labels """
                if _np.isnan(val): return ""
                L, germ = xvals[ix], yvals[iy]
                baseStr = g.get_plaquette(L, germ, False).base
                reps = (len(baseStr) // len(germ)) if len(germ) > 0 else 1
                guess = germ * reps
                if baseStr == guess:
                    if len(baseStr) == 0:
                        txt = "{}"
                    else:
                        txt = "(%s)<sup>%d</sup>" % (germ.str, reps)
                else:
                    txt = "L: %s<br>germ: %s" % (str(L), germ.str)

                txt += "<br>value: %g" % val
                for lbl, addl_subMxs in addl_hover_subMxs.items():
                    txt += "<br>%s: %s" % (lbl, str(addl_subMxs[iy][ix]))
                return txt

        else:
            def hoverLabelFn(val, iy, ix, iiy, iix):
                """ Standard hover labels """
                #Note: in this case, we need to "flip" the iiy index because
                # the matrices being plotted are flipped within generate_boxplot(...)
                if _np.isnan(val): return ""

                N = len(inner_yvals)
                L, germ = xvals[ix], yvals[iy]
                rhofid, efid = inner_xvals[iix], inner_yvals[N - 1 - iiy]  # FLIP
                baseStr = g.get_plaquette(L, germ, False).base
                reps = (len(baseStr) // len(germ)) if len(germ) > 0 else 1
                guess = germ * reps
                if baseStr == guess:
                    if len(baseStr) == 0:
                        txt = "%s+{}+%s" % (rhofid.str, efid.str)
                    else:
                        txt = "%s+(%s)<sup>%d</sup>+%s" % (
                            rhofid.str, germ.str, reps, efid.str)
                else:
                    txt = "L: %s<br>germ: %s<br>rho<sub>i</sub>: %s<br>E<sub>i</sub>: %s" \
                          % (str(L), germ.str, rhofid.str, efid.str)
                txt += ("<br>value: %g" % val)
                for lbl, addl_subMxs in addl_hover_subMxs.items():
                    N = len(addl_subMxs[iy][ix])  # flip so original [0,0] el is at top-left (FLIP)
                    txt += "<br>%s: %s" % (lbl, str(addl_subMxs[iy][ix][N - 1 - iiy][iix]))
                return txt

        hoverInfo = hoverLabelFn  # generate_boxplot can handle this

    return generate_boxplot(subMxs,
                            g.used_xvals(), g.used_yvals(),
                            g.minor_xvals(), g.minor_yvals(),
                            "L", "germ", "rho", "E<sub>i</sub>", colormap,
                            colorbar, boxLabels, prec, hoverInfo,
                            sumUp, invert, scale, bgcolor)  # "$\\rho_i$","$\\E_i$"


def circuit_color_scatterplot(circuit_structure, subMxs, colormap,
                              colorbar=False, hoverInfo=True, sumUp=False,
                              ylabel="", scale=1.0, addl_hover_subMxs=None):
    """
    Similar to :func:`circuit_color_boxplot` except a scatter plot is created.

    Parameters
    ----------
    circuit_structure : CircuitStructure
        Specifies a set of operation sequences along with their outer and inner x,y
        structure, e.g. fiducials, germs, and maximum lengths.

    subMxs : list
        A list of lists of 2D numpy.ndarrays.  subMxs[iy][ix] specifies the matrix of values
        or sum (if sumUp == True) displayed in iy-th row and ix-th column of the plot.  NaNs
        indicate elements should not be displayed.

    colormap : Colormap
        The colormap used to determine box color.

    colorbar : bool, optional
        Whether or not to show the color scale bar.

    boxLabels : bool, optional
        Whether to display static value-labels over each box.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Allowed values are:
          'compact' = round to nearest whole number using at most 3 characters
          'compacthp' = show as much precision as possible using at most 3 characters
          int >= 0 = fixed precision given by int
          int <  0 = number of significant figures given by -int

    hoverInfo : bool, optional
        Whether to incude interactive hover labels.

    sumUp : bool, optional
        False displays each matrix element as it's own color box
        True sums the elements of each (x,y) matrix and displays
        a single color box for the sum.

    ylabel : str, optional
        The y-axis label to use.

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    addl_hover_subMxs : dict, optional
        If not None, a dictionary whose values are lists-of-lists in the same
        format as `subMxs` which specify additional values to add to the
        hover-info of the corresponding boxes.  The keys of this dictionary
        are used as labels within the hover-info text.

    Returns
    -------
    plotly.Figure
    """
    g = circuit_structure
    xvals = g.used_xvals()
    yvals = g.used_yvals()
    inner_xvals = g.minor_xvals()
    inner_yvals = g.minor_yvals()

    if addl_hover_subMxs is None:
        addl_hover_subMxs = {}

    #TODO: move hover-function creation routines to new function since duplicated in
    # circuit_color_boxplot

    if hoverInfo and isinstance(g, _objs.LsGermsStructure):
        if sumUp:
            def hoverLabelFn(val, iy, ix):
                """ Standard hover labels """
                if _np.isnan(val): return ""
                L, germ = xvals[ix], yvals[iy]
                baseStr = g.get_plaquette(L, germ, False).base
                reps = (len(baseStr) // len(germ)) if len(germ) > 0 else 1
                guess = germ * reps
                if baseStr == guess:
                    if len(baseStr) == 0:
                        txt = "{}"
                    else:
                        txt = "(%s)<sup>%d</sup>" % (germ.str, reps)
                else:
                    txt = "L: %s<br>germ: %s" % (str(L), germ.str)

                txt += "<br>value: %g" % val
                for lbl, addl_subMxs in addl_hover_subMxs.items():
                    txt += "<br>%s: %s" % (lbl, str(addl_subMxs[iy][ix]))
                return txt

        else:
            def hoverLabelFn(val, iy, ix, iiy, iix):
                """ Standard hover labels """
                if _np.isnan(val): return ""

                L, germ = xvals[ix], yvals[iy]
                rhofid, efid = inner_xvals[iix], inner_yvals[iiy]
                baseStr = g.get_plaquette(L, germ, False).base
                reps = (len(baseStr) // len(germ)) if len(germ) > 0 else 1
                guess = germ * reps
                if baseStr == guess:
                    if len(baseStr) == 0:
                        txt = "%s+{}+%s" % (rhofid.str, efid.str)
                    else:
                        txt = "%s+(%s)<sup>%d</sup>+%s" % (
                            rhofid.str, germ.str, reps, efid.str)
                else:
                    txt = "L: %s<br>germ: %s<br>rho<sub>i</sub>: %s<br>E<sub>i</sub>: %s" \
                          % (str(L), germ.str, rhofid.str, efid.str)
                txt += ("<br>value: %g" % val)
                for lbl, addl_subMxs in addl_hover_subMxs.items():
                    txt += "<br>%s: %s" % (lbl, str(addl_subMxs[iy][ix][iiy][iix]))
                return txt

        hoverInfo = hoverLabelFn  # generate_boxplot can handle this

    xs = []; ys = []; texts = []
    gstrs = set()  # to eliminate duplicate strings
    for ix, x in enumerate(g.used_xvals()):
        for iy, y in enumerate(g.used_yvals()):
            plaq = g.get_plaquette(x, y)
            if sumUp:
                if plaq.base not in gstrs:
                    tot = sum([subMxs[iy][ix][iiy][iix] for iiy, iix, _ in plaq])
                    xs.append(len(plaq.base))  # x-coord is len of *base* string
                    ys.append(tot)
                    gstrs.add(plaq.base)
                    if hoverInfo:
                        if callable(hoverInfo):
                            texts.append(hoverInfo(tot, iy, ix))
                        else:
                            texts.append(str(tot))
            else:
                for iiy, iix, opstr in plaq:
                    if opstr in gstrs: continue  # skip duplicates
                    xs.append(len(opstr))
                    ys.append(subMxs[iy][ix][iiy][iix])
                    gstrs.add(opstr)
                    if hoverInfo:
                        if callable(hoverInfo):
                            texts.append(hoverInfo(subMxs[iy][ix][iiy][iix], iy, ix, iiy, iix))
                        else:
                            texts.append(str(subMxs[iy][ix][iiy][iix]))

    #This GL version works, but behaves badly, sometimes failing to render...
    #trace = go.Scattergl(x=xs, y=ys, mode="markers",
    #                     marker=dict(size=8,
    #                                 color=[colormap.get_color(y) for y in ys],
    #                                 #colorscale=colormap.get_colorscale(),  #doesn't seem to work properly in GL?
    #                                 line=dict(width=1)))
    trace = go.Scatter(x=xs, y=ys, mode="markers",
                       marker=dict(size=8,
                                   color=[colormap.get_color(y) for y in ys],
                                   colorscale=colormap.get_colorscale(),
                                   line=dict(width=1)))

    if hoverInfo:
        trace['hoverinfo'] = 'text'
        trace['text'] = texts
    else:
        trace['hoverinfo'] = 'none'

    xaxis = go_XAxis(
        title='sequence length',
        showline=False,
        zeroline=True,
    )
    yaxis = go_YAxis(
        title=ylabel
    )

    layout = go.Layout(
        #title="Sum = %.2f" % sum(ys), #DEBUG
        width=400 * scale,
        height=400 * scale,
        hovermode='closest',
        xaxis=xaxis,
        yaxis=yaxis,
    )
    return ReportFigure(go.Figure(data=[trace], layout=layout), colormap,
                        {'x': xs, 'y': ys})


def circuit_color_histogram(circuit_structure, subMxs, colormap,
                            ylabel="", scale=1.0):
    """
    Similar to :func:`circuit_color_boxplot` except a histogram is created.

    Parameters
    ----------
    circuit_structure : CircuitStructure
        Specifies a set of operation sequences along with their outer and inner x,y
        structure, e.g. fiducials, germs, and maximum lengths.

    subMxs : list
        A list of lists of 2D numpy.ndarrays.  subMxs[iy][ix] specifies the matrix of values
        or sum (if sumUp == True) displayed in iy-th row and ix-th column of the plot.  NaNs
        indicate elements should not be displayed.

    colormap : Colormap
        The colormap used to determine box color.

    hoverInfo : bool, optional
        Whether to incude interactive hover labels.

    sumUp : bool, optional
        False displays each matrix element as it's own color box
        True sums the elements of each (x,y) matrix and displays
        a single color box for the sum.

    ylabel : str, optional
        The y-axis label to use.

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    Returns
    -------
    plotly.Figure
    """
    g = circuit_structure

    ys = []  # artificially add minval so
    gstrs = set()  # to eliminate duplicate strings
    for ix, x in enumerate(g.used_xvals()):
        for iy, y in enumerate(g.used_yvals()):
            plaq = g.get_plaquette(x, y)
            #TODO: if sumUp then need to sum before appending...
            for iiy, iix, opstr in plaq:
                if opstr in gstrs: continue  # skip duplicates
                ys.append(subMxs[iy][ix][iiy][iix])
                gstrs.add(opstr)
    if len(ys) == 0: ys = [0]  # case of no data - dummy so max works below

    minval = 0
    maxval = max(minval + 1e-3, _np.max(ys))  # don't let minval==maxval
    nvals = len(ys)
    cumulative = dict(enabled=False)
    #             marker=dict(color=barcolor),
    #barcolor = 'gray'

    nbins = 50
    binsize = (maxval - minval) / (nbins - 1)
    bincenters = _np.linspace(minval, maxval, nbins)
    bindelta = (maxval - minval) / (nbins - 1)  # spacing between bin centers

    trace = go.Histogram(
        x=[bincenters[0]] + ys,  # artificially add 1 count in lowest bin so plotly anchors histogram properly
        autobinx=False,
        xbins=dict(
            start=minval - binsize / 2.0,
            end=maxval + binsize / 2.0,
            size=binsize
        ),
        name="count",
        marker=dict(
            color=[colormap.get_color(t) for t in bincenters],
            line=dict(
                color='black',
                width=1.0,
            )
        ),
        cumulative=cumulative,
        opacity=1.00,
        showlegend=False,
    )

    dof = colormap.dof if hasattr(colormap, "dof") else 1
    line_trace = go.Scatter(
        x=bincenters,
        y=[nvals * bindelta * _chi2.pdf(xval, dof) for xval in bincenters],
        name="expected",
        showlegend=False,
        line=dict(
            color=('rgb(0, 0, 0)'),
            width=1)  # dash = 'dash') # dash options include 'dash', 'dot', and 'dashdot'
    )

    hist_values, np_bins = _np.histogram(ys, nbins, range=(minval - binsize / 2.0,
                                                           maxval + binsize / 2.0))
    if len(hist_values) > 0 and len(hist_values[hist_values > 0]) > 0:
        minlog = _np.log10(max(_np.min(hist_values[hist_values > 0]) / 10.0, 1e-3))
        maxlog = _np.log10(1.5 * _np.max(hist_values))
    else:
        minlog, maxlog = -3, 0  # defaults to (1e-3,1) when there's no data

    layout = go.Layout(
        #title="Sum = %.2f" % sum(ys), #DEBUG
        width=500 * scale,
        height=350 * scale,
        font=dict(size=10),
        xaxis=dict(
            title=ylabel,  # b/c "y-values" are along x-axis in histogram
            showline=True
        ),
        yaxis=dict(
            type='log',
            #tickformat='g',
            exponentformat='power',
            showline=True,
            range=[minlog, maxlog]
        ),
        bargap=0,
        bargroupgap=0,
        legend=dict(orientation="h")
    )

    pythonVal = {'histogram values': ys}
    return ReportFigure(go.Figure(data=[trace, line_trace], layout=layout),
                        colormap, pythonVal)


def opmatrix_color_boxplot(opMatrix, m, M, mxBasis=None, mxBasisY=None,
                           xlabel=None, ylabel=None,
                           boxLabels=False, colorbar=None, prec=0, scale=1.0,
                           EBmatrix=None, title=None):
    """
    Creates a color box plot for visualizing a single matrix.

    Parameters
    ----------
    opMatrix : numpy array
        The matrix to visualize.

    m, M : float
        Minimum and maximum of the color scale.

    mxBasis, mxBasisY : str or Basis, optional
      The name abbreviation for the basis or a Basis object. Used to label the
      columns & rows (x- and y-ticklabels).  Typically in
      {"pp","gm","std","qt"}.  If you don't want labels, leave as None.

    xlabel, ylabel : str, optional
      Axis labels for the plot.

    boxLabels : bool, optional
        Whether box labels are displayed.

    colorbar : bool optional
        Whether to display a color bar to the right of the box plot.  If None,
        then a colorbar is displayed when `boxLabels == False`.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Only relevant when boxLabels == True. Allowed
        values are:

        - 'compact' = round to nearest whole number using at most 3 characters
        - 'compacthp' = show as much precision as possible using at most 3 characters
        - int >= 0 = fixed precision given by int
        - int <  0 = number of significant figures given by -int

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    EBmatrix : numpy array, optional
        An array, of the same size as `opMatrix`, which gives error bars to be
        be displayed in the hover info.

    title : str, optional
        A title for the plot


    Returns
    -------
    plotly.Figure
    """

    if isinstance(mxBasis, str):
        if mxBasisY is None:
            mxBasisY = _objs.BuiltinBasis(mxBasis, opMatrix.shape[0])
        mxBasis = _objs.BuiltinBasis(mxBasis, opMatrix.shape[1])
    else:
        if mxBasisY is None and opMatrix.shape[0] == opMatrix.shape[1]:
            mxBasisY = mxBasis  # can use mxBasis, whatever it is

    if isinstance(mxBasisY, str):
        mxBasisY = _objs.BuiltinBasis(mxBasisY, opMatrix.shape[0])

    if mxBasis is not None:
        xlabels = [("<i>%s</i>" % x) if len(x) else "" for x in mxBasis.labels]
    else:
        xlabels = [""] * opMatrix.shape[1]

    if mxBasisY is not None:
        ylabels = [("<i>%s</i>" % x) if len(x) else "" for x in mxBasisY.labels]
    else:
        ylabels = [""] * opMatrix.shape[0]

    colormap = _colormaps.DivergingColormap(vmin=m, vmax=M)
    thickLineInterval = 4 if (mxBasis is not None and mxBasis.name == "pp") \
        else None  # TODO: separate X and Y thick lines?
    return matrix_color_boxplot(opMatrix, xlabels, ylabels,
                                xlabel, ylabel, boxLabels, thickLineInterval,
                                colorbar, colormap, prec, scale,
                                EBmatrix, title)


def matrix_color_boxplot(matrix, xlabels=None, ylabels=None,
                         xlabel=None, ylabel=None, boxLabels=False,
                         thickLineInterval=None, colorbar=None, colormap=None,
                         prec=0, scale=1.0, EBmatrix=None, title=None, grid="black"):
    """
    Creates a color box plot for visualizing a single matrix.

    Parameters
    ----------
    matrix : numpy array
        The matrix to visualize.

    m, M : float
        Minimum and maximum of the color scale.

    xlabels, ylabels: list, optional
        List of (str) box labels for each axis.

    xlabel, ylabel : str, optional
        Axis labels for the plot.

    boxLabels : bool, optional
        Whether box labels are displayed.

    thickLineInterval : int, optional
        If not None, the interval at thicker (darker) lines should be placed.
        For example, if 2 then every other grid line will be thick.

    colorbar : bool optional
        Whether to display a color bar to the right of the box plot.  If None,
        then a colorbar is displayed when `boxLabels == False`.

    colormap : Colormap, optional
        An a color map object used to convert the numerical matrix values into
        colors.

    prec : int or {'compact','compacthp'}, optional
        Precision for box labels.  Only relevant when boxLabels == True. Allowed
        values are:

        - 'compact' = round to nearest whole number using at most 3 characters
        - 'compacthp' = show as much precision as possible using at most 3 characters
        - int >= 0 = fixed precision given by int
        - int <  0 = number of significant figures given by -int

    scale : float, optional
        Scaling factor to adjust the size of the final figure.

    EBmatrix : numpy array, optional
        An array, of the same size as `matrix`, which gives error bars to be
        be displayed in the hover info.

    title : str, optional
        A title for the plot

    grid : {"white","black",None}
        What color grid lines, if any, to add to the plot.  Advanced usage
        allows the addition of `:N` where `N` is an integer giving the line
        width.

    Returns
    -------
    plotly.Figure
    """
    if xlabels is None: xlabels = [""] * matrix.shape[1]
    if ylabels is None: ylabels = [""] * matrix.shape[0]
    HOVER_PREC = 7  # precision for hover labels

    colorbar = colorbar if (colorbar is not None) else (not boxLabels)

    flipped_mx = _np.flipud(matrix)  # FLIP so [0,0] matrix el is at *top* left
    ylabels = list(reversed(ylabels))  # FLIP y-labels to match

    #Create hoverlabels manually, since hoverinfo='z' arg to Heatmap
    # doesn't work for certain (e.g. linear-log) color maps
    if EBmatrix is None:
        def hoverLabelFn(i, j):
            """ Standard hover labels """
            val = flipped_mx[i, j]
            if _np.isnan(val): return ""
            return "%s" % round(val, HOVER_PREC)  # TODO: something better - or user-specifiable
    else:
        flipped_EBmx = _np.flipud(EBmatrix)  # FLIP so [0,0] matrix el is at *top* left

        def hoverLabelFn(i, j):
            """ Standard hover labels w/error bars"""
            val, eb = flipped_mx[i, j], flipped_EBmx[i, j]
            if _np.isnan(val): return ""
            # TODO: something better - or user-specifiable
            return "%s <br>+/- %s" % (round(val, HOVER_PREC), round(eb, HOVER_PREC))

    hoverLabels = []
    for i in range(matrix.shape[0]):
        hoverLabels.append([hoverLabelFn(i, j)
                            for j in range(matrix.shape[1])])

    trace = go.Heatmap(z=colormap.normalize(flipped_mx),
                       colorscale=colormap.get_colorscale(),
                       showscale=colorbar, zmin=colormap.hmin,
                       zmax=colormap.hmax, hoverinfo='text',
                       text=hoverLabels)
    #trace = dict(type='heatmapgl', z=colormap.normalize(flipped_mx),
    #             colorscale=colormap.get_colorscale(),
    #             showscale=colorbar, zmin=colormap.hmin,
    #             zmax=colormap.hmax, hoverinfo='text', text=hoverLabels) #hoverinfo='z')

    data = [trace]

    nX = matrix.shape[1]
    nY = matrix.shape[0]

    gridlines = []
    showframe = True  # show black axes except with white grid lines (aesthetic)

    if grid:
        if ':' in grid:
            gridlinecolor, w = grid.split(':')
            gridlinewidth = int(w)
        else:
            gridlinecolor = grid  # then 'grid' is the line color
            gridlinewidth = None

        if gridlinecolor == "white":
            showframe = False

        # Vertical lines
        for i in range(nX - 1):
            if gridlinewidth:
                w = gridlinewidth
            else:
                #add darker lines at multiples of thickLineInterval boxes
                w = 3 if (thickLineInterval
                          and (i + 1) % thickLineInterval == 0) else 1

            gridlines.append(
                {
                    'type': 'line',
                    'x0': i + 0.5, 'y0': -0.5,
                    'x1': i + 0.5, 'y1': nY - 0.5,
                    'line': {'color': gridlinecolor, 'width': w},
                })

        #Horizontal lines
        for i in range(nY - 1):
            if gridlinewidth:
                w = gridlinewidth
            else:
                #add darker lines at multiples of thickLineInterval boxes
                w = 3 if (thickLineInterval and (i + 1) % thickLineInterval == 0) else 1

            gridlines.append(
                {
                    'type': 'line',
                    'x0': -0.5, 'y0': i + 0.5,
                    'x1': nX - 0.5, 'y1': i + 0.5,
                    'line': {'color': gridlinecolor, 'width': w},
                })

    annotations = []
    if boxLabels:
        for ix in range(nX):
            for iy in range(nY):
                annotations.append(
                    dict(
                        text=_ph._eformat(matrix[iy, ix], prec),
                        x=ix, y=nY - 1 - iy, xref='x1', yref='y1',
                        font=dict(size=8,  # don't scale box labels (OLD: 8*scale)
                                  color=colormap.besttxtcolor(matrix[iy, ix])),
                        showarrow=False)
                )

    #Set plot size and margins
    lmargin = rmargin = tmargin = bmargin = 20
    if title: tmargin += 30
    if xlabel: tmargin += 30
    if ylabel: lmargin += 30
    max_xl = max([len(str(xl)) for xl in xlabels])
    if max_xl > 0: tmargin += max_xl * 7
    max_yl = max([len(str(yl)) for yl in ylabels])
    if max_yl > 0: lmargin += max_yl * 7
    if colorbar: rmargin = 100

    boxSizeX = boxSizeY = 15

    maxTextLen = -1  # DB
    if boxLabels:
        if prec in ('compact', 'compacthp'):
            precnum = 3 + 1  # +1 for - sign, e.g. "-1e4"
        else: precnum = abs(prec) + 1
        boxSizeX = boxSizeY = 8 * precnum

        if len(annotations) > 0:
            maxTextLen = max([len(ann['text']) for ann in annotations])
            boxSizeX = boxSizeY = max(8 * maxTextLen, 8 * precnum)

    if (matrix.shape[0] < 3):
        # there is issue with hover info not working for
        # small row of horizontal boxes
        boxSizeY = max(35, boxSizeY)

    width = lmargin + boxSizeX * matrix.shape[1] + rmargin
    height = tmargin + boxSizeY * matrix.shape[0] + bmargin
    #print("DB: matrix_color_boxplot dims: ",width,height) # to check auto-width/height

    width *= scale
    height *= scale
    lmargin *= scale
    rmargin *= scale
    tmargin *= scale
    bmargin *= scale

    layout = go.Layout(
        title=title,
        titlefont=dict(size=10 * scale),
        width=width,
        height=height,
        margin=go_Margin(l=lmargin, r=rmargin, b=bmargin, t=tmargin),  # pad=0
        xaxis=dict(
            side="top",
            title=xlabel,
            titlefont=dict(size=10 * scale),
            showgrid=False,
            zeroline=False,
            showline=showframe,
            showticklabels=True,
            mirror=True,
            ticks="",
            linewidth=2,
            ticktext=[str(xl) for xl in xlabels],
            tickvals=[i for i in range(len(xlabels))],
            tickangle=-90,
            range=[-0.5, len(xlabels) - 0.5]
        ),
        yaxis=dict(
            side="left",
            title=ylabel,
            titlefont=dict(size=10 * scale),
            showgrid=False,
            zeroline=False,
            showline=showframe,
            showticklabels=True,
            mirror=True,
            ticks="",
            linewidth=2,
            ticktext=[str(yl) for yl in ylabels],
            tickvals=[i for i in range(len(ylabels))],
            range=[-0.5, len(ylabels) - 0.5],
        ),
        shapes=gridlines,
        annotations=annotations
    )

    return ReportFigure(go.Figure(data=data, layout=layout),
                        colormap, flipped_mx, plt_data=flipped_mx)


class BoxKeyPlot(WorkspacePlot):
    """
    Plot serving as a key for fiducial rows/columns of each plaquette of
    a circuit color box plot.
    """

    def __init__(self, ws, prepStrs, effectStrs,
                 xlabel="Preparation fiducial", ylabel="Measurement fiducial", scale=1.0):
        """
        Create a plot showing the layout of a single sub-block of a goodness-of-fit
        box plot (such as those produced by ColorBoxPlot)

        Parameters
        ----------
        prepStrs, effectStrs : list of Circuits
            Preparation and measurement fiducials.

        xlabel, ylabel : str, optional
            X and Y axis labels

        scale : float, optional
            Scaling factor to adjust the size of the final figure.
        """
        # separate in rendering/saving: save_to=None, ticSize=20, scale=1.0 (?)
        super(BoxKeyPlot, self).__init__(ws, self._create, prepStrs, effectStrs,
                                         xlabel, ylabel, scale)

        #size, save_to,

    def _create(self, prepStrs, effectStrs, xlabel, ylabel, scale):

        #Copied from generate_boxplot
        def val_filter(vals):
            """filter to latex-ify operation sequences.  Later add filter as a possible parameter"""
            formatted_vals = []
            for val in vals:
                if isinstance(val, _objs.Circuit):
                    if len(val) == 0:
                        #formatted_vals.append(r"$\{\}$")
                        formatted_vals.append(r"{}")
                    else:
                        #formatted_vals.append( "$" + "\\cdot".join([("\\mathrm{%s}" % el) for el in val]) + "$" )
                        formatted_vals.append(val.str)
                else:
                    formatted_vals.append(str(val))
            return formatted_vals

        nX = len(prepStrs)
        nY = len(effectStrs)
        trace = go.Heatmap(z=_np.zeros((nY, nX), 'd'),
                           colorscale=[[0, 'white'], [1, 'black']],
                           showscale=False, zmin=0, zmax=1, hoverinfo='none')
        #trace = dict(type='heatmapgl', z=_np.zeros((nY,nX),'d'),
        #                   colorscale=[ [0, 'white'], [1, 'black'] ],
        #                   showscale=False, zmin=0,zmax=1,hoverinfo='none')
        data = [trace]

        gridlines = []

        # Vertical lines
        for i in range(nX - 1):
            gridlines.append(
                {
                    'type': 'line',
                    'x0': i + 0.5, 'y0': -0.5,
                    'x1': i + 0.5, 'y1': nY - 0.5,
                    'line': {'color': 'black', 'width': 1},
                })

        #Horizontal lines
        for i in range(nY - 1):
            gridlines.append(
                {
                    'type': 'line',
                    'x0': -0.5, 'y0': i + 0.5,
                    'x1': nX - 0.5, 'y1': i + 0.5,
                    'line': {'color': 'black', 'width': 1},
                })

        layout = go.Layout(
            width=40 * (nX + 1.5) * scale,
            height=40 * (nY + 1.5) * scale,
            xaxis=dict(
                side="bottom",
                showgrid=False,
                zeroline=False,
                showline=True,
                showticklabels=True,
                mirror=True,
                ticks="",
                linewidth=2,
                ticktext=val_filter(prepStrs),
                tickvals=[i for i in range(len(prepStrs))],
                tickangle=90
            ),
            yaxis=dict(
                side="right",
                showgrid=False,
                zeroline=False,
                showline=True,
                showticklabels=True,
                mirror=True,
                ticks="",
                linewidth=2,
                ticktext=list(reversed(val_filter(effectStrs))),
                tickvals=[i for i in range(len(effectStrs))],
            ),
            shapes=gridlines,
            annotations=[
                go_Annotation(
                    x=0.5,
                    y=1.2,
                    showarrow=False,
                    text=xlabel,
                    font={'size': 12 * scale, 'color': "black"},
                    xref='paper',
                    yref='paper'),
                go_Annotation(
                    x=-0.2,
                    y=0.5,
                    showarrow=False,
                    textangle=-90,
                    text=ylabel,
                    font={'size': 12 * scale, 'color': "black"},
                    xref='paper',
                    yref='paper'
                )
            ]
        )
        # margin = go_Margin(l=50,r=50,b=50,t=50) #pad=0
        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, "No data in box key plot!",
                            special='keyplot', args=(prepStrs, effectStrs, xlabel, ylabel))


class ColorBoxPlot(WorkspacePlot):
    """
    Plot of colored boxes arranged into plaquettes showing various quanties
    for each gate sequence in an analysis.
    """

    def __init__(self, ws, plottype, gss, dataset, model,
                 sumUp=False, boxLabels=False, hoverInfo=True, invert=False,
                 prec='compact', linlg_pcntle=.05, minProbClipForWeighting=1e-4,
                 directGSTmodels=None, dscomparator=None, stabilityanalyzer=None,
                 submatrices=None, typ="boxes", scale=1.0, comm=None,
                 wildcard=None, colorbar=False, bgcolor="white"):
        """
        Create a plot displaying the value of per-circuit quantities.

        Values are shown on a grid of colored boxes, organized according to
        the structure of the operation sequences (e.g. by germ and "L").

        Parameters
        ----------
        plottype : {"chi2","logl","tvd","blank","errorrate","directchi2","directlogl","dscmp",
                    "driftdetector", "driftsize"}
            Specifies the type of plot. "errorate", "directchi2" and
            "directlogl" require that `directGSTmodels` be set.

        gss : CircuitStructure
            Specifies the set of operation sequences along with their structure, e.g.
            fiducials, germs, and maximum lengths.

        dataset : DataSet
            The data used to specify frequencies and counts.

        model : Model
            The model used to specify the probabilities and SPAM labels.

        sumUp : bool, optional
            False displays each matrix element as it's own color box
            True sums the elements of each (x,y) matrix and displays
            a single color box for the sum.

        boxLabels : bool, optional
            Whether box labels are displayed.  It takes much longer to
            generate the figure when this is set to True.

        hoverInfo : bool, optional
            Whether to include interactive hover labels.

        invert : bool, optional
            If True, invert the nesting order of the color box plot (applicable
            only when sumUp == False).

        prec : int, optional
            Precision for box labels.  Allowed values are:
              'compact' = round to nearest whole number using at most 3 characters
              'compacthp' = show as much precision as possible using at most 3 characters
              int >= 0 = fixed precision given by int
              int <  0 = number of significant figures given by -int

        linlg_pcntle : float, optional
            Specifies the (1 - linlg_pcntle) percentile to compute for the boxplots

        minProbClipForWeighting : float, optional
            Defines a clipping point for the statistical weight used
            within the chi^2 or logl functions.

        directGSTmodels : dict, optional
            A dictionary of "direct" Models used when displaying certain plot
            types.  Keys are operation sequences and values are corresponding gate
            sets (see `plottype` above).

        dscomparator : DataComparator, optional
            The data set comparator used to produce the "dscmp" plot type.

        stabilityanalyzer : StabilityAnalyzer or 3-tuple, optional
            Only used to produce the "driftdetector" and "driftsize" boxplot. If a StabilityAnalyzer, then
            this contains the results of the drift / stability analysis to be displayed.
            For non-expert users, this is the best option. If a tuple, then the first
            element of the tuple is this StabilityAnalyzer object,
            and the second and third elements of the tuple label which instability detection
            results to display (a StabilityAnalyzer can contain multiple distinct tests for
            instability). The second element is the "detectorkey", which can be None (the
            default), or a string specifying which of the drift detection results to use for
            the plot. If it is None, then the default set of results are used. The third element
            of the tuple is either None, or a tuple that specifies which "level" of tests to
            use from the drift detection run (specified by the detectorkey), e.g., per-circuit
            with outcomes averaged or per-circuit per-outcome.

        submatrices : dict, optional
            A dictionary whose keys correspond to other potential plot
            types and whose values are each a list-of-lists of the sub
            matrices to plot, corresponding to the used x and y values
            of `gss`.

        typ : {"boxes","scatter","histogram"}
            Which type of plot to make: the standard grid of "boxes", a
            "scatter" plot of the values vs. sequence length, or a "histogram"
            of all the values.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        comm : mpi4py.MPI.Comm, optional
            When not None, an MPI communicator for distributing the computation
            across multiple processors.

        wildcard : WildcardBudget
            A wildcard budget to apply to the objective function that increases
            the goodness of fit by adjusting (by an amount measured in TVD) the
            probabilities produced by `model` before comparing with the
            frequencies in `dataset`.  Currently, this functionality is only
            supported for `plottype == "logl"`.

        colorbar : bool, optional
            Whether to include a colorbar.

        bgcolor : str, optional
            Background color for this plot.  Can be common color names, e.g.
            `"black"`, or string RGB values, e.g. `"rgb(255,128,0)"`.
        """
        # separate in rendering/saving: save_to=None, ticSize=20, scale=1.0 (?)
        super(ColorBoxPlot, self).__init__(ws, self._create, plottype, gss, dataset, model,
                                           prec, sumUp, boxLabels, hoverInfo,
                                           invert, linlg_pcntle, minProbClipForWeighting,
                                           directGSTmodels, dscomparator, stabilityanalyzer,
                                           submatrices, typ, scale, comm, wildcard, colorbar, bgcolor)

    def _create(self, plottypes, gss, dataset, model,
                prec, sumUp, boxLabels, hoverInfo,
                invert, linlg_pcntle, minProbClipForWeighting,
                directGSTmodels, dscomparator, stabilityanalyzer, submatrices,
                typ, scale, comm, wildcard, colorbar, bgcolor):

        probs_precomp_dict = None
        fig = None
        addl_hover_info_fns = _collections.OrderedDict()

        #TODO REMOVE?
        # Could do this to get counts for all spam labels
        #spamlabels = model.get_spam_labels()
        #cntMxs  = _ph.count_matrices( plaq_ds, dataset, spamlabels)
        #return _list_spam_dimension(cntMxs, "%d")

        #DEBUG: for checking
        #def _addl_mx_fn_chk(plaq,x,y):
        #    gsplaq_ds = plaq.expand_aliases(dataset)
        #    spamlabels = model.get_spam_labels()
        #    cntMxs  = _ph.total_count_matrix(   gsplaq_ds, dataset)[None,:,:]
        #    probMxs = _ph.probability_matrices( plaq, model, spamlabels,
        #                                    probs_precomp_dict)
        #    freqMxs = _ph.frequency_matrices(   gsplaq_ds, dataset, spamlabels)
        #    logLMxs = _tools.two_delta_loglfn( cntMxs, probMxs, freqMxs, 1e-4)
        #    return logLMxs.sum(axis=0) # sum over spam labels

        # End "Additional sub-matrix" functions

        if isinstance(plottypes, str):
            plottypes = [plottypes]

        plottypes_that_need_precomp = ('chi2', 'logl', 'tvd')
        if any([(t in plottypes) for t in plottypes_that_need_precomp]):  # bulk-compute probabilities for performance
            probs_precomp_dict = self._ccompute(_ph._computeProbabilities,
                                                gss, model, dataset,
                                                comm=comm, smartc=self.ws.smartCache,
                                                wildcard=wildcard)

        for ptyp in plottypes:
            if ptyp == "chi2":
                colormapType = "linlog"
                linlog_color = "red"
                ytitle = "chi<sup>2</sup>"
                mx_fn = _mx_fn_chi2  # use a *global* function so cache can tell it's the same
                extra_arg = (dataset, model, minProbClipForWeighting, probs_precomp_dict)

                # (function, extra_arg) tuples
                addl_hover_info_fns['outcomes'] = (_addl_mx_fn_sl, None)
                addl_hover_info_fns['p'] = (_addl_mx_fn_p, (model, probs_precomp_dict))
                addl_hover_info_fns['f'] = (_addl_mx_fn_f, (model, dataset, self.ws.smartCache))
                addl_hover_info_fns['total counts'] = (_addl_mx_fn_cnt, (model, dataset, self.ws.smartCache))

            elif ptyp == "logl":
                colormapType = "linlog"
                linlog_color = "red"
                ytitle = "2 log(L ratio)"
                mx_fn = _mx_fn_logl  # use a *global* function so cache can tell it's the same
                extra_arg = (dataset, model, minProbClipForWeighting, probs_precomp_dict)

                # (function, extra_arg) tuples
                addl_hover_info_fns['outcomes'] = (_addl_mx_fn_sl, None)
                addl_hover_info_fns['p'] = (_addl_mx_fn_p, (model, probs_precomp_dict))
                addl_hover_info_fns['f'] = (_addl_mx_fn_f, (model, dataset, self.ws.smartCache))
                addl_hover_info_fns['total counts'] = (_addl_mx_fn_cnt, (model, dataset, self.ws.smartCache))
                #DEBUG: addl_hover_info_fns['chk'] = _addl_mx_fn_chk

            elif ptyp == "tvd":
                colormapType = "blueseq"
                ytitle = "Total Variational Distance (TVD)"
                mx_fn = _mx_fn_tvd  # use a *global* function so cache can tell it's the same
                extra_arg = (dataset, model, probs_precomp_dict)

                # (function, extra_arg) tuples
                addl_hover_info_fns['outcomes'] = (_addl_mx_fn_sl, None)
                addl_hover_info_fns['p'] = (_addl_mx_fn_p, (model, probs_precomp_dict))
                addl_hover_info_fns['f'] = (_addl_mx_fn_f, (model, dataset, self.ws.smartCache))
                addl_hover_info_fns['total counts'] = (_addl_mx_fn_cnt, (model, dataset, self.ws.smartCache))

            elif ptyp == "blank":
                colormapType = "trivial"
                ytitle = ""
                mx_fn = _mx_fn_blank  # use a *global* function so cache can tell it's the same
                extra_arg = gss

            elif ptyp == "errorrate":
                colormapType = "seq"
                ytitle = "error rate"
                mx_fn = _mx_fn_errorrate  # use a *global* function so cache can tell it's the same
                extra_arg = directGSTmodels
                assert(sumUp is True), "Can only use 'errorrate' plot with sumUp == True"

            elif ptyp == "directchi2":
                colormapType = "linlog"
                linlog_color = "yellow"
                ytitle = "chi<sup>2</sup>"
                mx_fn = _mx_fn_directchi2  # use a *global* function so cache can tell it's the same
                extra_arg = (dataset, directGSTmodels, minProbClipForWeighting, gss)

            elif ptyp == "directlogl":
                colormapType = "linlog"
                linlog_color = "yellow"
                ytitle = "Direct 2 log(L ratio)"
                mx_fn = _mx_fn_directlogl  # use a *global* function so cache can tell it's the same
                extra_arg = (dataset, directGSTmodels, minProbClipForWeighting, gss)

            elif ptyp == "dscmp":
                assert(dscomparator is not None), \
                    "Must specify `dscomparator` argument to create `dscmp` plot!"
                colormapType = "manuallinlog"
                linlog_color = "green"
                linlog_trans = dscomparator.get_LLR_pseudothreshold()
                ytitle = "2 log(L ratio)"
                mx_fn = _mx_fn_dscmp  # use a *global* function so cache can tell it's the same
                extra_arg = dscomparator

                # if dataset is None: # then set dataset to be first compared dataset (for
                #                     # extracting # degrees of freedom below)
                #     if isinstance(dscomparator.dataset_list_or_multidataset,list):
                #         dataset = dscomparator.dataset_list_or_multidataset[0]
                #     elif isinstance(dscomparator.dataset_list_or_multidataset,_objs.MultiDataSet):
                #         key0 = list(dscomparator.dataset_list_or_multidataset.keys())[0]
                #         dataset = dscomparator.dataset_list_or_multidataset[key0]

            elif ptyp == "driftdetector":

                assert(stabilityanalyzer is not None), \
                    "Must specify `stabilityanalyzer` argument to create `drift` plot!"
                # If stabilityanalyzer  is a tuple, we expand into its components
                if isinstance(stabilityanalyzer, tuple):

                    detectorkey = stabilityanalyzer[1]
                    test = stabilityanalyzer[2]
                    stabilityanalyzer = stabilityanalyzer[0]
                # If stabilityanalyzer is a StabilityAnalyzer, we initialize the other components not given
                else:
                    detectorkey = None
                    test = None

                # If these componentes aren't given, we use defaults
                if detectorkey is None: detectorkey = stabilityanalyzer._def_detection
                if test is None: test = ('circuit', )
                assert('circuit' in test), \
                    "Cannot create this plot unless considering a per-circuit instability test!"
                test = stabilityanalyzer._equivalent_implemented_test(test, detectorkey)
                assert(test is not None), \
                    "The automatic test that we default to was not implemented! Must specify the test to use!"
                assert(len(stabilityanalyzer.data.keys()) == 1), \
                    "Currently cannot create a box-plot for multi-DataSet StabilityAnalyzers!"

                colormapType = "manuallinlog"
                linlog_color = "green"
                pvaluethreshold, junk = stabilityanalyzer.get_pvalue_threshold(test, detectorkey=detectorkey)
                linlog_trans = -1 * _np.log10(pvaluethreshold)
                ytitle = "Evidence for instability as quantified by -log10(pvalue)"
                mx_fn = _mx_fn_driftpv  # use a *global* function so cache can tell it's the same
                extra_arg = (stabilityanalyzer, test)

            elif ptyp == "driftsize":

                assert(stabilityanalyzer is not None), \
                    "Must specify `stabilityanalyzer` argument to create `drift` plot!"
                # If stabilityanalyzer  is a tuple, we expand into its components
                if isinstance(stabilityanalyzer, tuple):

                    estimatekey = stabilityanalyzer[1]
                    estimator = stabilityanalyzer[2]
                    stabilityanalyzer = stabilityanalyzer[0]
                # If stabilityanalyzer is a StabilityAnalyzer, we initialize the other components not given
                else:
                    estimatekey = None
                    estimator = None

                colormapType = "blueseq"
                ytitle = "Total Variational Distance (TVD) Bound"
                mx_fn = _mx_fn_drifttvd  # use a *global* function so cache can tell it's the same
                extra_arg = (stabilityanalyzer, estimatekey, estimator)

            # future: delete this, or update it and added it back in.
            # elif ptyp == "driftpwr":
            #     assert(driftresults is not None), \
            #         "Must specify `driftresults` argument to create `driftpv` plot!"
            #     detectorkey = driftresults[1]
            #     driftresults = driftresults[0]
            #     assert(driftresults.number_of_entities == 1), \
            #         "Currently cannot create a box-plot for multi-entity DriftResults!"
            #     colormapType = "manuallinlog"
            #     linlog_color = "green"
            #     linlog_trans = driftresults.get_power_significance_threshold(sequence='per', detectorkey=detectorkey)
            #     ytitle = "Maximum power in spectrum"
            #     mx_fn = _mx_fn_driftpwr  # use a *global* function so cache can tell it's the same
            #     extra_arg = driftresults

            elif (submatrices is not None) and ptyp in submatrices:
                ytitle = ptyp
                colormapType = submatrices.get(ptyp + ".colormap", "seq")
            else:
                raise ValueError("Invalid plot type: %s" % ptyp)

            if (submatrices is not None) and ptyp in submatrices:
                subMxs = submatrices[ptyp]  # "custom" type -- all mxs precomputed by user
            else:
                subMxs = self._ccompute(_ph._computeSubMxs, gss, model, mx_fn, dataset, extra_arg)

            addl_hover_info = _collections.OrderedDict()
            for lbl, (addl_mx_fn, addl_extra_arg) in addl_hover_info_fns.items():
                if (submatrices is not None) and lbl in submatrices:
                    addl_subMxs = submatrices[lbl]  # ever useful?
                else:
                    addl_subMxs = self._ccompute(_ph._computeSubMxs, gss, model, addl_mx_fn, dataset, addl_extra_arg)
                addl_hover_info[lbl] = addl_subMxs

            if colormapType == "linlog":
                if dataset is None:
                    _warnings.warn("No dataset specified: using DOF-per-element == 1")
                    element_dof = 1
                else:
                    #element_dof = len(dataset.get_outcome_labels()) - 1
                    #Instead of the above, which doesn't work well when there are circuits with different
                    # outcomes, the line below just takes the average degrees of freedom per circuit
                    element_dof = dataset.get_degrees_of_freedom(gss.allstrs) / len(gss.allstrs)

                n_boxes, dof_per_box = _ph._compute_num_boxes_dof(subMxs, sumUp, element_dof)
                # NOTE: currently dof_per_box is constant, and takes the total
                # number of outcome labels in the DataSet, which can be incorrect
                # when different sequences have different outcome labels.

            if len(subMxs) > 0:
                dataMax = max([(0 if (mx is None or _np.all(_np.isnan(mx))) else _np.nanmax(mx))
                               for subMxRow in subMxs for mx in subMxRow])
            else: dataMax = 0

            if colormapType == "linlog":
                colormap = _colormaps.LinlogColormap(0, dataMax, n_boxes,
                                                     linlg_pcntle, dof_per_box, linlog_color)
            elif colormapType == "manuallinlog":
                colormap = _colormaps.LinlogColormap.manual_transition_pt(
                    0, dataMax, linlog_trans, linlog_color)

            elif colormapType == "trivial":
                colormap = _colormaps.SequentialColormap(vmin=0, vmax=1)

            elif colormapType in ("seq", "revseq", "blueseq", "redseq"):
                if len(subMxs) > 0:
                    max_abs = max([_np.max(_np.abs(_np.nan_to_num(subMxs[iy][ix])))
                                   for ix in range(len(gss.used_xvals()))
                                   for iy in range(len(gss.used_yvals()))])
                else: max_abs = 0
                if max_abs == 0: max_abs = 1e-6  # pick a nonzero value if all entries are zero or nan
                if colormapType == "seq": color = "whiteToBlack"
                elif colormapType == "revseq": color = "blackToWhite"
                elif colormapType == "blueseq": color = "whiteToBlue"
                elif colormapType == "redseq": color = "whiteToRed"
                colormap = _colormaps.SequentialColormap(vmin=0, vmax=max_abs, color=color)

            else: assert(False), "Internal logic error"  # pragma: no cover

            if typ == "boxes":
                newfig = circuit_color_boxplot(gss, subMxs, colormap,
                                               colorbar, boxLabels, prec,
                                               hoverInfo, sumUp, invert,
                                               scale, bgcolor, addl_hover_info)

            elif typ == "scatter":
                newfig = circuit_color_scatterplot(gss, subMxs, colormap,
                                                   colorbar, hoverInfo, sumUp, ytitle,
                                                   scale, addl_hover_info)
            elif typ == "histogram":
                newfig = circuit_color_histogram(gss, subMxs, colormap,
                                                 ytitle, scale)
            else:
                raise ValueError("Invalid `typ` argument: %s" % typ)

            if fig is None:
                fig = newfig
            else:
                newfig.plotlyfig['data'][0].update(visible=False)
                combined_fig_data = list(fig.plotlyfig['data']) + [newfig.plotlyfig['data'][0]]
                fig = ReportFigure(go.Figure(data=combined_fig_data, layout=fig.plotlyfig['layout']),
                                   fig.colormap, fig.pythonvalue)  # just add newfig's data
                #Note: can't do fig.plotlyfig['data'].append(newfig.plotlyfig['data'][0]) as of plotly v3

        nTraces = len(fig.plotlyfig['data'])
        assert(nTraces >= len(plottypes))  # not == b/c histogram adds line trace

        if len(plottypes) > 1:
            buttons = []
            for i, nm in enumerate(plottypes):
                visible = [False] * nTraces
                visible[i] = True
                buttons.append(
                    dict(args=['visible', visible],
                         label=nm,
                         method='restyle'))
            fig.plotlyfig['layout'].update(
                updatemenus=list([
                    dict(buttons=buttons,
                         direction='left',
                         pad={'r': 10, 't': 10},
                         showactive=True, type='buttons',
                         x=0.1, xanchor='left',
                         y=1.1, yanchor='top')
                ]))

        #colormap2 = _colormaps.LinlogColormap(0, dataMax, n_boxes, linlg_pcntle, dof_per_box, "blue")
        #fig2 = circuit_color_boxplot(gss, subMxs, colormap2,
        #                                False, boxLabels, prec, hoverInfo, sumUp, invert)
        #fig['data'].append(fig2['data'][0])
        #fig['layout'].update(
        #    )
        return fig

#Helper function for ColorBoxPlot matrix computation


def _mx_fn_chi2(plaq, x, y, extra):
    dataset, model, minProbClipForWeighting, probs_precomp_dict = extra
    return _ph.chi2_matrix(plaq, dataset, model, minProbClipForWeighting,
                           probs_precomp_dict)


def _mx_fn_logl(plaq, x, y, extra):
    dataset, model, minProbClipForWeighting, probs_precomp_dict = extra
    return _ph.logl_matrix(plaq, dataset, model, minProbClipForWeighting,
                           probs_precomp_dict)


def _mx_fn_tvd(plaq, x, y, extra):
    dataset, model, probs_precomp_dict = extra
    return _ph.tvd_matrix(plaq, dataset, model,
                          probs_precomp_dict)


def _mx_fn_blank(plaq, x, y, gss):
    return _np.nan * _np.zeros((len(gss.minor_yvals()),
                                len(gss.minor_xvals())), 'd')


def _mx_fn_errorrate(plaq, x, y, directGSTmodels):  # error rate as 1x1 matrix which we have plotting function sum up
    return _np.array([[_ph.small_eigval_err_rate(plaq.base, directGSTmodels)]])


def _mx_fn_directchi2(plaq, x, y, extra):
    dataset, directGSTmodels, minProbClipForWeighting, gss = extra
    return _ph.direct_chi2_matrix(
        plaq, gss, dataset, directGSTmodels.get(plaq.base, None),
        minProbClipForWeighting)


def _mx_fn_directlogl(plaq, x, y, extra):
    dataset, directGSTmodels, minProbClipForWeighting, gss = extra
    return _ph.direct_logl_matrix(
        plaq, gss, dataset, directGSTmodels.get(plaq.base, None),
        minProbClipForWeighting)


def _mx_fn_dscmp(plaq, x, y, dscomparator):
    return _ph.dscompare_llr_matrices(plaq, dscomparator)


def _mx_fn_driftpv(plaq, x, y, instabilityanalyzertuple):
    return _ph.drift_neglog10pvalue_matrices(plaq, instabilityanalyzertuple)


def _mx_fn_drifttvd(plaq, x, y, instabilityanalyzertuple):
    return _ph.drift_maxtvd_matrices(plaq, instabilityanalyzertuple)

# future: delete this, or update it and added it back in.
# def _mx_fn_driftpwr(plaq, x, y, driftresults):
#     return _ph.drift_maxpower_matrices(plaq, driftresults)

# Begin "Additional sub-matrix" functions for adding more info to hover text


def _separate_outcomes_matrix(plaq, elements, fmt="%.3g"):
    list_mx = _np.empty((plaq.rows, plaq.cols), dtype=_np.object)
    for i, j, _, elIndices, _ in plaq.iter_simplified():
        list_mx[i, j] = ", ".join(["NaN" if _np.isnan(x) else
                                   (fmt % x) for x in elements[elIndices]])
    return list_mx


def _outcome_to_str(x):  # same function as in writers.py
    if isinstance(x, str): return x
    else: return ":".join([str(i) for i in x])


def _addl_mx_fn_sl(plaq, x, y, extra):
    slmx = _np.empty((plaq.rows, plaq.cols), dtype=_np.object)
    for i, j, opstr, elIndices, outcomes in plaq.iter_simplified():
        slmx[i, j] = ", ".join([_outcome_to_str(ol) for ol in outcomes])
    return slmx


def _addl_mx_fn_p(plaq, x, y, extra):
    model, probs_precomp_dict = extra
    probs = _ph.probability_matrices(plaq, model,
                                     probs_precomp_dict)
    return _separate_outcomes_matrix(plaq, probs, "%.5g")


def _addl_mx_fn_f(plaq, x, y, extra):
    model, dataset, smartc = extra
    plaq_ds = smartc.cached_compute(plaq.expand_aliases,
                                    (dataset,), dict(circuit_simplifier=model))[1]  # doesn't seem to work yet...
    freqs = _ph.frequency_matrices(plaq_ds, dataset)
    return _separate_outcomes_matrix(plaq, freqs, "%.5g")


def _addl_mx_fn_cnt(plaq, x, y, extra):
    model, dataset, smartc = extra
    plaq_ds = smartc.cached_compute(plaq.expand_aliases,
                                    (dataset,), dict(circuit_simplifier=model))[1]
    cnts = _ph.total_count_matrix(plaq_ds, dataset)
    return _separate_outcomes_matrix(plaq, cnts, "%d")


#def gate_matrix_boxplot(opMatrix, size=None, m=-1.0, M=1.0,
#                        save_to=None, fontSize=20, mxBasis=None,
#                        mxBasisDims=None, xlabel=None, ylabel=None,
#                        title=None, boxLabels=False, prec=0, mxBasisDimsY=None):
class GateMatrixPlot(WorkspacePlot):
    """
    Plot of a operation matrix using colored boxes.  More specific than MatrixPlot
    because of basis formatting for x and y labels.
    """
    # separate in rendering/saving: size=None,fontSize=20, save_to=None, title=None, scale

    def __init__(self, ws, opMatrix, m=-1.0, M=1.0,
                 mxBasis=None, xlabel=None, ylabel=None,
                 boxLabels=False, colorbar=None, prec=0, mxBasisY=None,
                 scale=1.0, EBmatrix=None):
        """
        Creates a color box plot of a operation matrix using a diverging color map.

        This can be a useful way to display large matrices which have so many
        entries that their entries cannot easily fit within the width of a page.

        Parameters
        ----------
        opMatrix : ndarray
          The operation matrix data to display.

        m, M : float, optional
          Min and max values of the color scale.

        mxBasis : str or Basis object, optional
          The basis, often of `opMatrix`, used to create the x-labels (and
          y-labels when `mxBasisY` is None). Typically in {"pp","gm","std","qt"}.
          If you don't want labels, leave as None.

        xlabel : str, optional
          An x-axis label for the plot.

        ylabel : str, optional
          A y-axis label for the plot.

        boxLabels : bool, optional
          Whether box labels are displayed.

        colorbar : bool optional
          Whether to display a color bar to the right of the box plot.  If None,
          then a colorbar is displayed when `boxLabels == False`.

        prec : int or {'compact','compacthp'}, optional
            Precision for box labels.  Only relevant when boxLabels == True. Allowed
            values are:

            - 'compact' = round to nearest whole number using at most 3 characters
            - 'compacthp' = show as much precision as possible using at most 3 characters
            - int >= 0 = fixed precision given by int
            - int <  0 = number of significant figures given by -int

        mxBasisY : str or Basis object, optional
          The basis, used to create the y-labels (for rows) when these are
          *different* from the x-labels.  Typically in
          {"pp","gm","std","qt"}.  If you don't want labels, leave as None.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        EBmatrix : numpy array, optional
            An array, of the same size as `opMatrix`, which gives error bars to be
            be displayed in the hover info.
        """
        super(GateMatrixPlot, self).__init__(ws, self._create, opMatrix, m, M,
                                             mxBasis, xlabel, ylabel,
                                             boxLabels, colorbar, prec, mxBasisY, scale, EBmatrix)

    def _create(self, opMatrix, m, M,
                mxBasis, xlabel, ylabel,
                boxLabels, colorbar, prec, mxBasisY, scale, EBmatrix):

        return opmatrix_color_boxplot(
            opMatrix, m, M, mxBasis, mxBasisY,
            xlabel, ylabel, boxLabels, colorbar, prec, scale, EBmatrix)


class MatrixPlot(WorkspacePlot):
    """ Plot of a general matrix using colored boxes """

    def __init__(self, ws, matrix, m=-1.0, M=1.0,
                 xlabels=None, ylabels=None, xlabel=None, ylabel=None,
                 boxLabels=False, colorbar=None, colormap=None, prec=0,
                 scale=1.0, grid="black"):
        """
        Creates a color box plot of a matrix using the given color map.

        This can be a useful way to display large matrices which have so many
        entries that their entries cannot easily fit within the width of a page.

        Parameters
        ----------
        matrix : ndarray
          The operation matrix data to display.

        m, M : float, optional
          Min and max values of the color scale.

        xlabels, ylabels: list, optional
          List of (str) box labels for each axis.

        xlabel : str, optional
          An x-axis label for the plot.

        ylabel : str, optional
          A y-axis label for the plot.

        boxLabels : bool, optional
          Whether box labels are displayed.

        colorbar : bool optional
          Whether to display a color bar to the right of the box plot.  If None,
          then a colorbar is displayed when `boxLabels == False`.

        colormap : Colormap, optional
          An a color map object used to convert the numerical matrix values into
          colors.

        prec : int or {'compact','compacthp'}, optional
            Precision for box labels.  Only relevant when boxLabels == True. Allowed
            values are:

            - 'compact' = round to nearest whole number using at most 3 characters
            - 'compacthp' = show as much precision as possible using at most 3 characters
            - int >= 0 = fixed precision given by int
            - int <  0 = number of significant figures given by -int

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        grid : {"white","black",None}
            What color grid lines, if any, to add to the plot.  Advanced usage
            allows the addition of `:N` where `N` is an integer giving the line
            width.
        """
        super(MatrixPlot, self).__init__(ws, self._create, matrix, m, M,
                                         xlabels, ylabels, xlabel, ylabel,
                                         boxLabels, colorbar, colormap, prec, scale, grid)

    def _create(self, matrix, m, M,
                xlabels, ylabels, xlabel, ylabel,
                boxLabels, colorbar, colormap, prec, scale, grid):

        if colormap is None:
            colormap = _colormaps.DivergingColormap(vmin=m, vmax=M)

        ret = matrix_color_boxplot(
            matrix, xlabels, ylabels, xlabel, ylabel,
            boxLabels, None, colorbar, colormap, prec, scale, grid=grid)
        return ret


#    evals = _np.linalg.eigvals(gate)
#    target_evals = _np.linalg.eigvals(targetOp)
#    rel_op = _np.dot(_np.linalg.inv(targetOp), gate)
#    rel_evals = _np.linalg.eigvals(rel_op)
#    rel_evals10 = rel_evals**10

class PolarEigenvaluePlot(WorkspacePlot):
    """ Polar plot of complex eigenvalues """

    def __init__(self, ws, evals_list, colors, labels=None, scale=1.0, amp=None,
                 centerText=None):
        """
        Creates a polar plot of one or more sets of eigenvalues (or any complex #s).

        Parameters
        ----------
        evals_list : list
            A list of eigenvalue arrays to display.

        colors : list
            A corresponding list of color names to use for arrays given
            by `evals_list` (must have `len(colors) == len(evals_list)`).
            Colors can be standard names, e.g. `"blue"`, or rgb strings
            such as `"rgb(23,92,64)"`.

        labels : list, optional
            A list of labels, one for each element of `evals_list` to be
            placed in the plot legend.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        amp : float, optional
            An amount to amplify (raise to the exponent `amp`) each set of
            eigenvalues.  (Amplified eigenvalues are shown in the same color
            but with smaller markers.) If `amp` is None, no amplification is
            performed.

        centerText : str, optional
            Text to be placed at the very center of the polar plot (sometimes
            useful to use as a title).
        """
        super(PolarEigenvaluePlot, self).__init__(ws, self._create, evals_list,
                                                  colors, labels, scale, amp,
                                                  centerText)

    def _create(self, evals_list, colors, labels, scale, amp, centerText):

        annotations = []
        if centerText is not None:
            annotations.append(
                dict(text=centerText,
                     r=0, t=0,
                     font=dict(size=10 * scale,
                               color="black",
                               showarrow=False)
                     ))

        #Note: plotly needs a plain lists for r and t, otherwise it
        # produces javascript [ [a], [b], ... ] instead of [a, b, ...]
        data = []
        for i, evals in enumerate(evals_list):
            color = colors[i] if (colors is not None) else "black"
            trace = go.Scatter(
                r=list(_np.absolute(evals).flat),
                t=list(_np.angle(evals).flatten() * (180.0 / _np.pi)),
                mode='markers',
                marker=dict(
                    color=color,
                    size=45,
                    line=dict(
                        color='white'
                    ),
                    opacity=0.7
                ))
            if labels is None or len(labels[i]) == 0:
                trace.update(showlegend=False)
            else:
                trace.update(name=labels[i])
            data.append(trace)

            #Add amplified eigenvalues
            if amp is not None:
                amp_evals = evals**amp
                trace = go.Scatter(
                    r=list(_np.absolute(amp_evals).flat),
                    t=list(_np.angle(amp_evals).flatten() * (180.0 / _np.pi)),
                    showlegend=False,
                    mode='markers',
                    marker=dict(
                        color=color,
                        size=20,
                        line=dict(
                            color='white'
                        ),
                        opacity=0.5
                    ))
                #if labels is not None:
                #    trace.update(name="%s^%g" % (labels[i],amp))
                data.append(trace)

        layout = go.Layout(
            width=300 * scale,
            height=300 * scale,
            #title='Test Polar',
            #font=dict(size=10),
            plot_bgcolor='rgb(240, 240, 240)',
            radialaxis=dict(
                range=[0, 1.25]),
            angularaxis=dict(
                tickcolor='rgb(180,180,180)',
                #range=[0,2]
                #ticktext=['A','B','C','D']
            ),
            direction="counterclockwise",
            orientation=-90
        )

        #HACK around plotly bug: Plotly somehow holds residual polar plot data
        # which gets plotted unless new data overwrites it.  This residual data
        # takes up 4 points of data for the first 3 data traces - so we make
        # sure this data is filled in with undisplayed data here (because we
        # don't want to see the residual data!).
        for trace in data:
            if len(trace['r']) < 4:  # hopefully never needed
                extra = 4 - len(trace['r'])  # pragma: no cover
                trace['r'] += [1e3] * extra  # pragma: no cover
                trace['t'] += [0.0] * extra  # pragma: no cover
        while len(data) < 3:
            data.append(go.Scatter(
                r=[1e3] * 4,
                t=[0.0] * 4,
                name="Dummy",
                mode='markers',
                showlegend=False,
            ))
        assert(len(data) >= 3)

        pythonVal = {}
        for i, tr in enumerate(data):
            key = tr['name'] if ("name" in tr) else "trace%d" % i
            pythonVal[key] = {'r': tr['r'], 't': tr['t']}

        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, pythonVal)


class ProjectionsBoxPlot(WorkspacePlot):
    """ Plot of matrix of (usually error-generator) projections """

    def __init__(self, ws, projections, projection_basis, m=None, M=None,
                 boxLabels=False, colorbar=None, prec="compacthp", scale=1.0,
                 EBmatrix=None, title=None):
        """
        Creates a color box plot displaying projections.

        Typically `projections` is obtained by calling
        :func:`std_errgen_projections`, and so holds the projections of a gate
        error generator onto the generators corresponding to a set of standard
        errors constructed from the given basis.

        Parameters
        ----------
        projections : ndarray
          A 1-dimensional array of length equal to the numer of elements in
          the given basis (usually equal to the gate dimension).  Ordering of
          the values is assumed to correspond to the ordering given by the
          routines in `pygsti.tools`, (e.g. :func:`pp_matrices` when
          `projection_basis` equals "pp").

        projection_basis : {'std', 'gm', 'pp', 'qt'}
          The basis is used to construct the error generators onto which
          the gate  error generator is projected.  Allowed values are
          Matrix-unit (std), Gell-Mann (gm), Pauli-product (pp) and Qutrit (qt).

        m,M : float, optional
          Color scale min and max values, respectivey.  If None, then computed
          automatically from the data range.

        boxLabels : bool, optional
          Whether box labels are displayed.

        colorbar : bool optional
          Whether to display a color bar to the right of the box plot.  If None,
          then a colorbar is displayed when `boxLabels == False`.

        prec : int or {'compact','compacthp'}, optional
            Precision for box labels.  Only relevant when boxLabels == True. Allowed
            values are:

            - 'compact' = round to nearest whole number using at most 3 characters
            - 'compacthp' = show as much precision as possible using at most 3 characters
            - int >= 0 = fixed precision given by int
            - int <  0 = number of significant figures given by -int

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        EBmatrix : numpy array, optional
            An array, of the same size as `projections`, which gives error bars to be
            be displayed in the hover info.

        title : str, optional
            A title for the plot
        """
        super(ProjectionsBoxPlot, self).__init__(ws, self._create, projections,
                                                 projection_basis, m, M,
                                                 boxLabels, colorbar, prec, scale,
                                                 EBmatrix, title)

    def _create(self, projections,
                projection_basis, m, M,
                boxLabels, colorbar, prec, scale,
                EBmatrix, title):

        absMax = _np.max(_np.abs(projections))
        if m is None: m = -absMax
        if M is None: M = absMax

        d2 = len(projections)  # number of projections == dim of gate
        d = _np.sqrt(d2)  # dim of density matrix
        nQubits = _np.log2(d)

        if not _np.isclose(round(nQubits), nQubits):
            #Non-integral # of qubits, so just show as a single row
            projections = projections.reshape((1, projections.size))
            xlabel = ""; ylabel = ""
        elif nQubits == 1:
            projections = projections.reshape((1, 4))
            xlabel = "Q1"; ylabel = ""
        elif nQubits == 2:
            projections = projections.reshape((4, 4))
            xlabel = "Q2"; ylabel = "Q1"
        else:
            projections = projections.reshape((4, projections.size // 4))
            xlabel = "Q*"; ylabel = "Q1"

        if EBmatrix is not None:
            EBmatrix = EBmatrix.reshape(projections.shape)

        xd = projections.shape[1]  # x-basis-dim
        yd = projections.shape[0]  # y-basis-dim

        if isinstance(projection_basis, _objs.Basis):
            if isinstance(projection_basis, _objs.TensorProdBasis) and len(projection_basis.component_bases) == 2 \
               and xd == projection_basis.component_bases[0].dim and yd == projection_basis.component_bases[1].dim:
                basis_for_xlabels = projection_basis.component_bases[0]
                basis_for_ylabels = projection_basis.component_bases[1]
            elif xd == projection_basis.dim and yd == 1:
                basis_for_xlabels = projection_basis
                basis_for_ylabels = None
            elif xd == yd == projection_basis.dim:
                basis_for_xlabels = projection_basis
                basis_for_ylabels = projection_basis
            else:
                try:
                    basis_for_xlabels = _objs.BuiltinBasis(projection_basis.name, xd)
                    basis_for_ylabels = _objs.BuiltinBasis(projection_basis.name, yd)
                except:
                    basis_for_xlabels = basis_for_ylabels = None
        else:
            try:
                basis_for_xlabels = _objs.BuiltinBasis(projection_basis, xd)
                basis_for_ylabels = _objs.BuiltinBasis(projection_basis, yd)
            except:
                basis_for_xlabels = basis_for_ylabels = None

        return opmatrix_color_boxplot(
            projections, m, M,
            basis_for_xlabels,
            basis_for_ylabels,
            xlabel, ylabel, boxLabels, colorbar, prec,
            scale, EBmatrix, title)


#    def choi_eigenvalue_barplot(evals, errbars=None, size=(8,5), barWidth=1,
#                            save_to=None, fontSize=15, xlabel="index",
#                            ylabel="Re[eigenvalue]", title=None):

# xlabel="index", ylabel="Re[eigenvalue]", title=None
# TODO: maybe a "postFormat" or "addToFigure" fn to add title & axis labels to any figure?
class ChoiEigenvalueBarPlot(WorkspacePlot):
    """ Bar plot of eigenvalues showing red bars for negative values """

    def __init__(self, ws, evals, errbars=None, scale=1.0):
        """
        Creates a bar plot showing the real parts of each of the eigenvalues
        given.  This is useful for plotting the eigenvalues of Choi matrices,
        since all elements are positive for a CPTP map.

        Parameters
        ----------
        evals : ndarray
           An array containing the eigenvalues to plot.

        errbars : ndarray, optional
           An array containing the lengths of the error bars
           to place on each bar of the plot.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.
        """
        super(ChoiEigenvalueBarPlot, self).__init__(ws, self._create, evals,
                                                    errbars, scale)

    def _create(self, evals, errbars, scale):

        HOVER_PREC = 7
        xs = list(range(evals.size))
        ys = []; colors = []; texts = []
        for i, ev in enumerate(evals.flatten()):
            ys.append(abs(ev.real))
            colors.append('rgb(200,200,200)' if ev.real > 0 else 'red')
            if errbars is not None:
                texts.append("%g +/- %g" % (round(ev.real, HOVER_PREC),
                                            round(errbars.flatten()[i].real, HOVER_PREC)))
            else:
                texts.append("%g" % round(ev.real, HOVER_PREC))

        trace = go.Bar(
            x=xs, y=ys, text=texts,
            marker=dict(color=colors),
            hoverinfo='text'
        )

        LOWER_LOG_THRESHOLD = -6  # so don't plot all the way down to, e.g., 1e-13
        ys = _np.clip(ys, 1e-30, 1e100)  # to avoid log(0) errors
        log_ys = _np.log10(_np.array(ys, 'd'))
        minlog = max(_np.floor(min(log_ys)) - 0.1, LOWER_LOG_THRESHOLD)
        maxlog = max(_np.ceil(max(log_ys)), minlog + 1)

        #Set plot size and margins
        lmargin = rmargin = tmargin = bmargin = 10
        lmargin += 30  # for y-tics
        bmargin += 40  # for x-tics & xlabel

        width = lmargin + max(20 * len(xs), 120) + rmargin
        height = tmargin + 120 + bmargin

        width *= scale
        height *= scale
        lmargin *= scale
        rmargin *= scale
        tmargin *= scale
        bmargin *= scale

        data = [trace]
        layout = go.Layout(
            width=width,
            height=height,
            margin=go_Margin(l=lmargin, r=rmargin, b=bmargin, t=tmargin),
            xaxis=dict(
                title="index",
                tickvals=xs
            ),
            yaxis=dict(
                type='log',
                range=[minlog, maxlog]
            ),
            bargap=0.02
        )

        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, evals, plt_y=evals, plt_yerr=errbars,
                            pythonErrorBar=errbars)


class GramMatrixBarPlot(WorkspacePlot):
    """ Bar plot of Gram matrix eigenvalues stacked against those of target """

    def __init__(self, ws, dataset, target, maxlen=10,
                 fixedLists=None, scale=1.0):
        """
        Creates a bar plot showing eigenvalues of the Gram matrix compared to
        those of the a target model's Gram matrix.

        Parameters
        ----------
        dataset : DataSet
            The DataSet

        target : Model
            A target model which is used for it's mapping of SPAM labels to
            SPAM specifiers and for Gram matrix comparision.

        maxlen : integer, optional
            The maximum length string used when searching for the
            maximal (best) Gram matrix.  It's useful to make this
            at least twice the maximum length fiducial sequence.

        fixedLists : (prepStrs, effectStrs), optional
            2-tuple of operation sequence lists, specifying the preparation and
            measurement fiducials to use when constructing the Gram matrix,
            and thereby bypassing the search for such lists.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.
        """
        super(GramMatrixBarPlot, self).__init__(ws, self._create,
                                                dataset, target, maxlen, fixedLists, scale)

    def _create(self, dataset, target, maxlen, fixedLists, scale):

        if fixedLists is not None and \
                (len(fixedLists[0]) == 0 or len(fixedLists[1]) == 0):
            #Empty fixed lists => create empty gram plot
            svals = target_svals = _np.array([], 'd')
        else:
            _, svals, target_svals = _alg.max_gram_rank_and_evals(dataset, target, maxlen, fixedLists)
            svals = _np.sort(_np.abs(svals)).reshape(-1, 1)
            target_svals = _np.sort(_np.abs(target_svals)).reshape(-1, 1)

        xs = list(range(svals.size))
        trace1 = go.Bar(
            x=xs, y=list(svals.flatten()),
            marker=dict(color="blue"),
            hoverinfo='y',
            name="from Data"
        )
        trace2 = go.Bar(
            x=xs, y=list(target_svals.flatten()),
            marker=dict(color="black"),
            hoverinfo='y',
            name="from Target"
        )

        if svals.size > 0:
            ymin = min(_np.min(svals), _np.min(target_svals))
            ymax = max(_np.max(svals), _np.max(target_svals))
            ymin = max(ymin, 1e-8)  # prevent lower y-limit from being riduculously small
        else:
            ymin = 0.1; ymax = 1.0  # just pick some values for empty plot

        data = [trace1, trace2]
        layout = go.Layout(
            width=400 * scale,
            height=300 * scale,
            xaxis=dict(
                title="index",
                tickvals=xs
            ),
            yaxis=dict(
                title="eigenvalue",
                type='log',
                exponentformat='power',
                range=[_np.log10(ymin), _np.log10(ymax)],
            ),
            bargap=0.1
        )

        pythonVal = {}
        for tr in data:
            pythonVal[tr['name']] = tr['y']
        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, pythonVal)


class FitComparisonBarPlot(WorkspacePlot):
    """ Bar plot showing the overall (aggregate) goodness of fit
        (along one dimension)"""

    def __init__(self, ws, Xs, gssByX, modelByX, datasetByX,
                 objective="logl", Xlabel='L', NpByX=None, scale=1.0,
                 comm=None, wildcard=None, minProbClip=1e-4):
        """
        Creates a bar plot showing the overall (aggregate) goodness of fit
        for one or more model estimates to corresponding data sets.

        Parameters
        ----------
        Xs : list of integers
            List of X-values. Typically these are the maximum lengths or
            exponents used to index the different iterations of GST.

        gssByX : list of LsGermsStructure
            Specifies the set (& structure) of the operation sequences used at each X.

        modelByX : list of Models
            `Model`s corresponding to each X value.

        datasetByX : DataSet or list of DataSets
            The data sets to compare each model against.  If a single
            :class:`DataSet` is given, then it is used for all comparisons.

        objective : {"logl", "chi2"}, optional
            Whether to use log-likelihood or chi^2 values.

        Xlabel : str, optional
            A label for the 'X' variable which indexes the different models.
            This string will be the x-label of the resulting bar plot.

        NpByX : list of ints, optional
            A list of parameter counts to use for each X.  If None, then
            the number of non-gauge parameters for each model is used.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        comm : mpi4py.MPI.Comm, optional
            When not None, an MPI communicator for distributing the computation
            across multiple processors.

        wildcard : WildcardBudget
            A wildcard budget to apply to the objective function (`objective`),
            which increases the goodness of fit by adjusting (by an amount
            measured in TVD) the probabilities produced by a model before
            comparing with the frequencies in `dataset`.  Currently, this
            functionality is only supported for `objective == "logl"`.

        minProbClip : float, optional
            The minimum probability treated normally in the evaluation of the log-likelihood.
            A penalty function replaces the true log-likelihood for probabilities that lie
            below this threshold so that the log-likelihood never becomes undefined (which improves
            optimizer performance).
        """
        super(FitComparisonBarPlot, self).__init__(ws, self._create,
                                                   Xs, gssByX, modelByX, datasetByX,
                                                   objective, Xlabel, NpByX, scale,
                                                   comm, wildcard, minProbClip)

    def _create(self, Xs, gssByX, modelByX, datasetByX, objective, Xlabel,
                NpByX, scale, comm, wildcard, minProbClip):

        xs = list(range(len(Xs)))
        xtics = []; ys = []; colors = []; texts = []

        if NpByX is None:
            try:
                NpByX = [mdl.num_nongauge_params() if (mdl is not None) else 0
                         for mdl in modelByX]  # Note: models can be None => N/A
            except:  # numpy can throw a LinAlgError
                _warnings.warn(("FigComparisonBarPlot could not obtain number of"
                                " *non-gauge* parameters - using total params instead"))
                NpByX = [mdl.num_params() if (mdl is not None) else 0
                         for mdl in modelByX]

        if isinstance(datasetByX, _objs.DataSet):
            datasetByX = [datasetByX] * len(modelByX)

        for X, mdl, gss, dataset, Np in zip(Xs, modelByX, gssByX, datasetByX, NpByX):
            if gss is None or mdl is None:
                Nsig, rating = _np.nan, 5
            else:
                Nsig, rating, _, _, _, _ = self._ccompute(_ph.ratedNsigma, dataset, mdl,
                                                          gss, objective, Np, returnAll=True,
                                                          comm=comm, smartc=self.ws.smartCache,
                                                          wildcard=wildcard, minProbClip=minProbClip)
                #Note: don't really need returnAll=True, but helps w/caching b/c other fns use it.

            if rating == 5: color = "darkgreen"
            elif rating == 4: color = "lightgreen"
            elif rating == 3: color = "yellow"
            elif rating == 2: color = "orange"
            else: color = "red"

            xtics.append(str(X))
            ys.append(Nsig)
            texts.append("%g<br>rating: %d" % (Nsig, rating))
            colors.append(color)

        MIN_BAR = 1e-4  # so all bars have positive height (since log scale)
        plotted_ys = [max(y, MIN_BAR) for y in ys]
        trace = go.Bar(
            x=xs, y=plotted_ys, text=texts,
            marker=dict(color=colors),
            hoverinfo='text'
        )

        #Set plot size and margins
        lmargin = rmargin = tmargin = bmargin = 10
        if Xlabel: bmargin += 20
        lmargin += 20  # y-label is always present
        if xtics:
            max_xl = max([len(xl) for xl in xtics])
            if max_xl > 0: bmargin += max_xl * 5
        lmargin += 20  # for y-labels (guess)

        width = lmargin + max(30 * len(xs), 150) + rmargin
        height = tmargin + 200 + bmargin

        width *= scale
        height *= scale
        lmargin *= scale
        rmargin *= scale
        tmargin *= scale
        bmargin *= scale

        data = [trace]
        layout = go.Layout(
            width=width,
            height=height,
            margin=go_Margin(l=lmargin, r=rmargin, b=bmargin, t=tmargin),
            xaxis=dict(
                title=Xlabel,
                tickvals=xs,
                ticktext=xtics
            ),
            yaxis=dict(
                title="N<sub>sigma</sub>",
                type='log'
            ),
            bargap=0.1
        )
        if len(plotted_ys) == 0:
            layout['yaxis']['range'] = [_np.log10(0.1),
                                        _np.log10(1.0)]  # empty plot: range doesn't matter
        elif max(plotted_ys) < 1.0:
            layout['yaxis']['range'] = [_np.log10(min(plotted_ys) / 2.0),
                                        _np.log10(1.0)]
        else:
            layout['yaxis']['range'] = [_np.log10(min(plotted_ys) / 2.0),
                                        _np.log10(max(plotted_ys) * 2.0)]

        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, {'x': xs, 'y': ys})


class FitComparisonBoxPlot(WorkspacePlot):
    """ Box plot showing the overall (aggregate) goodness of fit
        (along 2 dimensions)"""

    def __init__(self, ws, Xs, Ys, gssByYthenX, modelByYthenX, datasetByYthenX,
                 objective="logl", Xlabel=None, Ylabel=None, scale=1.0, comm=None,
                 wildcard=None, minProbClip=1e-4):
        """
        Creates a box plot showing the overall (aggregate) goodness of fit
        for one or more model estimates to their respective  data sets.

        Parameters
        ----------
        Xs, Ys : list
            List of X-values and Y-values (converted to strings).

        gssByYthenX : list of lists of LsGermsStructure objects
            Specifies the set (& structure) of the operation sequences used at each Y
            and X value, indexed as `gssByYthenX[iY][iX]`, where `iX` and `iY`
            are X and Y indices, respectively.

        modelByYthenX : list of lists of Models
            `Model`s corresponding to each X and Y value.

        datasetByYthenX : list of lists of DataSets
            `DataSet`s corresponding to each X and Y value.

        objective : {"logl", "chi2"}, optional
            Whether to use log-likelihood or chi^2 values.

        Xlabel, Ylabel : str, optional
            Labels for the 'X' and 'Y' variables which index the different gate
            sets. These strings will be the x- and y-label of the resulting box
            plot.

        scale : float, optional
            Scaling factor to adjust the size of the final figure.

        comm : mpi4py.MPI.Comm, optional
            When not None, an MPI communicator for distributing the computation
            across multiple processors.

        wildcard : WildcardBudget
            A wildcard budget to apply to the objective function (`objective`),
            which increases the goodness of fit by adjusting (by an amount
            measured in TVD) the probabilities produced by a model before
            comparing with the frequencies in `dataset`.  Currently, this
            functionality is only supported for `objective == "logl"`.

        minProbClip : float, optional
            The minimum probability treated normally in the evaluation of the log-likelihood.
            A penalty function replaces the true log-likelihood for probabilities that lie
            below this threshold so that the log-likelihood never becomes undefined (which improves
            optimizer performance).
        """
        super(FitComparisonBoxPlot, self).__init__(
            ws, self._create, Xs, Ys, gssByYthenX, modelByYthenX,
            datasetByYthenX, objective, Xlabel, Ylabel, scale, comm,
            wildcard, minProbClip)

    def _create(self, Xs, Ys, gssByYX, modelByYX, datasetByYX, objective,
                Xlabel, Ylabel, scale, comm, wildcard, minProbClip):

        xlabels = list(map(str, Xs))
        ylabels = list(map(str, Ys))

        NsigMx = _np.empty((len(Ys), len(Xs)), 'd')
        cmap = _colormaps.PiecewiseLinearColormap(
            [[0, (0, 0.5, 0)], [2, (0, 0.5, 0)],  # rating=5 darkgreen
             [20, (0, 1.0, 0)],  # rating=4 lightgreen
             [100, (1.0, 1.0, 0)],  # rating=3 yellow
             [500, (1.0, 0.5, 0)],  # rating=2 orange
             [1000, (1.0, 0, 0)]])  # rating=1 red

        for iY, Y in enumerate(Ys):
            for iX, X in enumerate(Xs):
                dataset = datasetByYX[iY][iX]
                mdl = modelByYX[iY][iX]
                gss = gssByYX[iY][iX]

                if dataset is None or gss is None or mdl is None:
                    NsigMx[iY][iX] = _np.nan
                    continue

                Nsig, rating, _, _, _, _ = self._ccompute(
                    _ph.ratedNsigma, dataset, mdl, gss, objective,
                    returnAll=True, comm=comm, smartc=self.ws.smartCache,
                    wildcard=wildcard, minProbClip=minProbClip)
                NsigMx[iY][iX] = Nsig

        return matrix_color_boxplot(
            NsigMx, xlabels, ylabels, Xlabel, Ylabel,
            boxLabels=True, colorbar=False, colormap=cmap,
            prec='compact', scale=scale, grid="white")


class DatasetComparisonSummaryPlot(WorkspacePlot):
    """ A grid of grayscale boxes comparing data sets pair-wise."""

    def __init__(self, ws, dslabels, dsc_dict, scale=1.0):
        """
        Creates a plot showing the total 2*deltaLogL values for each pair of
        DataSets out of some number of total DataSets.

        Background: For every pair of data sets, the likelihood is computed for
        two different models: 1) the model in which a single set of
        probabilities (one per gate sequence, obtained by the combined outcome
        frequencies) generates both data sets, and 2) the model in which each
        data is generated from different sets of probabilities.  Twice the ratio
        of these log-likelihoods can be compared to the value that is expected
        when model 1) is valid.  This plot shows the difference between the
        expected and actual twice-log-likelihood ratio in units of standard
        deviations.  Zero or negative values indicate the data sets appear to be
        generated by the same underlying probabilities.  Large positive values
        indicate the data sets appear to be generated by different underlying
        probabilities.

        Parameters
        ----------
        dslabels : list
            A list of data set labels, specifying the ordering and the number
            of data sets.

        dsc_dict : dict
            A dictionary of `DataComparator` objects whose keys are 2-tuples of
            integers such that the value associated with `(i,j)` is a
            `DataComparator` object that compares the `i`-th and `j`-th data
            sets (as indexed by `dslabels`.
        """
        super(DatasetComparisonSummaryPlot, self).__init__(ws, self._create, dslabels, dsc_dict, scale)

    def _create(self, dslabels, dsc_dict, scale):
        nSigmaMx = _np.zeros((len(dslabels), len(dslabels)), 'd') * _np.nan
        logLMx = _np.zeros((len(dslabels), len(dslabels)), 'd') * _np.nan
        max_nSigma = max_2DeltaLogL = 0.0
        for i, _ in enumerate(dslabels):
            for j, _ in enumerate(dslabels[i + 1:], start=i + 1):
                dsc = dsc_dict.get((i, j), dsc_dict.get((j, i), None))
                val = dsc.aggregate_nsigma if (dsc is not None) else None
                nSigmaMx[i, j] = nSigmaMx[j, i] = val
                if val and val > max_nSigma: max_nSigma = val

                val = dsc.aggregate_llr if (dsc is not None) else None
                logLMx[i, j] = logLMx[j, i] = val
                if val and val > max_2DeltaLogL: max_2DeltaLogL = val

        colormap = _colormaps.SequentialColormap(vmin=0, vmax=max_nSigma)
        nSigma_fig = matrix_color_boxplot(
            nSigmaMx, dslabels, dslabels, "Dataset 1", "Dataset 2",
            boxLabels=True, prec=1, colormap=colormap, scale=scale)

        colormap = _colormaps.SequentialColormap(vmin=0, vmax=max_2DeltaLogL)
        logL_fig = matrix_color_boxplot(
            logLMx, dslabels, dslabels, "Dataset 1", "Dataset 2",
            boxLabels=True, prec=1, colormap=colormap, scale=scale)

        #Combine plotly figures into one
        nSigma_figdict = nSigma_fig.plotlyfig.to_dict()  # so we can work with normal dicts
        # and not weird plotly objects.  Older versions of plotly do not support this syntax, so upgrade if needed.
        logL_figdict = logL_fig.plotlyfig.to_dict()
        combined_fig_data = list(nSigma_figdict['data']) + [logL_figdict['data'][0]]
        combined_fig_data[-1].update(visible=False)
        combined_fig = ReportFigure(go.Figure(data=combined_fig_data, layout=nSigma_figdict['layout']),
                                    nSigma_fig.colormap, nSigma_fig.pythonvalue)

        annotations = [nSigma_figdict['layout']['annotations'],
                       logL_figdict['layout']['annotations']]

        buttons = []; nTraces = 2
        for i, nm in enumerate(['Nsigma', '2DeltaLogL']):
            visible = [False] * nTraces
            visible[i] = True
            buttons.append(
                dict(args=[{'visible': visible},
                           {'annotations': annotations[i]}],
                     label=nm,
                     method='update'))  # 'restyle'
        #.update( updatemenus=
        combined_fig.plotlyfig['layout']['updatemenus'] = list([
            dict(buttons=buttons,
                 direction='left',
                 #pad = {'r': 1, 'b': 1},
                 showactive=True, type='buttons',
                 x=0.0, xanchor='left',
                 y=-0.1, yanchor='top')
        ])  # )
        m = combined_fig.plotlyfig['layout']['margin']
        w = combined_fig.plotlyfig['layout']['width']
        h = combined_fig.plotlyfig['layout']['height']
        exr = 0 if w > 240 else 240 - w  # extend to right
        combined_fig.plotlyfig['layout'].update(
            margin=go_Margin(l=m['l'], r=m['r'] + exr, b=m['b'] + 40, t=m['t']),
            width=w + exr,
            height=h + 40
        )

        return combined_fig


class DatasetComparisonHistogramPlot(WorkspacePlot):
    """ Histogram of p-values comparing two data sets """

    def __init__(self, ws, dsc, nbins=50, frequency=True,
                 log=True, display='pvalue', scale=1.0):
        super(DatasetComparisonHistogramPlot, self).__init__(ws, self._create, dsc, nbins, frequency,
                                                             log, display, scale)

    def _create(self, dsc, nbins, frequency, log, display, scale):
        if display == 'llr' and nbins is None:
            nbins = len(dsc.llrs)

        TOL = 1e-10
        pVals = _np.array(list(dsc.pVals.values()), 'd')
        pVals_nz = _np.array([x for x in pVals if abs(x) > TOL])
        pVals0 = (len(pVals) - len(pVals_nz)) if log else dsc.pVals0
        llrVals = _np.array(list(dsc.llrs.values()), 'd')

        if log:
            if len(pVals_nz) == 0:
                minval = maxval = thres = 0.0
                lastBinCount = 0
            else:
                minval = _np.floor(_np.log10(min(pVals_nz)))
                maxval = _np.ceil(_np.log10(max(pVals_nz)))
                thres = (maxval - minval) / (nbins - 1) * (nbins - 2)
                lastBinCount = (_np.log10(pVals_nz) > thres).sum()
                #Kenny: why use this as a normalization?  Is this correct?
        else:
            minval = min(pVals)
            maxval = max(pVals)
            thres = (maxval - minval) / (nbins - 1) * (nbins - 2)
            lastBinCount = (pVals > thres).sum()

        if display == 'pvalue':
            norm = 'probability' if frequency else 'count'
            vals = _np.log10(pVals_nz) if log else pVals
            cumulative = dict(enabled=False)
            barcolor = '#43C6DB'  # turquoise
        elif display == 'llr':
            norm = 'probability'
            vals = _np.log10(llrVals) if log else llrVals
            cumulative = dict(enabled=True)
            barcolor = '#FFD801'  # rubber ducky yellow
        else:
            raise ValueError("Invalid display value: %s" % display)

        histTrace = go.Histogram(
            x=vals, histnorm=norm,
            autobinx=False,
            xbins=dict(
                start=minval,
                end=maxval,
                size=(maxval - minval) / (nbins - 1)
            ),
            cumulative=cumulative,
            marker=dict(color=barcolor),
            opacity=0.75,
            showlegend=False,
        )

        if display == 'pvalue':
            bin_edges = _np.linspace(minval, maxval, nbins)
            linear_bin_edges = 10**(bin_edges) if log else bin_edges
            M = 1.0 if frequency else lastBinCount

            noChangeTrace = go.Scatter(
                x=bin_edges,
                y=M * _scipy.stats.chi2.pdf(
                    _scipy.stats.chi2.isf(linear_bin_edges, dsc.dof), dsc.dof),
                mode="lines",
                marker=dict(
                    color='rgba(0,0,255,0.8)',
                    line=dict(
                        width=2,
                    )),
                name='No-change prediction'
            )

            data = [histTrace, noChangeTrace]
            xlabel = 'p-value'
            ylabel = "Relative frequency" if frequency else "Number of occurrences"
            title = 'p-value histogram for experimental coins;'

        elif display == 'llr':
            data = [histTrace]
            xlabel = 'log-likelihood'
            ylabel = 'Cumulative frequency'
            title = 'Cumulative log-likelihood ratio histogram for experimental coins;'

        if log:
            minInt = int(_np.floor(minval))
            maxInt = int(_np.ceil(maxval))
            xaxis_dict = dict(
                title=xlabel,
                tickvals=list(range(minInt, maxInt + 1)),
                ticktext=["10<sup>%d</sup>" % i for i in range(minInt, maxInt + 1)]
            )
        else:
            xaxis_dict = dict(title=xlabel)  # auto-tick labels

        datasetnames = dsc.DS_names
        if dsc.op_exclusions:
            title += ' ' + str(dsc.op_exclusions) + ' excluded'
            if dsc.op_inclusions:
                title += ';'
        if dsc.op_inclusions:
            title += ' ' + str(dsc.op_inclusions) + ' included'
        title += '<br>Comparing datasets ' + str(datasetnames)
        title += ' p=0 ' + str(pVals0) + ' times; ' + str(len(dsc.pVals)) + ' total sequences'

        layout = go.Layout(
            width=700 * scale,
            height=400 * scale,
            title=title,
            font=dict(size=10),
            xaxis=xaxis_dict,
            yaxis=dict(
                title=ylabel,
                type='log' if log else 'linear',
                #tickformat='g',
                exponentformat='power',
            ),
            bargap=0,
            bargroupgap=0,
            legend=dict(orientation="h")
        )

        pythonVal = {'histogram values': vals}
        if display == 'pvalue':
            pythonVal['noChangeTrace'] = {'x': noChangeTrace['x'], 'y': noChangeTrace['y']}
        return ReportFigure(go.Figure(data=data, layout=layout),
                            None, pythonVal)


class RandomizedBenchmarkingPlot(WorkspacePlot):
    """ Plot of RB Decay curve """

    def __init__(self, ws, rbR, fitkey=None, decay=True,
                 success_probabilities=True, ylim=None, xlim=None,
                 showpts=True, legend=True, title=None, scale=1.0):
        """
        Plot RB decay curve, as a function of sequence length.  Optionally
        includes a fitted exponential decay.

        Parameters
        ----------
        rbR : RandomizedBenchmarkingResults
            The RB results object containing all the relevant RB data.

        fitkey : dict key, optional
            The key of the self.fits dictionary to plot the fit for. If None, will
            look for a 'full' key (the key for a full fit to A + Bp^m if the standard
            analysis functions are used) and plot this if possible. It otherwise checks
            that there is only one key in the dict and defaults to this. If there are
            multiple keys and none of them are 'full', `fitkey` must be specified when
            `decay` is True.

        decay : bool, optional
            Whether to plot a fit, or just the data.

        success_probabilities : bool, optional
            Whether to plot the success probabilities distribution, as a
            "box & whisker" plot.

        ylim, xlim : tuple, optional
            The x and y limits for the figure.

        showpts : bool, optional
            When `success_probabilities == True`, whether individual points
            should be shown along with a "box & whisker".

        legend : bool, optional
            Whether to show a legend.

        title : str, optional
            A title to put on the figure.

        Returns
        -------
        None
        """
        super(RandomizedBenchmarkingPlot, self).__init__(
            ws, self._create, rbR, fitkey, decay, success_probabilities,
            ylim, xlim, showpts, legend, title, scale)

    def _create(self, rbR, fitkey, decay, success_probabilities, ylim, xlim,
                showpts, legend, title, scale):

        if decay and fitkey is None:
            allfitkeys = list(rbR.fits.keys())
            if 'full' in allfitkeys:
                fitkey = 'full'
            elif len(allfitkeys) == 1:
                fitkey = allfitkeys[0]
            else:
                raise ValueError(("There are multiple fits and none have the "
                                  "key 'full'. Please specify the fit to plot!"))

        ASPs = []  # (avg success probs)
        data_per_depth = rbR.data.cache[rbR.protocol.datatype]
        for depth in rbR.depths:
            percircuitdata = data_per_depth[depth]
            ASPs.append(_np.mean(percircuitdata))  # average [adjusted] success probabilities

        xdata = _np.asarray(rbR.depths)
        ydata = _np.asarray(ASPs)

        data = []  # list of traces
        data.append(go.Scatter(
            x=xdata, y=ydata,
            mode='markers',
            marker=dict(
                color="rgb(0,0,0)",
                size=5
            ),
            name='Average success probabilities',
            showlegend=legend,
        ))

        if decay:
            lengths = _np.linspace(0, max(rbR.depths), 200)
            A = rbR.fits[fitkey].estimates['A']
            B = rbR.fits[fitkey].estimates['B']
            p = rbR.fits[fitkey].estimates['p']

            data.append(go.Scatter(
                x=lengths,
                y=A + B * p**lengths,
                mode='lines',
                line=dict(width=1, color="rgb(120,120,120)"),
                name='Fit, r = {:.2} +/- {:.1}'.format(rbR.fits[fitkey].estimates['r'],
                                                       rbR.fits[fitkey].stds['r']),
                showlegend=legend,
            ))

        if success_probabilities:
            all_success_probs_by_depth = [data_per_depth[depth] for depth in rbR.depths]
            for depth, prob_dist in zip(rbR.depths, all_success_probs_by_depth):
                data.append(go.Box(
                    x0=depth, y=prob_dist,
                    whiskerwidth=0.2, opacity=0.7, showlegend=False,
                    boxpoints='all' if showpts else False,
                    pointpos=0, jitter=0.5,
                    boxmean=False,  # or True or 'sd'
                    hoveron="boxes", hoverinfo="all",
                    name='m=%d' % depth))

        #pad by 10%
        ymin = min(ydata)
        ymin -= 0.1 * abs(1.0 - ymin)
        xmin = -0.1 * max(xdata)
        xmax = max(xdata) * 1.1

        layout = go.Layout(
            width=800 * scale,
            height=400 * scale,
            title=title,
            titlefont=dict(size=16),
            xaxis=dict(
                title="RB sequence length (m)",
                titlefont=dict(size=14),
                range=xlim if xlim else [xmin, xmax],
            ),
            yaxis=dict(
                title="Success probability",
                titlefont=dict(size=14),
                range=ylim if ylim else [ymin, 1.0],
            ),
            legend=dict(
                x=0.5, y=1.2,
                font=dict(
                    size=13
                ),
            )
        )

        pythonVal = {}
        for i, tr in enumerate(data):
            if 'x0' in tr: continue  # don't put boxes in python val for now
            key = tr['name'] if ("name" in tr) else "trace%d" % i
            pythonVal[key] = {'x': tr['x'], 'y': tr['y']}

        #reverse order of data so z-ordering is nicer
        return ReportFigure(go.Figure(data=list(data), layout=layout),
                            None, pythonVal)


#This older version on an RB decay plot contained a lot more theory detail
# compared with the current one - so we'll keep it around (commented out)
# in case we want to steal/revive pieces of it in the future.
#class OLDRandomizedBenchmarkingPlot(WorkspacePlot):
#     """ Plot of RB Decay curve """
#     def __init__(self, ws, rbR,xlim=None, ylim=None,
#                  fit='standard', Magesan_zeroth=False, Magesan_first=False,
#                  exact_decay=False,L_matrix_decay=False, Magesan_zeroth_SEB=False,
#                  Magesan_first_SEB=False, L_matrix_decay_SEB=False,mdl=False,
#                  target_model=False,group=False, group_to_model=None, norm='1to1', legend=True,
#                  title='Randomized Benchmarking Decay', scale=1.0):
#         """
#         Plot RB decay curve, as a function of some the sequence length
#         computed using the `gstyp` gate-label-set.
#
#         Parameters
#         ----------
#         rbR : RBResults
#             The RB results object containing all the relevant RB data.
#
#         gstyp : str, optional
#             The gate-label-set specifying which translation (i.e. strings with
#             which operation labels) to use when computing sequence lengths.
#
#         xlim : tuple, optional
#             The x-range as (xmin,xmax).
#
#         ylim : tuple, optional
#             The y-range as (ymin,ymax).
#
#         save_fig_path : str, optional
#             If not None, the filename where the resulting plot should be saved.
#
#         fitting : str, optional
#             Allowed values are 'standard', 'first order' or 'all'. Specifies
#             whether the zeroth or first order fitting model results are plotted,
#             or both.
#
#         Magesan_zeroth : bool, optional
#             If True, plots the decay predicted by the 'zeroth order' theory of Magesan
#             et al. PRA 85 042311 2012. Requires mdl and target_model to be specified.
#
#         Magesan_first : bool, optional
#             If True, plots the decay predicted by the 'first order' theory of Magesan
#             et al. PRA 85 042311 2012. Requires mdl and target_model to be specified.
#
#         Magesan_zeroth_SEB : bool, optional
#             If True, plots the systematic error bound for the 'zeroth order' theory
#             predicted decay. This is the region around the zeroth order decay in which
#             the exact RB average survival probabilities are guaranteed to fall.
#
#         Magesan_first_SEB : bool, optional
#             As above, but for 'first order' theory.
#
#         exact_decay : bool, optional
#             If True, plots the exact RB decay, as predicted by the 'R matrix' theory
#             of arXiv:1702.01853. Requires mdl and group to be specified
#
#         L_matrix_decay : bool, optional
#             If True, plots the RB decay, as predicted by the approximate 'L matrix'
#             theory of arXiv:1702.01853. Requires mdl and target_model to be specified.
#
#         L_matrix_decay_SEB : bool, optional
#             If True, plots the systematic error bound for approximate 'L matrix'
#             theory of arXiv:1702.01853. This is the region around predicted decay
#             in which the exact RB average survival probabilities are guaranteed
#             to fall.
#
#         mdl : model, optional
#             Required, if plotting any of the theory decays. The model for which
#             these decays should be plotted for.
#
#         target_model : Model, optional
#             Required, if plotting certain theory decays. The target model for which
#             these decays should be plotted for.
#
#         group : MatrixGroup, optional
#             Required, if plotting R matrix theory decay. The matrix group that mdl
#             is an implementation of.
#
#         group_to_model : dict, optional
#             If not None, a dictionary that maps labels of group elements to labels
#             of mdl. Only used if subset_sampling is not None. If subset_sampling is
#             not None and the mdl and group elements have the same labels, this dictionary
#             is not required. Otherwise it is necessary.
#
#         norm : str, optional
#             The norm used for calculating the Magesan theory bounds.
#
#         legend : bool, optional
#             Specifies whether a legend is added to the graph
#
#         title : str, optional
#             Specifies a title for the graph
#
#         Returns
#         -------
#         None
#         """
# #         loc : str, optional
# #            Specifies the location of the legend.
#         super(RandomizedBenchmarkingPlot,self).__init__(
#             ws, self._create, rbR, xlim, ylim, fit, Magesan_zeroth,
#             Magesan_first, exact_decay, L_matrix_decay, Magesan_zeroth_SEB,
#             Magesan_first_SEB, L_matrix_decay_SEB, mdl, target_model, group,
#             group_to_model, norm, legend, title, scale)
#
#     def _create(self, rbR, xlim, ylim, fit, Magesan_zeroth,
#                 Magesan_first, exact_decay, L_matrix_decay, Magesan_zeroth_SEB,
#                 Magesan_first_SEB, L_matrix_decay_SEB, mdl, target_model, group,
#                 group_to_model, norm, legend, title, scale):
#
#         from ..extras.rb import rbutils as _rbutils
#         #TODO: maybe move the computational/fitting part of this function
#         #  back to the RBResults object to reduce the logic (and dependence
#         #  on rbutils) here.
#
#         #newplot = _plt.figure(figsize=(8, 4))
#         #newplotgca = newplot.gca()
#
#         # Note: minus one to get xdata that discounts final Clifford-inverse
#         xdata = _np.asarray(rbR.results['lengths']) - 1
#         ydata = _np.asarray(rbR.results['successes'])
#         A = rbR.results['A']
#         B = rbR.results['B']
#         f = rbR.results['f']
#         if fit == 'first order':
#             C = rbR.results['C']
#         pre_avg = rbR.pre_avg
#
#         if (Magesan_zeroth_SEB is True) and (Magesan_zeroth is False):
#             print("As Magesan_zeroth_SEB is True, Setting Magesan_zeroth to True\n")
#             Magesan_zeroth = True
#         if (Magesan_first_SEB is True) and (Magesan_first is False):
#             print("As Magesan_first_SEB is True, Setting Magesan_first to True\n")
#             Magesan_first = True
#
#         if (Magesan_zeroth is True) or (Magesan_first is True):
#             if (mdl is False) or (target_model is False):
#                 raise ValueError("To plot Magesan et al theory decay curves a model" +
#                            " and a target model is required.")
#             else:
#                 MTP = _rbutils.Magesan_theory_parameters(mdl, target_model,
#                                                 success_outcomelabel=rbR.success_outcomelabel,
#                                                          norm=norm,d=rbR.d)
#                 f_an = MTP['p']
#                 A_an = MTP['A']
#                 B_an = MTP['B']
#                 A1_an = MTP['A1']
#                 B1_an = MTP['B1']
#                 C1_an = MTP['C1']
#                 delta = MTP['delta']
#
#         if exact_decay is True:
#             if (mdl is False) or (group is False):
#                 raise ValueError("To plot the exact decay curve a model" +
#                                  " and the target group are required.")
#             else:
#                 mvalues,ASPs = _rbutils.exact_RB_ASPs(mdl,group,max(xdata),m_min=1,m_step=1,
#                                                       d=rbR.d, group_to_model=group_to_model,
#                                                       success_outcomelabel=rbR.success_outcomelabel)
#
#         if L_matrix_decay is True:
#             if (mdl is False) or (target_model is False):
#                 raise ValueError("To plot the L matrix theory decay curve a model" +
#                            " and a target model is required.")
#             else:
#                 mvalues, LM_ASPs, LM_ASPs_SEB_lower, LM_ASPs_SEB_upper = \
#                 _rbutils.L_matrix_ASPs(mdl,target_model,max(xdata),m_min=1,m_step=1,d=rbR.d,
#                                        success_outcomelabel=rbR.success_outcomelabel, error_bounds=True)
#
#         xlabel = 'Sequence length'
#
#         data = [] # list of traces
#         data.append( go.Scatter(
#             x = xdata, y = ydata,
#             mode = 'markers',
#             marker = dict(
#                 color = "rgb(0,0,0)",
#                 size = 6 if pre_avg else 3
#             ),
#             name = 'Averaged RB data' if pre_avg else 'RB data',
#         ))
#
#         if fit=='standard' or fit=='first order':
#             fit_label_1='Fit'
#             fit_label_2='Fit'
#             color2 = "black"
#
#         theory_color2 = "green"
#         theory_fill2 = "rgba(0,128,0,0.1)"
#         if Magesan_zeroth is True and Magesan_first is True:
#             theory_color2 = "magenta"
#             theory_fill2 = "rgba(255,0,255,0.1)"
#
#         if fit=='standard':
#             data.append( go.Scatter(
#                 x = _np.arange(max(xdata)),
#                 y = _rbutils.standard_fit_function(_np.arange(max(xdata)),A,B,f),
#                 mode = 'lines',
#                 line = dict(width=1, color="black"),
#                 name = fit_label_1,
#                 showlegend=legend,
#             ))
#
#         if fit=='first order':
#             data.append( go.Scatter(
#                 x = _np.arange(max(xdata)),
#                 y = _rbutils.first_order_fit_function(_np.arange(max(xdata)),A,B,C,f),
#                 mode = 'lines',
#                 line = dict(width=1, color=color2),
#                 name = fit_label_2,
#                 showlegend=legend,
#             ))
#
#         if Magesan_zeroth is True:
#             data.append( go.Scatter(
#                 x = _np.arange(max(xdata)),
#                 y = _rbutils.standard_fit_function(_np.arange(max(xdata)),A_an,B_an,f_an),
#                 mode = 'lines',
#                 line = dict(width=2, color="green", dash='dash'),
#                 name = '0th order theory',
#                 showlegend=legend,
#             ))
#
#             if Magesan_zeroth_SEB is True:
#                 data.append( go.Scatter(
#                     x = _np.arange(max(xdata)),
#                     y = _rbutils.seb_upper(
#                         _rbutils.standard_fit_function(_np.arange(max(xdata)),A_an,B_an,f_an),
#                         _np.arange(max(xdata)), delta, order='zeroth'),
#                     mode = 'lines',
#                     line = dict(width=0.5, color="green"),
#                     name = '0th order bound',
#                     fill='tonexty',
#                     fillcolor='rgba(0,128,0,0.1)',
#                     showlegend=False,
#                 ))
#                 data.append( go.Scatter(
#                     x = _np.arange(max(xdata)),
#                     y = _rbutils.seb_lower(
#                         _rbutils.standard_fit_function(_np.arange(max(xdata)),A_an,B_an,f_an),
#                         _np.arange(max(xdata)), delta, order='zeroth'),
#                     mode = 'lines',
#                     line = dict(width=0.5, color="green"),
#                     name = '0th order bound',
#                     showlegend=False,
#                 ))
#
#
#         if Magesan_first is True:
#             data.append( go.Scatter(
#                 x = _np.arange(max(xdata)),
#                 y = _rbutils.first_order_fit_function(_np.arange(max(xdata)),A1_an,B1_an,C1_an,f_an),
#                 mode = 'lines',
#                 line = dict(width=2, color=theory_color2, dash='dash'),
#                 name = '1st order theory',
#                 showlegend=legend,
#             ))
#
#             if Magesan_first_SEB is True:
#                 data.append( go.Scatter(
#                     x = _np.arange(max(xdata)),
#                     y = _rbutils.seb_upper(
#                         _rbutils.first_order_fit_function(_np.arange(max(xdata)),A1_an,B1_an,C1_an,f_an),
#                         _np.arange(max(xdata)), delta, order='first'),
#                     mode = 'lines',
#                     line = dict(width=0.5, color=theory_color2), #linewidth=4?
#                     name = '1st order bound',
#                     fill='tonexty',
#                     fillcolor=theory_fill2,
#                     showlegend=False,
#                 ))
#                 data.append( go.Scatter(
#                     x = _np.arange(max(xdata)),
#                     y = _rbutils.seb_lower(
#                         _rbutils.first_order_fit_function(_np.arange(max(xdata)),A1_an,B1_an,C1_an,f_an),
#                         _np.arange(max(xdata)), delta, order='first'),
#                     mode = 'lines',
#                     line = dict(width=0.5, color=theory_color2),
#                     name = '1st order bound',
#                     showlegend=False,
#                 ))
#
#
#         if exact_decay is True:
#             data.append( go.Scatter(
#                 x = mvalues,
#                 y = ASPs,
#                 mode = 'lines',
#                 line = dict(width=2, color="blue",dash='dash'),
#                 name = 'Exact decay',
#                 showlegend=legend,
#             ))
#
#         if L_matrix_decay is True:
#             data.append( go.Scatter(
#                 x = mvalues,
#                 y = LM_ASPs,
#                 mode = 'lines',
#                 line = dict(width=2, color="cyan",dash='dash'),
#                 name = 'L matrix decay',
#                 showlegend=legend,
#             ))
#             if L_matrix_decay_SEB is True:
#                 data.append( go.Scatter(
#                     x = mvalues,
#                     y = LM_ASPs_SEB_upper,
#                     mode = 'lines',
#                     line = dict(width=0.5, color="cyan"),
#                     name = 'LM bound',
#                     fill='tonexty',
#                     fillcolor='rgba(0,255,255,0.1)',
#                     showlegend=False,
#                 ))
#                 data.append( go.Scatter(
#                     x = mvalues,
#                     y = LM_ASPs_SEB_lower,
#                     mode = 'lines',
#                     line = dict(width=0.5, color="cyan"),
#                     name = 'LM bound',
#                     showlegend=False,
#                 ))
#
#         ymin = min([min(trace['y']) for trace in data])
#         ymin -= 0.1*abs(1.0-ymin) #pad by 10%
#
#         layout = go.Layout(
#             width=800*scale,
#             height=400*scale,
#             title=title,
#             titlefont=dict(size=16),
#             xaxis=dict(
#                 title=xlabel,
#                 titlefont=dict(size=14),
#                 range=xlim if xlim else [0,max(xdata)],
#             ),
#             yaxis=dict(
#                 title='Mean survival probability',
#                 titlefont=dict(size=14),
#                 range=ylim if ylim else [ymin,1.0],
#             ),
#             legend=dict(
#                 font=dict(
#                     size=13,
#                 ),
#             )
#         )
#
#         pythonVal = {}
#         for i,tr in enumerate(data):
#             key = tr['name'] if ("name" in tr) else "trace%d" % i
#             pythonVal[key] = {'x': tr['x'], 'y': tr['y']}
#
#         #reverse order of data so z-ordering is nicer
#         return ReportFigure(go.Figure(data=list(reversed(data)), layout=layout),
#                             None, pythonVal)
#
#         #newplotgca.set_xlabel(xlabel, fontsize=15)
#         #newplotgca.set_ylabel('Mean survival probability',fontsize=15)
#         #if title==True:
#         #    newplotgca.set_title('Randomized Benchmarking Decay', fontsize=18)
#         #newplotgca.set_frame_on(True)
#         #newplotgca.yaxis.grid(False)
#         #newplotgca.tick_params(axis='x', top='off', labelsize=12)
#         #newplotgca.tick_params(axis='y', left='off', right='off', labelsize=12)
#
#         #if legend==True:
#         #    leg = _plt.legend(fancybox=True, loc=loc)
#         #    leg.get_frame().set_alpha(0.9)
#
#         #newplotgca.spines["top"].set_visible(False)
#         #newplotgca.spines["right"].set_visible(False)
#         #newplotgca.spines["bottom"].set_alpha(.7)
#         #newplotgca.spines["left"].set_alpha(.7)


#Histograms??
#TODO: histogram
#        if histogram:
#            fig = _plt.figure()
#            histdata = subMxSums.flatten()
#            #take gives back (1,N) shaped array (why?)
#            histdata_finite = _np.take(histdata, _np.where(_np.isfinite(histdata)))[0]
#            histMin = min( histdata_finite ) if cmapFactory.vmin is None else cmapFactory.vmin
#            histMax = max( histdata_finite ) if cmapFactory.vmax is None else cmapFactory.vmax
#            _plt.hist(_np.clip(histdata_finite,histMin,histMax), histBins,
#                      range=[histMin, histMax], facecolor='gray', align='mid')
#            if save_to is not None:
#                if len(save_to) > 0:
#                    _plt.savefig( _makeHistFilename(save_to) )
#                _plt.close(fig)

#           if histogram:
#                fig = _plt.figure()
#                histdata = _np.concatenate( [ subMxs[iy][ix].flatten() for ix in range(nXs) for iy in range(nYs)] )
#                #take gives back (1,N) shaped array (why?)
#                histdata_finite = _np.take(histdata, _np.where(_np.isfinite(histdata)))[0]
#                histMin = min( histdata_finite ) if cmapFactory.vmin is None else cmapFactory.vmin
#                histMax = max( histdata_finite ) if cmapFactory.vmax is None else cmapFactory.vmax
#                _plt.hist(_np.clip(histdata_finite,histMin,histMax), histBins,
#                          range=[histMin, histMax], facecolor='gray', align='mid')
#                if save_to is not None:
#                    if len(save_to) > 0:
#                        _plt.savefig( _makeHistFilename(save_to) )
#                    _plt.close(fig)
