#!/usr/bin/env python

###############################################################################
"""
The Spectrum class enables operations on image data.
Light is produced, absorbed, reflected, refracted, and diffracted.
This class encapsulates data and performs operations necessary to generate
image data suitable for analysis of full-spectrum vision.

A spectrum is a continuous curve predicting intensity as a function of wavelength.
A discrete spectrum associates discrete intensities with discrete values for wavelength.
One can view discrete wavelengths and intensities as integrals within windows.
The discrete intensity is the integral of all intensities for
all wavelengths within a small range.
http://en.wikipedia.org/wiki/Discrete_spectrum_(physics)

The Spectrum class is initialized with a vector (sequence) of discrete wavelengths.
Once initialized the wavelength vector is a class static and is held fixed.
A second vector of the same length, holding intensities, is generated.
Instances of a Spectrum class have separate intensity vectors.
Operations on instances include photon production functions,
normalization, summing, absorption and reflection.

Two functions are of special interest: the Hadamard product and the dot product.
The Hadamard product is the simple product of two vectors.
The Hadamard product enables production of a combined spectrum from
emission spectra, reflection spectra, and absorption spectra;
spanning from light being produced to light being sensed in an eye.

Photons are emitted in proportions by a source.
For each wavelength extent there is a corresponding photon rate.
Let 'E' be the vector of photon emission rates.

Photons are absorbed in proportion from objects.
The remainder are reflected.
Reflected photons are in proportion to the Hadamard product of
the source photon rate and the reflection rate.
Let 'R' be the vector of photons reflection rates.

The Hadamard product is the point-by-point product of rates.
Let 'I' be the vector of photons arriving at the cornea of an eye
and the letter 'o' be the product symbol.
http://en.wikipedia.org/wiki/Hadamard_product_(matrices)
http://en.wikipedia.org/wiki/Matrix_multiplication
    I = E o R
    or
    [i0 i1 i2] = [e0 e1 e2] o [r1 r2 r3] = [e1*r1 e2*r2 e3*r3]
    which operation is commutative.

Once photons reach the optics of an image sensor they are subjected to
refraction diffraction and absorption.

Excluding optics, the entire lifetime of a photon between emission and sensing
can be simplified into the equation:
    S = E o R o A
    where
    E = Emission spectrum
    R = Reflection spectrum
    A = Absorption spectrum
    S = Sensory spectrum

In image sensing, photons are refracted and diffracted by the optics.
In animal optics, the lens has no wavelength correction.

Consider a point source of monochromatic photons on the optical axis.
Refraction through convex lenses brings these photons to a second point.
Diffraction causes the point to be spread into an Airy pattern.
An Airy pattern has narrow rings of zeros separating wide annuli of light.
If the point source is polychromatic, longer wavelength photons exhibit
a first zeros at a greater radius than photons of a shorter wavelength.

Consider a point source off the optical axis.
For both refraction and diffraction, the focal points and Airy patterns
are eccentric (displaced from center).
The displacement of the photon pattern from center is
greater for longer wavelengths than for shorter wavelengths.
For purposes of evaluating the character of patterns in an image,
Since refractive displacement enhances diffractive displacement,
it is sufficient to consider only diffraction since
refractions effect increases the effective diffractive displacement and size.

So, for this same off-axis polychromatic point source,
a sensor in the image place receives photons from
non-concentric Airy patterns for each wavelength of incident light.

To calculate the incident spectrum of such a source on an individual sensor
the Airy pattern for every wavelength contributes a point intensity
for a different radius from the center of its pattern.
The contributions are assembled into a spectrum.

Finally, the sensor itself has an absorption spectrum.  The dot product of
the assembled spectrum from diffraction with the sensor spectrum
is the sensor absorption which is transduced.
If this transduction has remained unchanged, the sensor reaches equilibrium.
If the transduced absorption is different, the sensor changes state
as it approaches equilibrium.

When a sensor changes state, it generates a difference signal.

"""
###############################################################################

import os, inspect, scipy, random

from optparse import OptionParser

from scipy import arange, exp, random, zeros, ones, array
from scipy.constants import *

###############################################################################

