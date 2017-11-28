# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# $File: game.py
# $Date: Tue Nov 28 14:4726 2017 +0800
# $Author: renyong15 © <mails.tsinghua.edu.cn>
#
from __future__ import print_function
import utils
import copy
import tensorflow as tf
from collections import deque

import Network
from strategy import strategy

'''
(1, 1) is considered as the upper left corner of the board,
(size, 1) is the lower left
'''

DELTA = [[1, 0], [-1, 0], [0, -1], [0, 1]]


class Executor:
    def __init__(self, **kwargs):
        self.game = kwargs['game']

    def _bfs(self, vertex, color, block, status, alive_break):
        block.append(vertex)
        status[self.game._flatten(vertex)] = True
        nei = self._neighbor(vertex)
        for n in nei:
            if not status[self.game._flatten(n)]:
                if self.game.board[self.game._flatten(n)] == color:
                    self._bfs(n, color, block, status, alive_break)

    def _find_block(self, vertex, alive_break=False):
        block = []
        status = [False] * (self.game.size * self.game.size)
        color = self.game.board[self.game._flatten(vertex)]
        self._bfs(vertex, color, block, status, alive_break)

        for b in block:
            for n in self._neighbor(b):
                if self.game.board[self.game._flatten(n)] == utils.EMPTY:
                    return False, block
        return True, block

    def _is_qi(self, color, vertex):
        nei = self._neighbor(vertex)
        for n in nei:
            if self.game.board[self.game._flatten(n)] == utils.EMPTY:
                return True

        self.game.board[self.game._flatten(vertex)] = color
        for n in nei:
            if self.game.board[self.game._flatten(n)] == utils.another_color(color):
                can_kill, block = self._find_block(n)
                if can_kill:
                    self.game.board[self.game._flatten(vertex)] = utils.EMPTY
                    return True

        ### can not suicide
        can_kill, block = self._find_block(vertex)
        if can_kill:
            self.game.board[self.game._flatten(vertex)] = utils.EMPTY
            return False

        self.game.board[self.game._flatten(vertex)] = utils.EMPTY
        return True

    def _check_global_isomorphous(self, color, vertex):
        ##backup
        _board = copy.copy(self.game.board)
        self.game.board[self.game._flatten(vertex)] = color
        self._process_board(color, vertex)
        if self.game.board in self.game.history:
            res = True
        else:
            res = False

        self.game.board = _board
        return res

    def _in_board(self, vertex):
        x, y = vertex
        if x < 1 or x > self.game.size: return False
        if y < 1 or y > self.game.size: return False
        return True

    def _neighbor(self, vertex):
        x, y = vertex
        nei = []
        for d in DELTA:
            _x = x + d[0]
            _y = y + d[1]
            if self._in_board((_x, _y)):
                nei.append((_x, _y))
        return nei

    def _process_board(self, color, vertex):
        nei = self._neighbor(vertex)
        for n in nei:
            if self.game.board[self.game._flatten(n)] == utils.another_color(color):
                can_kill, block = self._find_block(n, alive_break=True)
                if can_kill:
                    for b in block:
                        self.game.board[self.game._flatten(b)] = utils.EMPTY

    def is_valid(self, color, vertex):
        ### in board
        if not self._in_board(vertex):
            return False

        ### already have stone
        if not self.game.board[self.game._flatten(vertex)] == utils.EMPTY:
            return False

        ### check if it is qi
        if not self._is_qi(color, vertex):
            return False

        if self._check_global_isomorphous(color, vertex):
            return False

        return True

    def do_move(self, color, vertex):
        if not self.is_valid(color, vertex):
            return False
        self.game.board[self.game._flatten(vertex)] = color
        self._process_board(color, vertex)
        self.game.history.append(copy.copy(self.game.board))
        self.game.past.append(copy.copy(self.game.board))
        return True


class Game:
    def __init__(self, size=19, komi=6.5):
        self.size = size
        self.komi = 6.5
        self.board = [utils.EMPTY] * (self.size * self.size)
        self.strategy = strategy()
        self.executor = Executor(game=self)
        self.history = []
        self.past = deque(maxlen=8)
        for i in range(8):
            self.past.append(self.board)

    def _flatten(self, vertex):
        x, y = vertex
        return (y - 1) * self.size + (x - 1)

    def clear(self):
        self.board = [utils.EMPTY] * (self.size * self.size)

    def set_size(self, n):
        self.size = n
        self.clear()

    def set_komi(self, k):
        self.komi = k

    def check_valid(self, vertex):
        return True

    def do_move(self, color, vertex):
        if vertex == utils.PASS:
            return True
        res = self.executor.do_move(color, vertex)
        return res

    def gen_move(self, color):
        # move = self.strategy.gen_move(color)
        # return move
        move = self.strategy.gen_move(self.past, color)
        self.do_move(color, move)
        return move

    def status2symbol(self, s):
        pool = {utils.WHITE: '#', utils.EMPTY: '.', utils.BLACK: '*', utils.FILL: 'F', utils.UNKNOWN: '?'}
        return pool[s]

    def show_board(self):
        row = [i for i in range(1, 20)]
        col = ' abcdefghijklmnopqrstuvwxyz'
        print(' ', end='')
        for j in range(self.size + 1):
            print(col[j], end='  ')
        print('')
        for i in range(self.size):
            print(row[i], end='  ')
            if row[i] < 10:
                print(' ', end='')
            for j in range(self.size):
                print(self.status2symbol(self.board[self._flatten((j + 1, i + 1))]), end='  ')
            print('')


if __name__ == "__main__":
    g = Game()
    g.show_board()
