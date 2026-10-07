#!/usr/bin/env python3
"""Absorbance spectrum from two PySpectrometer2 CSV files (System B).

Usage:
    python3 absorbance.py REFERENCE.csv SAMPLE.csv [-o OUTPUT.csv]

REFERENCE.csv is the spectrum saved (key 's') with the blank cuvette, SAMPLE.csv the
spectrum saved with the sample, both in the 'Wavelength,Intensity' format written by
PySpectrometer2. The sample is interpolated onto the reference wavelengths and

    A = -log10(I / I0)

Points where I <= 0 or I0 <= 0 (or outside the common range) are written as NaN.

This file is an addition of this fork; it is not part of the original PySpectrometer2.
"""
import argparse
import csv
import numpy as np


def read_spectrum(path):
    """Return (wavelength, intensity) arrays from a PySpectrometer2 CSV."""
    with open(path, newline='') as f:
        rows = [r for r in csv.reader(f) if r]
    data = np.array([[float(r[0]), float(r[1])] for r in rows[1:]])
    order = np.argsort(data[:, 0])
    return data[order, 0], data[order, 1]


def absorbance(wl_ref, i0, wl_s, i):
    """Interpolate the sample onto the reference grid and return (I, A)."""
    i_on_ref = np.interp(wl_ref, wl_s, i, left=np.nan, right=np.nan)
    with np.errstate(divide='ignore', invalid='ignore'):
        a = -np.log10(i_on_ref / i0)
    a[~((i_on_ref > 0) & (i0 > 0))] = np.nan
    return i_on_ref, a


def _selftest():
    wl = np.array([400.0, 500.0, 600.0])
    i_s, a = absorbance(wl, np.array([100.0, 100.0, 0.0]), wl, np.array([10.0, 100.0, 5.0]))
    assert np.allclose(a[:2], [1.0, 0.0]) and np.isnan(a[2])
    print("self-test OK")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('reference', nargs='?')
    p.add_argument('sample', nargs='?')
    p.add_argument('-o', '--output', default='absorbance.csv')
    p.add_argument('--selftest', action='store_true', help='run a quick check and exit')
    args = p.parse_args()
    if args.selftest:
        return _selftest()
    if not (args.reference and args.sample):
        p.error('REFERENCE and SAMPLE are required')
    wl, i0 = read_spectrum(args.reference)
    i, a = absorbance(wl, i0, *read_spectrum(args.sample))
    with open(args.output, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Wavelength_nm', 'I0_Reference', 'I_Sample', 'Absorbance'])
        for row in zip(wl, i0, i, a):
            w.writerow([f'{row[0]:.3f}', f'{row[1]:g}', f'{row[2]:g}', f'{row[3]:.4f}'])
    print(f'Saved {args.output} ({len(wl)} points)')


if __name__ == '__main__':
    main()
