import unittest
import pygsti

# ppt format ommitted because the string it produces isn't necessarily in the correct order
#   -> if latex and html pass, it will likely pass as well
# text formatting has also been ommitted, since providing it with a precision has no effect

from ..testutils import BaseTestCase, compare_files, temp_files

class FormatterBaseTestCase(BaseTestCase):
    def setUp(self):
        super(FormatterBaseTestCase, self).setUp()

        self.arbitraryNum = 1.819743 # Six digits after decimal
        self.roundedNum   = 1.82     # Two digits after decimal

        latexString = '\\begin{tabular}[l]{|c|}\n\hline\n%s \\\\ \hline\n\end{tabular}\n'
        htmlString  = '<table class=pygstiTbl><thead><tr><th> %s </th></tr></thead><tbody></tbody></table>'

        self.precise   = {
            'html'  : htmlString  % self.arbitraryNum,
            'latex' : latexString % self.arbitraryNum}

        self.imprecise = {
            'html'  : htmlString  % self.roundedNum,
            'latex' : latexString % self.roundedNum}

class PrecisionTest(FormatterBaseTestCase):

    def setUp(self):
        super(PrecisionTest, self).setUp()

        headings   = [self.arbitraryNum]
        formatters = ['Precision']
        self.table = pygsti.report.table.ReportTable(headings, formatters)

    def test_precision_formatting(self):
        # Precise first
        for fmt in ['html', 'latex']: # text format ommitted - it doesn't care about precision :)
            self.assertEqual(self.precise[fmt], self.table.render(fmt, precision=6, polarprecision=3))

        # Imprecise second
        for fmt in ['html', 'latex']:
            self.assertEqual(self.imprecise[fmt], self.table.render(fmt, precision=2, polarprecision=3))

    def test_dual_render_call(self):
        self.table.render('latex', precision=6)
        with self.assertRaises(ValueError):
            # Check if FormatSet detects no update to 'precision' spec,
            #   even though formatDict['Precision']['latex'].specs['precision']
            #   is currently set to 6 (from above)
            self.table.render('latex', precision=None)

    def test_unsupplied_spec(self):
        with self.assertRaises(ValueError):
            self.table.render('latex', precision=None)

if __name__ == '__main__':
    unittest.main(verbosity=2)
