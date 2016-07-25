import unittest
import pygsti

arbitraryNum = 1.819743 # Six digits after decimal
roundedNum   = 1.82     # Two digits after decimal

# ppt format ommitted because the string it produces isn't necessarily in the correct order 
#   -> if latex and html pass, it will likely pass as well
# text formatting has also been ommitted, since providing it with a precision has no effect

# Constant values for checking against
latexString = '\\begin{tabular}[l]{|c|}\n\hline\n%s \\\\ \hline\n\end{tabular}\n'
htmlString  = '<table class=pygstiTbl><thead><tr><th> %s </th></tr></thead><tbody></tbody></table>'

precise   = {
    'html'  : htmlString  % arbitraryNum,
    'latex' : latexString % arbitraryNum}

imprecise = {
    'html'  : htmlString  % roundedNum,
    'latex' : latexString % roundedNum}

class PrecisionTest(unittest.TestCase):

    def test_precision_formatting(self):
        headings   = [arbitraryNum]
        formatters = ['Precision']
        table      = pygsti.report.table.ReportTable(headings, formatters)

        # Precise first
        for fmt in ['html', 'latex']: # text format ommitted - it doesn't care about precision :)
            self.assertEqual(precise[fmt], table.render(fmt, precision=6, polarprecision=3)) 

        # Imprecise second
        for fmt in ['html', 'latex']:
            self.assertEqual(imprecise[fmt], table.render(fmt, precision=2, polarprecision=3)) 

    def test_dual_render_call(self):
        headings   = [arbitraryNum]
        formatters = ['Precision']
        table      = pygsti.report.table.ReportTable(headings, formatters) 

        table.render('latex', precision=6)

        with self.assertRaises(ValueError):
            # Check if FormatSet detects no update to 'precision' spec, 
            #   even though formatDict['Precision']['latex'].specs['precision'] 
            #   is currently set to 6 (from above)
            table.render('latex', precision=None) 

if __name__ == '__main__':
    unittest.main(verbosity=2)
