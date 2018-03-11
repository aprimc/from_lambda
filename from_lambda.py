import dis
import inspect
from collections import namedtuple

Lambda = namedtuple('Lambda', ['args', 'expr'])
Val = namedtuple('Val', ['v'])
Arg = namedtuple('Arg', ['n'])
Global = namedtuple('Global', ['n'])
BinOp = namedtuple('BinOp', ['op', 'x', 'y'])
UnOp = namedtuple('UnOp', ['op', 'x'])
IfElse = namedtuple('IfElse', ['c', 't', 'f'])
# TODO maybe Subscr
Attr = namedtuple('Attr', ['n', 'x'])
List = namedtuple('List', ['vs'])
Tuple = namedtuple('Tuple', ['vs'])
Map = namedtuple('Map', ['vs'])
Set = namedtuple('Set', ['vs'])
Call = namedtuple('Call', ['f', 'args'])
#CallKw = namedtuple('Call', ['f', 'args', 'kw'])

def to_str(ex):
    if type(ex) is Lambda:
        if ex.args:
            return 'lambda {}: {}'.format(', '.join(ex.args), to_str(ex.expr))
        return 'lambda: {}'.format(to_str(ex.expr))
    if type(ex) is Val:
        return str(ex.v)
    if type(ex) in (Arg, Global):
        return str(ex.n)
    if type(ex) is Attr:
        p = _get_prec(ex)
        if p > _get_prec(ex.x):
            return '({}).{}'.format(to_str(ex.x), ex.n)
        return '{}.{}'.format(to_str(ex.x), ex.n)
    if type(ex) is BinOp:
        p = _get_prec(ex)
        if ex.op == '[]':
            if p > _get_prec(ex.x):
                return '({})[{}]'.format(to_str(ex.x), to_str(ex.y))
            return '{}[{}]'.format(to_str(ex.x), to_str(ex.y))
        fx = '{}' if p <= _get_prec(ex.x)&62 else '({})'
        fy = '{}' if p|1 <= _get_prec(ex.y) else '({})'
        f = fx + ' {} ' + fy
        return f.format(to_str(ex.x), ex.op, to_str(ex.y))
    if type(ex) is UnOp:
        t = ex.op
        if t[-1].isalpha():
            t = t + ' '
        if _get_prec(ex) > _get_prec(ex.x):
            return '{}({})'.format(t, to_str(ex.x))
        return '{}{}'.format(t, to_str(ex.x))
    if type(ex) is Call:
        if _get_prec(ex) > _get_prec(ex.f):
            return '({})({})'.format(to_str(ex.f), ', '.join(map(to_str, ex.args)))
        return '{}({})'.format(to_str(ex.f), ', '.join(map(to_str, ex.args)))
    if type(ex) is IfElse:
        p = _get_prec(ex)
        fc = '{}' if p < _get_prec(ex.c) else '({})'
        ft = '{}' if p < _get_prec(ex.t) else '({})'
        ff = '{}' if p <= _get_prec(ex.f) else '({})'
        f = '{} if {} else {}'.format(ft, fc, ff)
        return f.format(to_str(ex.t), to_str(ex.c), to_str(ex.f))
    if type(ex) is List:
        return '[{}]'.format(', '.join(map(to_str, ex.vs)))
    if type(ex) is Tuple:
        if len(ex.vs) == 1:
            return '({},)'.format(to_str(ex.vs[0]))
        return '({})'.format(', '.join(map(to_str, ex.vs)))
    if type(ex) is Set:
        if len(ex.vs) == 0:
            return 'set()'
        return '{{{}}}'.format(', '.join(map(to_str, ex.vs)))
    if type(ex) is Map:
        return '{{{}}}'.format(', '.join(map(lambda p: '{}: {}'.format(to_str(p[0]), to_str(p[1])), ex.vs)))
    raise TypeError(type(ex))

_bin_prec = {
    'or': 5,
    'and': 7,
    'in': 10, 'is': 10, 'not in': 10, 'is not': 10,
    '<': 10, '<=': 10, '>': 10, '>=': 10, '==': 10, '!=': 10,
    '|': 12,
    '^': 14,
    '&': 16,
    '<<': 18, '>>': 18,
    '+': 20, '-': 20,
    '*': 22, '@': 22, '/': 22, '//': 22, '%': 22,
    '**': 27,
    '[]': 30,
}

