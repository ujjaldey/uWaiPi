# -*- coding: utf-8 -*-

###################################################################################################
#      __        __    _ ____  _
#  _   \ \      / /_ _(_)  _ \(_)
# | | | \ \ /\ / / _` | | |_) | |
# | |_| |\ V  V / (_| | |  __/| |
#  \__,_| \_/\_/ \__,_|_|_|   |_|
#
# Copyright (c) 2016 Ujjal Dey
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or 
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###################################################################################################

from multiprocessing import Process
from functools import wraps

def async(func):
	@wraps(func)
	def async_func(*args, **kwargs):
		try:
			func_hl = Process(target = func, args = args, kwargs = kwargs)
			func_hl.start()
			return func_hl
		except KeyboardInterrupt:
			return
	return async_func
