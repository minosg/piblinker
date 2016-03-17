#!/usr/bin/env python

"""colorlogger.py: New python logger with color output support."""

__author__ = "Minoas Galanakis"
__version__ = "0.0.1"
__email__ = "minos197@gmail.com"
__date__ = "04-03-2016"

import re
from datetime import datetime
from inspect import getframeinfo, stack


def colorlogger(logtype):
    """Decorator that allows custom methods for clogger."""

    def clog_decorator(func):
        def clog_wrapper(self, *args):
            return CLogger._color_stdout(func(self, *args), logtype)
        return clog_wrapper
    return clog_decorator


class ANSIColors(object):

    @classmethod
    def setup(self):
        """ Create class attributes for common ANSI colors"""

        colors = ["BLACK", "RED", "GREEN", "YELLOW",
                  "BLUE", "MAGENDA", "CYAN", "WHITE"]
        normal = range(30, 38)
        bright = range(90, 98)

        a = [["%s" % c, "\033[%sm" % v] for c, v in zip(colors, normal)] +\
            [["H%s" % c, "\033[%sm" % v] for c, v
                in zip(colors, bright)] +\
            [["U%s" % c, "\033[%s;4m" % v] for c, v
                in zip(colors, normal)] +\
            [["UH%s" % c, "\033[%s;4m" % v] for c, v
                in zip(colors, bright)] +\
            [["END", "\033[0m"]] +\
            [["UEND", "\033[;21m"]]

        self.color_list = ["%s%s" % (p, c) for c in colors
                           for p in["", "H", "U", "UH"]]
        for attrib in a:
            setattr(self, *attrib)
        return ANSIColors.cprint

    @classmethod
    def cprint(self, lne, sep=" "):
        """Color print to terminal using ANSI colors.

        Expects a list of inputs of color followed by text. Enables
        users customization on value separations using optional sep
        parameter. Can be used in both cprint["RED",
        "Error","GREEN","Some Text"] or cprint([ANSIColors.RED,
        "Error",ANSIColors.GREEN,"Some Text"]) Raises Arrgument Error
        when color not found

        """

        colors = lne[::2]
        # Do a sanity check on input and allow dual mode input
        test_input = re.compile(r'^\033\[[3/9]{1}[0-9]{1}(?:;4)?m{1}$')
        test_underline = re.compile(r'^\033\[[3/9]{1}[0-9]{1}(?:;4){1}m{1}.+$')
        if not filter(test_input.findall, colors):
            for i in range(len(colors)):
                exec("colors[%d] = ANSIColors.%s" % (i, colors[i]))
        cline = ["%s%s" % (x) for x in zip(colors, lne[1:][::2])]

        # Compose the string
        pline = ""
        for c in cline:
            pline += c
            # If the line contains a underline it needs to be terminated
            if test_underline.findall(c):
                pline += ANSIColors.UEND
            pline += sep
        print pline + ANSIColors.END


class CLogger(object):

    def __init__(self):
        raise ValueError('Clogger is not meant to be instantiated.\n'
                         'Use as class with CLogger.setup(cmd, debug_level,'
                         'file_path, colorPattern).\n'
                         'Only cmd is required\n'
                         'For example:\n'
                         'logger = CLogger.setup("main_program","Debug",'
                         '"/var/log/main.log",["WHITE","UWHITE"])')

    @classmethod
    def setup(self,
              label="",
              level="error",
              path="",
              alt_levels=None,
              pattern=None):

        self.LOG_PATH = path
        self.LOG_LABEL = label
        self.cprint = ANSIColors.setup()
        self.set_def_colors(alt_levels)
        self.set_level(level)
        return self

    @classmethod
    def set_def_colors(self, color_dict=None):
        """ Set the default colors for different levels of debuggin """

        # Create the default dictionary
        self.DLEVELS = {"info": [0, "BLUE"],
                        "warning": [1, "YELLOW"],
                        "error": [2, "HRED"],
                        "debug": [3, "WHITE"],
                        "ver_debug": [4, "WHITE"]}
        # Extract the log base collor if it exists
        try:
            c = color_dict.pop("base_color")
        except (KeyError, AttributeError):
            c = "CYAN"
        self.BASE_COLOR = ["%s%s" % (pre, c) for pre in ["", "U"]]

        if isinstance(color_dict, dict):
            # Update only the valid entries
            self.DLEVELS.update({k: [v[0], color_dict[k]] for k, v
                                in self.DLEVELS.iteritems()
                                if k in color_dict and color_dict[k]
                                in ANSIColors.color_list})

    @classmethod
    def set_level(self, lv="info"):
        """ Set Logging level """

        if not isinstance(lv, int):
            try:
                lv = self.DLEVELS[lv.lower()][0]
            except KeyError:
                raise ValueError("Error, supported debug levels"
                                 "are: %s" % ", ".join(self.DLEVELS.keys()))
        self.LEVEL = lv

    @classmethod
    def _log(self, msg, *args):

        msg = [datetime.now().strftime('%F %T'),
               "%s" % self.LOG_LABEL, (msg % args)]
        # To file
        if self.LOG_PATH:
            try:
                fp = open(self.LOG_PATH, 'a')
                fp.write(" ".join(msg) + '\n')
            except:
                pass
        return msg

    @classmethod
    def _color_stdout(self, dataset, ltype):
        """ Print text with preformated color for debug level """

        lv_no, lv_clr = self.DLEVELS[ltype]
        if (self.LEVEL < lv_no):
            return

        pattern = self.BASE_COLOR + [lv_clr]
        # Compose the line
        colored_line = [
            item for pair in zip(
                pattern,
                dataset) for item in pair]
        # Add log type information and padding
        padding = " " * (7 - len(ltype))

        colored_line[-1] = "[%s]:%s %s" % (ltype, padding, colored_line[-1])

        if self.LEVEL == self.DLEVELS["ver_debug"][0]:

            #print "\n".join(stack())
            mod, line, fn, _, _ = getframeinfo(stack()[-3][0])
            details = " >> Called by %s() at %d in %s" % (fn, line, mod)
            colored_line[-1] = colored_line[-1] + details

        self.cprint(colored_line)

    @classmethod
    @colorlogger("error")
    def error(self, msg, *args):
        return self._log(msg, *args)

    @classmethod
    @colorlogger("info")
    def info(self, msg, *args):
        return self._log(msg, *args)

    @classmethod
    @colorlogger("warning")
    def warning(self, msg, *args):
        return self._log(msg, *args)

    @classmethod
    @colorlogger("debug")
    def debug(self, msg, *args):
        return self._log(msg, *args)


if __name__ == '__main__':
    log = CLogger.setup("colortest", "ver_debug")

    log.info("This is an info")
    log.warning("This is a warning")
    log.error("This is an error")
    log.debug("This is debug")
