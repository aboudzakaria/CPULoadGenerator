#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

import scipy.stats as sp
import json
import matplotlib.pyplot as plt


#TIMESTEP_DISTR = sp.geom
TIMESTEP_DISTR = 20
TIMESTEP_DISTR_ARGS = {'p': 0.2}

WALK_DISTR = sp.beta
WALK_ARGS = {'a': 0.8, 'b': 0.8}


class Variable:
    def __init__(self, distr, **distr_args):
        if not isinstance(distr, (int, float, sp._discrete_distns.rv_discrete,
                                  sp._continuous_distns.rv_continuous)):
            raise TypeError('Invalid type for argument distr.')
        self.distr = distr
        self.distr_args = distr_args

    def get(self):
        if isinstance(self.distr, (int, float)):
            step = self.distr
        else:
            step = self.distr.rvs(**self.distr_args)
        return step


class TimeSerie:
    """
    """
    def __init__(self, start_time, duration, start_value, timestep_variable,
                 value_variable):
        self.current_time = start_time
        self.current_value = start_value
        self.start_value = start_value
        self.start_time = start_time
        self.end_time = start_time + duration
        self.durations = list()
        self.values = list()
        self.timestep_variable = timestep_variable
        self.value_variable = value_variable

    def __repr__(self):
        res = list()
        for duration, value in self:
            res.append('{} {}'.format(duration, value))
        return '\n'.join(res)

    def __iter__(self):
        for duration, value in zip(self.durations, self.values):
            yield duration, value

    def append(self, time, value):
        done = False
        if time > self.current_time:
            duration = time - self.current_time
            self.durations.append(duration)
            self.values.append(self.current_value)
            self.current_time = time
            self.current_value = value
            done = True
        return done

    def set_next(self):
        timestep = self.timestep_variable.get()
        value = self.value_variable.get()
        done = False
        time = self.current_time + timestep
        if self.current_time < self.end_time:
            if time < self.end_time:
                done = self.append(time, value)
            else:
                done = self.append(self.end_time, self.current_value)
        return done

    def fill(self):
        done = True
        while done:
            done = self.set_next()

    def export_json(self, out_file, repeat=1, indent=None):
        dic = dict()
        dic['repeat'] = repeat
        dic['scenario'] = list()
        for duration, value in self:
            dic_slot = {'cpu_load': [value],
                        'duration': duration}
            dic['scenario'].append(dic_slot)
        with open(out_file, 'w') as of:
            json.dump(dic, of, indent=indent)

    def plot(self, *args, **kwargs):
        x = [self.start_time]
        y = [self.start_value]
        for duration, value in self:
            x.append(x[-1] + duration)
            y.append(value)
        plt.plot(x, y, *args, **kwargs)
        plt.show()


class CPULoad(TimeSerie):
    def plot(self, *args, **kwargs):
        plt.ylim((0, 1))
        return TimeSerie.plot(self, *args, **kwargs)


class CPULoadCst(CPULoad):
    def __init__(self, start_value, start_time=0, duration=1000,
                 timestep_variable=Variable(TIMESTEP_DISTR,
                                            **TIMESTEP_DISTR_ARGS)):
        value_variable = Variable(start_value)
        TimeSerie.__init__(self, start_time, duration, start_value,
                           timestep_variable, value_variable)


class CPULoadRandomWalk(CPULoad):
    def __init__(self, start_value, step_scale=.1, start_time=0, duration=1000,
                 timestep_variable=Variable(TIMESTEP_DISTR,
                                            **TIMESTEP_DISTR_ARGS)):
        value_variable = Variable(WALK_DISTR, scale=step_scale,
                                  loc=-step_scale / 2, **WALK_ARGS)
        TimeSerie.__init__(self, start_time, duration, start_value,
                           timestep_variable, value_variable)

    def set_next(self):
        timestep = self.timestep_variable.get()
        walk = self.value_variable.get()
        value = max(0., min(1., self.current_value + walk))
        done = False
        time = self.current_time + timestep
        if self.current_time < self.end_time:
            if time < self.end_time:
                done = self.append(time, value)
            else:
                done = self.append(self.end_time, self.current_value)
        return done