scipy.set_printoptions(precision=2, linewidth=1000)

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Spectrum(object):

    # First instance forces initialization, wait for OptionParser to parse argv.
    initialized   = False
    stepsize      = None
    visible       = None
    wavelengths   = None
    energy        = None
    length        = None
    named         = {}
    rand          = 0

    def id(this, name=None):
        if name: this.name = name
        if this.name:
            assert not Spectrum.named.has_key(this.name)
            this[this.name] = this
        return this

    def __init__(this, **kwargs):
        if not Spectrum.initialized:
            Spectrum.stepsize    = float(kwargs.get('stepsize'   ,   1))
            Spectrum.infrared    = float(kwargs.get('infrared'   , 740))
            Spectrum.ultraviolet = float(kwargs.get('ultraviolet', 380))
            Spectrum.visible = {
                    'ultraviolet': Spectrum.ultraviolet * nano,
                    'infrared'   : Spectrum.infrared    * nano,
                    'step'       : Spectrum.stepsize    * nano}
            Spectrum.visible['step'] = Spectrum.stepsize * nano
            Spectrum.wavelengths = arange(
                    Spectrum.visible['ultraviolet'],
                    Spectrum.visible['infrared'],
                    Spectrum.visible['step'])
            Spectrum.length = len(Spectrum.wavelengths)
            Spectrum.energy = h * c / Spectrum.wavelengths
            Spectrum.initialized = True
            if kwargs.get('verbose', False):
                print '\t', Spectrum.visible, '\t', Spectrum.length

        temperature = kwargs.get('T', None)
        initial     = kwargs.get('initial', None)
        assert not (temperature and initial)

        if kwargs.get('rand', False):
            this.line = random.random((Spectrum.length,));
        elif kwargs.get('sweep', False):
            this.line = arange(0.0, 1.0, 1.0/Spectrum.length)
        elif temperature:
            this.line = BlackBody.amplitude(this.wavelengths, temperature)
        elif initial: this.line = initial * ones(Spectrum.length, float)
        else: this.line = kwargs.get('line', zeros(Spectrum.length, float))

        if not initial: this.normalize()

    def __call__(this, wavelength):
        index = int(wavelength / nano) - int(this.wavelengths[0]/nano)
        assert 0 <= index < len(this.line)
        return this.line[index]

    def __setitem__(this, name, spectrum):
        Spectrum.named[name] = spectrum
    def __getitem__(this, name):
        return Spectrum.named.get(name, None)
    def __repr__(this):
        return ((this.name + ': ') if this.name else '') + str(this.line)

    def __add__(this, that):
        return Spectrum(line = this.line + that.line)
    def __sub__(this, that):
        return Spectrum(line = this.line - that.line)
    # Hadamard product
    def __mul__(this, that):
        return Spectrum(line = this.line * that.line)
    def __div__(this, that):
        return Spectrum(line = this.line / that.line)

    def __iadd__(this, that):
        this.line = this.line + that.line
        return this.normalize()
    def __isub__(this, that):
        this.line = this.line - that.line
        return this.normalize()
    def __imul__(this, that):
        this.line = this.line * that.line
        return this.normalize()
    def __idiv__(this, that):
        this.line = this.line / that.line
        return this.normalize()

    def normalize(this):
        denominator = this.line.max()
        if denominator != 0.0: this.line /= denominator
        return this

    def inverse(this):
        """Convert reflection spectrum to absorption spectrum
        or the other way around."""
        this.normalize()
        this.line = 1.0 - this.line

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class BlackBody(object):
    """Physical constants"""
    hcok, Volume = h * c / k, centi * femto
    Scale, Numerator = 2e+5, 2.0*h*(c**2)
    Constant = Scale * Volume * Numerator

    @staticmethod
    def amplitude(wavelength, T):
        return BlackBody.Constant/(
                (wavelength**5)*(exp(BlackBody.hcok/(wavelength*T))-1.0))

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Photoreceptor(Spectrum):
    """emulating Bowmaker and Dartnall, 1980"""

    def __init__(this, peaks, name=''):
        """This is pure curve-fitting without theoretical foundation."""
        super(Photoreceptor, this).__init__()
        this.wlo    = this.wavelengths[0]
        this.scale  = nano
        this.center = 0
        this.x      = Photoreceptor.wavelengths / this.scale
        for peak, coeff in peaks.items():
            this.center = this.center if coeff != 1.0 else peak
            this.line += array([
                coeff*exp(-3e-4*(wavelength-peak)**2)
                for wavelength in this.x])
        this.normalize()

    @property
    def peak(this): return this.center

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Photoreceptors(object):
    def __init__(self):
        """Create photoreceptors"""
        Photoreceptor({564:1.0,400:0.25}).id('photoreceptor.L')
        #print spectrum['photoreceptor.L']
        Photoreceptor({534:1.0,400:0.25}).id('photoreceptor.M')
        #print spectrum['photoreceptor.M']
        Photoreceptor({498:1.0,400:0.25}).id('photoreceptor.X')
        #print spectrum['photoreceptor.X']
        Photoreceptor({420:1.0         }).id('photoreceptor.S')
        #print spectrum['photoreceptor.S']

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Blackbodies(object):
    def __init__(self):
        """Create 3 blackbody spectra having different temperatures."""
        B4K   = Spectrum(T = 4 * kilo).id('blackbody.4000K')
        print spectrum['blackbody.4000K']
        B5K   = Spectrum(T = 5 * kilo).id('blackbody.5000K')
        print spectrum['blackbody.5000K']
        B6K   = Spectrum(T = 6 * kilo).id('blackbody.6000K')
        print spectrum['blackbody.6000K']
        B456K = B4K + B5K + B6K
        print B456K.id('B456K')

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Tests(object):
    def __init__(self):
        """Create random&initialized spectra, perform various math with them."""
        Q = [Spectrum(rand=True).id('random.%d' % (i))
                for i in range(5)]
        R = [Spectrum(initial=float(1.0/(i+1))).id('initial.%d' % (i+1))
                for i in range(5)]
        # TODO Q and R are unchecked
        """Create swept spectra and perform various math with them."""
        S = [Spectrum(sweep=True).id('sweep.%d' % (i))
                for i in range(5)]

        print S[0]; print S[1]
        S[2]  = S[0] * S[1]; print S[2].id('Hadamard.1')
        S[3]  = S[0] + S[1]; print S[3].id('spectralsum.1')
        S[4] += S[3]       ; print S[4].id('spectralsum.2')

spectrum = Spectrum()

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":
    parser = OptionParser()
    #parser.add_option("-i", "--infrared"   , dest="infrared"   , default=740,
            #help="longest lambda wavelength in nanometers [default 740]")
    #parser.add_option("-u", "--ultraviolet", dest="ultraviolet", default=380,
            #help="shortest lambda wavelength in nanometers [default 380]")
    #parser.add_option("-s", "--step-size"  , dest="stepsize"   , default= 10,
            #help="width of lambda bucket in nanometers [default 10]")
    #parser.add_option( "-v", "--verbose",
            #action="store_false", dest="verbose", default=True,
            #help="announce actions and sizes")
    """Create base for generic access to spectrum naming dictionary."""
    (options, args) = parser.parse_args()
    #spectrum = Spectrum(**vars(options))

    photoreceptors  = Photoreceptors()
    blackbodies     = Blackbodies()
    tests           = Tests()
###############################################################################