_un_prec = {
    'not': 11,
    '+': 25, '-': 25, '~': 25,
}

def _get_prec(ex):
    if type(ex) is BinOp:
        return _bin_prec[ex.op]
    if type(ex) is UnOp:
        return _un_prec[ex.op]
    if type(ex) is Lambda:
        return 0
    if type(ex) is IfElse:
        return 2
    if type(ex) in (Attr, Call):
        return 30
    if type(ex) in (List, Tuple, Map, Set):
        return 32
    return 63

_unary_lookup = {
    'UNARY_POSITIVE': '+',
    'UNARY_NEGATIVE': '-',
    'UNARY_NOT': 'not',
    'UNARY_INVERT': '~',
    #'GET_ITER': 'GET_ITER',
    #'GET_YIELD_FROM_ITER': 'GET_YIELD_FROM_ITER',
}

_binary_lookup = {
    'BINARY_POWER': '**',
    'BINARY_MULTIPLY': '*',
    'BINARY_MATRIX_MULTIPLY': '@',
    'BINARY_FLOOR_DIVIDE': '//',
    'BINARY_TRUE_DIVIDE': '/',
    'BINARY_MODULO': '%',
    'BINARY_ADD': '+',
    'BINARY_SUBTRACT': '-',
    'BINARY_SUBSCR': '[]',
    'BINARY_LSHIFT': '<<',
    'BINARY_RSHIFT': '>>',
    'BINARY_AND': '&',
    'BINARY_XOR': '^',
    'BINARY_OR': '|',
}

def _find_offset(ops, offset):
    i, k = 0, len(ops)
    while i < k:
        j = (i + k) // 2
        o = ops[j].offset
        if o == offset:
            return j
        if o > offset:
            k = j
        else:
            i = j + 1
    if k == len(ops):
        return k
    raise KeyError

def _normalize(x):
    if type(x) is IfElse:
        if type(x.t) is BinOp and x.t.op == 'or' and x.t.y == x.f:
            # c or d if b else d --> c and b or d
            return BinOp('or', BinOp('and', x.c, x.t.x), x.f)
        if type(x.t) is BinOp and x.t.op == 'and' and x.t.y == x.f and type(x.c) is UnOp and x.c.op == 'not':
            # b and c if not a else c --> (a or b) and c
            return BinOp('and', BinOp('or', x.c.x, x.t.x), x.f)
    return x

def parse_lambda(f):
    assert inspect.isfunction(f)
    args = list(inspect.signature(f).parameters.keys())
    # TODO assert no *args, **kwargs
    expr = _parse_expr(list(dis.get_instructions(f)), 0, [])
    return Lambda(args, expr)

