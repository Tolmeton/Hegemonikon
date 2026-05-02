import sys
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード")
from hermeneus.src.parser import CCLParser
from hermeneus.src.ccl_ast import Variable, Workflow, OpType, Sequence

class TestCCLProjection(unittest.TestCase):
    def setUp(self):
        self.parser = CCLParser()

    def test_variable_projection(self):
        ast = self.parser.parse("$result.insight")
        self.assertIsInstance(ast, Variable)
        self.assertEqual(ast.name, "$result")
        self.assertEqual(ast.projection, "insight")
        
        ast2 = self.parser.parse("¥[raw_data]")
        self.assertIsInstance(ast2, Variable)
        self.assertEqual(ast2.name, "¥[raw_data]")
        self.assertIsNone(ast2.projection)

        ast3 = self.parser.parse("#[processed].value")
        self.assertIsInstance(ast3, Variable)
        self.assertEqual(ast3.name, "#[processed]")
        self.assertEqual(ast3.projection, "value")

        ast4 = self.parser.parse("$var")
        self.assertIsInstance(ast4, Variable)
        self.assertEqual(ast4.name, "$var")
        self.assertIsNone(ast4.projection)

    def test_workflow_projection(self):
        ast = self.parser.parse("/noe+.insight")
        self.assertIsInstance(ast, Workflow)
        self.assertEqual(ast.id, "noe")
        self.assertIn(OpType.DEEPEN, ast.operators)
        self.assertEqual(ast.projection, "insight")

        ast2 = self.parser.parse("/noe.insight")
        self.assertIsInstance(ast2, Workflow)
        self.assertEqual(ast2.id, "noe")
        self.assertEqual(ast2.projection, "insight")

        ast3 = self.parser.parse("/noe.d.insight")
        self.assertIsInstance(ast3, Sequence)
        self.assertEqual(ast3.steps[-1].id, "zet")
        self.assertEqual(ast3.steps[-1].projection, "insight")

        ast4 = self.parser.parse("/noe.VF+")
        self.assertIsInstance(ast4, Workflow)
        self.assertEqual(ast4.id, "noe")
        self.assertIn(OpType.DEEPEN, ast4.operators)
        self.assertEqual(ast4.modifiers.get("_x_dot"), "VF")
        self.assertIsNone(ast4.relation)
        self.assertIsNone(ast4.projection)

if __name__ == '__main__':
    unittest.main()
