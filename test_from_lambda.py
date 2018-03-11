import unittest
import from_lambda

class TestFromLambda(unittest.TestCase):
    @staticmethod
    def parse_to_str(l):
        return from_lambda.to_str(from_lambda.parse_lambda(l))

    def test_binary(self):
        self.assertEqual('lambda x: x + 1', self.parse_to_str(lambda x: x + 1))
        self.assertEqual('lambda x: x + 1 + a', self.parse_to_str(lambda x: x + 1 + a))
        self.assertEqual('lambda x: x + 1 + a', self.parse_to_str(lambda x: (x + 1) + a))
        self.assertEqual('lambda x: x + (1 + a)', self.parse_to_str(lambda x: x + (1 + a)))
        self.assertEqual('lambda x: (x + 1) * a', self.parse_to_str(lambda x: (x + 1) * a))
        self.assertEqual('lambda: a ** b ** c', self.parse_to_str(lambda: a ** b ** c))
        self.assertEqual('lambda: a ** b ** c', self.parse_to_str(lambda: a ** (b ** c)))
        self.assertEqual('lambda: (a ** b) ** c', self.parse_to_str(lambda: (a ** b) ** c))

    def test_and_or(self):
        self.assertEqual('lambda: a and b', self.parse_to_str(lambda: a and b))
        self.assertEqual('lambda: a or b', self.parse_to_str(lambda: a or b))
        self.assertEqual('lambda: a and b and c', self.parse_to_str(lambda: a and b and c))
        self.assertEqual('lambda: a or b or c', self.parse_to_str(lambda: a or b or c))
        self.assertEqual('lambda: a and b or c', self.parse_to_str(lambda: a and b or c))
        self.assertEqual('lambda: a or b and c', self.parse_to_str(lambda: a or b and c))
        self.assertEqual('lambda: a and (b or c)', self.parse_to_str(lambda: a and (b or c)))
        self.assertEqual('lambda: (a or b) and c', self.parse_to_str(lambda: (a or b) and c))
        self.assertEqual('lambda: (a and b) + 1', self.parse_to_str(lambda: (a and b) + 1))

    def test_if_else(self):
        self.assertEqual('lambda: a if b else c', self.parse_to_str(lambda: a if b else c))
        self.assertEqual('lambda: a if not b else c', self.parse_to_str(lambda: a if not b else c))
        self.assertEqual('lambda: a if b else c if d else e', self.parse_to_str(lambda: a if b else c if d else e))
        self.assertEqual('lambda: a if b else c if d else e', self.parse_to_str(lambda: a if b else (c if d else e)))
        self.assertEqual('lambda: a if (b if c else d) else e', self.parse_to_str(lambda: a if (b if c else d) else e))
        self.assertEqual('lambda: (a if b else c) + 1', self.parse_to_str(lambda: (a if b else c) + 1))

    def test_build_literal(self):
        self.assertEqual('lambda: 1', self.parse_to_str(lambda: 1))
        self.assertEqual('lambda: [1, 2, 3]', self.parse_to_str(lambda: [1, 2, 3]))
        self.assertEqual('lambda: []', self.parse_to_str(lambda: []))
        self.assertEqual('lambda: (1, 2, 3)', self.parse_to_str(lambda: (1, 2, 3)))
        self.assertEqual('lambda: (1,)', self.parse_to_str(lambda: (1,)))
        self.assertEqual('lambda: ()', self.parse_to_str(lambda: ()))
        self.assertEqual('lambda: {1, 2, 3}', self.parse_to_str(lambda: {1, 2, 3}))
        self.assertEqual('lambda: {}', self.parse_to_str(lambda: {}))
        self.assertEqual('lambda: {a: 1, b: 2}', self.parse_to_str(lambda: {a: 1, b: 2}))
        self.assertEqual('lambda: {a: 1, b: 2, c: 3}', self.parse_to_str(lambda: {a: 1, b: 2, c: 3}))

    def test_attr_subscr(self):
        self.assertEqual('lambda: a.b', self.parse_to_str(lambda: a.b))
        self.assertEqual('lambda: a.b.c', self.parse_to_str(lambda: a.b.c))
        self.assertEqual('lambda: a.b.c', self.parse_to_str(lambda: (a.b).c))
        self.assertEqual('lambda: a[b]', self.parse_to_str(lambda: a[b]))
        self.assertEqual('lambda: a[b].c', self.parse_to_str(lambda: a[b].c))
        self.assertEqual('lambda: a.b[c]', self.parse_to_str(lambda: a.b[c]))

    def test_simple_call(self):
        self.assertEqual('lambda x: f(x)', self.parse_to_str(lambda x: f(x)))
        self.assertEqual('lambda x: f(x + 1) * 2', self.parse_to_str(lambda x: f(x + 1) * 2))
        self.assertEqual('lambda x: f(x).g(x)', self.parse_to_str(lambda x: f(x).g(x)))

    def test_comparison(self):
        self.assertEqual('lambda: a < b', self.parse_to_str(lambda: a < b))
        self.assertEqual('lambda: a < b and b < c', self.parse_to_str(lambda: a < b and b < c))
        self.assertEqual('lambda: a < b and b < c', self.parse_to_str(lambda: a < b < c))
        self.assertEqual('lambda: (a < b and b < c) and d < e', self.parse_to_str(lambda: a < b < c and d < e))
        self.assertEqual('lambda: a < b and b < c and d < e', self.parse_to_str(lambda: a < b and b < c and d < e))
        self.assertEqual('lambda: a < b and b < c and d < e', self.parse_to_str(lambda: (a < b and b < c) and d < e))