def _parse_expr(ops, i, stack):
    for j in range(i, len(ops)):
        op = ops[j]
        opname = op.opname
        if opname == 'RETURN_VALUE':
            return stack[-1]
        if opname == 'LOAD_CONST':
            stack.append(Val(op.argval))
            continue
        if opname == 'LOAD_FAST':
            stack.append(Arg(op.argval))
            continue
        if opname == 'LOAD_GLOBAL':
            stack.append(Global(op.argval))
            continue
        if opname == 'LOAD_ATTR':
            x = stack.pop()
            stack.append(Attr(op.argval, x))
            continue
        tag = _unary_lookup.get(opname, None)
        if tag:
            x = stack.pop()
            stack.append(UnOp(tag, x))
            continue
        tag = _binary_lookup.get(opname, None)
        if tag:
            y = stack.pop()
            x = stack.pop()
            stack.append(BinOp(tag, x, y))
            continue
        if opname == 'COMPARE_OP':
            y = stack.pop()
            x = stack.pop()
            stack.append(BinOp(op.argval, x, y))
            continue
        if opname == 'JUMP_IF_FALSE_OR_POP':
            jj = _find_offset(ops, op.argval)
            a = stack.pop()
            b = _parse_expr(ops[:jj], j + 1, stack[:])
            stack.append(BinOp('and', a, b))
            return _parse_expr(ops, jj, stack)
        if opname == 'JUMP_IF_TRUE_OR_POP':
            jj = _find_offset(ops, op.argval)
            a = stack.pop()
            b = _parse_expr(ops[:jj], j + 1, stack[:])
            stack.append(BinOp('or', a, b))
            return _parse_expr(ops, jj, stack)
        if opname == 'POP_JUMP_IF_FALSE':
            jj = _find_offset(ops, op.argval)
            k = None
            if ops[jj - 1].opname == 'JUMP_FORWARD':
                k = _find_offset(ops, ops[jj - 1].argval)
            c = stack.pop()
            if k is None:
                ##t = _parse_expr(ops[:jj], j + 1, stack[:])
                t = _parse_expr(ops, j + 1, stack[:])
                f = _parse_expr(ops, jj, stack)
                return _normalize(IfElse(c, t, f))
            else:
                t = _parse_expr(ops[:jj - 1], j + 1, stack[:])
                f = _parse_expr(ops[:k], jj, stack[:])
                stack.append(_normalize(IfElse(c, t, f)))
                return _parse_expr(ops[k:], 0, stack)
        if opname == 'POP_JUMP_IF_TRUE':
            jj = _find_offset(ops, op.argval)
            k = None
            if ops[jj - 1].opname == 'JUMP_FORWARD':
                k = _find_offset(ops, ops[jj - 1].argval)
            c = stack.pop()
            if k is None:
                ##t = _parse_expr(ops[:jj], j + 1, stack[:])
                t = _parse_expr(ops, j + 1, stack[:])
                f = _parse_expr(ops, jj, stack)
                return _normalize(IfElse(UnOp('not', c), t, f))
            else:
                t = _parse_expr(ops[:jj - 1], j + 1, stack[:])
                f = _parse_expr(ops[:k], jj, stack[:])
                stack.append(_normalize(IfElse(UnOp('not', c), t, f)))
                return _parse_expr(ops[k:], 0, stack)
        if opname == 'JUMP_FORWARD':
            jj = _find_offset(ops, op.argval)
            return _parse_expr(ops, jj, stack)
        if opname == 'BUILD_LIST':
            vs = tuple(_popn(stack, op.argval))
            stack.append(List(vs))
            continue
        if opname == 'BUILD_TUPLE':
            vs = tuple(_popn(stack, op.argval))
            stack.append(Tuple(vs))
            continue
        if opname == 'BUILD_SET':
            vs = tuple(_popn(stack, op.argval))
            stack.append(Set(vs))
            continue
        if opname == 'BUILD_MAP':
            vs = _popn(stack, 2*op.argval)
            vs = tuple(zip(vs[0::2], vs[1::2]))
            stack.append(Map(vs))
            continue
        if opname == 'CALL_FUNCTION':
            args = tuple(_popn(stack, op.argval))
            f = stack.pop()
            stack.append(Call(f, args))
            continue
        #if opname == 'CALL_FUNCTION_KW':
        #    kw = stack.pop()
        #    args = tuple(_popn(stack, op.argval))
        #    f = stack.pop()
        #    assert type(kw) is Val
        #    stack.append(CallKw(f, args, kw.v))
        #    continue
        # TODO CALL_FUNCTION_EX, BUILD_TUPLE_UNPACK_WITH_CALL
        # TODO MAKE_FUNCTION
        if opname == 'NOP':
            continue
        if opname == 'POP_TOP':
            stack.pop()
            continue
        if opname == 'ROT_TWO':
            t = stack[-2]
            stack[-2] = stack[-1]
            stack[-1] = t
            continue
        if opname == 'ROT_THREE':
            t = stack[-1]
            stack[-1] = stack[-2]
            stack[-2] = stack[-3]
            stack[-3] = t
            continue
        if opname == 'DUP_TOP':
            stack.append(stack[-1])
            continue
        if opname == 'DUP_TOP_TWO':
            stack.append(stack[-2])
            stack.append(stack[-2])
            continue
        raise ValueError(op.opname)
    return stack[-1]

def _popn(l, n):
    if not n:
        return []
    r = l[-n:]
    del l[-n:]
    return r

