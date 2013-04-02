#!/usr/bin/python

"""
Eye.py

Implements a filter that reliably emulates human refraction/diffraction.
"""

###############################################################################
__date__       = "20130131"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "Trade Secret"
__status__     = "Production"
__version__    = "0.0.1"

"""
TeX block
; \title{Perception Requires Shapeliness}
; \author{Jonathan D. Lettvin}
; \begin{document}
; \maketitle
; \begin{abstract}
;
; Transforming a visual scene to optic nerve signal is explored.
;
; Photons from RGB monitors are diffracted and refracted over a retina.
; Opposed wavelength variance by diffraction and refraction
; cause Airy disk size to be wavelength-invariant.
; Refraction causes wavelength-variant differential radial displacement.
;
; Photoreceptors decay to equilibrium state with flux.
; Photoreceptors generate signal on flux changes.
; Horizontal cells average Photoreceptor state.
; Horizontal cells generate signal on change of average.
; Difference between Photoreceptor and Horizontal cell signals is
; detected by dendritic spine TGS units (transient gradient samplers).
;
; Dendritic spines are distributed over paraboloid extensions of bipolar cells.
; Coincident detection of transient gradients constitutes a feature detection.
; Centrifugal bipolar cells select section of paraboloid.
; Pupillary reflex couples to section selection.
;
; Character of human optical input is demonstrated.
; After image in photoreceptor response is demonstrated.
; Shapes of bipolar cell have consequence.
; Hyperacuity is demonstrated.
;
; \end{abstract}
;
; \section{Introduction}
; Eye is a model of how a scene projects onto a retina,
; how a retina converts converts projections into coherent signal,
; and how feedback refines the conversion.
;
; \section{Discussion}
 ;\subsection{Parabolic Shell Convolution/Correlation in Vision}
"""

"""
Action block
DONE:
    A VGS (vector gradient sampler) measures a local gradient in a field.
    associate RVGS (rings of vector gradient samplers) with diffraction radii.
    Implemented in Spines.py
TODO:
    Use diffraction radius to select RVGS.
    Use VGS to generate pulses for convolution.
    Use threshold on convolution value to determine informational value.
    Use informational value to generate new image features.
TODO:
    Make movie of layer A, then run again using move layer A to make layer B,
    and on up to the latest layer, to reduce compute burden on single run
    and also to prep for fully parallel or gpgpu implementation.
"""

#IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
# Imports from generic libraries
import          os, sys, json, gc

from time       import clock
from scipy      import zeros, ones, array, asarray, arange, uint8, around
from scipy      import fabs, exp, tanh, sqrt, set_printoptions
from optparse   import OptionParser
from itertools  import product

# Imports from OpenCV
from cv2        import getAffineTransform, warpAffine, filter2D
from cv2.cv     import GetSubRect, NamedWindow, GetCaptureProperty
from cv2.cv     import CaptureFromCAM, CreateMat, GetMat, QueryFrame, ShowImage
from cv2.cv     import WaitKey, DestroyAllWindows, CV_8UC3, CV_32FC1
from cv2.cv     import CV_CAP_PROP_FRAME_WIDTH, CV_CAP_PROP_FRAME_HEIGHT

# Imports from this suite
from Diffract   import Human
from Paraboloid import Paraboloid
from Spectrum   import Spectrum, Photoreceptors
from Spines     import Spines

#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
# Change how scipy displays numbers.
set_printoptions(precision=2)

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Eye(Human):

    #11111111111111111111111111111111111111111111111111111111111111111111111111
    def __init__(self, **kw):
        super(Eye, self).__init__()
        self.kw = kw

        # The order of execution for sub-init functions is important.
        # They are defined in the same order they are to be executed.

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initParaboloid():
            # Initialize human bipolar cell paraboloid kernel.
            # dE =  1.0 with dR = 0.4 makes thick paraboloid shell.
            #                dR = 0.1 makes thin  paraboloid shell.
            #  E = 11.7 makes a radius of 12.0, 11.7 is the max needed.
            E, dE, dR       = 11.7, 1.0, 0.4
            self.paraboloid = Paraboloid.Paraboloid(E=E, dE=dE, dR=dR)
            if kw.get('verbose', False):
                print '%d layered paraboloid' % (len(self.paraboloid.ring))
                for r in arange(0.0,1.5,0.5):
                    ring = self.paraboloid.ring[r]
                    print 'ring[%2.2f](%d): ' % (r, len(ring))
                    for x,y in ring:
                        print '(%+3.1f,%+3.1f)' % (x,y),
                    print

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initTransforms():
            # Ratios against Inrared for each or R, G, and B
            I               = {c:self.wavelength['R'] / self.wavelength[c]
                    for c in 'RGB'}
            # Displacements to center R, G, and B affine transforms
            D               = {c: [d * (1.0 - I[c]) / 2 for d in (self.X, self.Y)]
                    for c in 'RGB'}
            # Affine transform matrices for R, G, and B
            self.M          = {c: array([[I[c], 0, D[c][0]], [0, I[c], D[c][1]]])
                    for c in 'RGB'}
            # Generate apertures for Airy kernels
            self.apertures = arange(1e-3, 9e-3, 1e-3)
            self.pupil      = 2
            self.aperture   = self.pupil * 1e-3
            if kw.get('verbose', False):
                for a in self.apertures: print a,
                print

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initRingKernel():
            # Generate the radius of convolution ring kernels (around micron size)
            self.ring = {n+1: around(1e6 * self.circle(
                wavelength=self.wavelength['R'], aperture=d), decimals=1)
                for n, d in enumerate(self.apertures)}

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initAiryKernel():
            # Generate an Airy convolution kernel
            self.KAiry = {n+1: self.genAiry(
                0, 0, self.wavelength['R'], d)
                for n, d in enumerate(self.apertures)}
            if kw.get('verbose', False):
                for n in self.ring.iterkeys():
                    print n, self.ring[n]
                print
                for n in self.ring.iterkeys():
                    print n, self.KAiry[n]
                print

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initGaussKernel():
            radius = 3
            span = 1 + 2 * radius
            self.KGauss = zeros((span,span), dtype=self.dtype)
            verbose = self.kw.get('verbose', False)
            if verbose: print 'initGaussKernel'
            for y in arange(-radius, radius+1, 1):
                y0 = y + radius
                for x in arange(-radius, radius+1, 1):
                    x0 = x + radius
                    r  = sqrt(float(x*x+y*y))
                    if verbose: print (x0, y0), (x, y), r
                    self.KGauss[x0, y0] = exp(-0.1*(r*r))
            self.KGauss *= 2e-1/sum(self.KGauss) # Why? 2e-1

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initOpenCV():
            # Setup OpenCV
            self.camera     = self.kw.get("camera", 0)
            self.capture    = CaptureFromCAM(self.camera)

            self.dtype      = float
            # Wavelengths for R, G, and B.
            self.wavelength = {'I':720e-9, 'R':566e-9, 'G':533e-9, 'B':433e-9}
            # A hack to prevent saturation.
            self.decay1     = 3e-1
            self.diffusion  = 4e+0
            self.dsize      = tuple(int(GetCaptureProperty(self.capture, p))
                    for p in (CV_CAP_PROP_FRAME_WIDTH, CV_CAP_PROP_FRAME_HEIGHT))
            self.X, self.Y  = self.dsize
            self.shape      = (self.Y, self.X, 3)
            self.paste      = CreateMat(self.Y, self.X, CV_8UC3)
            self.target     = asarray(GetSubRect(self.paste, (0,0, self.X,self.Y)))

            # Associate color planes with correct letter.
            self.plane      = {c:n for n,c in enumerate('BGR')}

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initPhotoreceptors():
            # Initialize human photoreceptor spectral transfer function.
            self.spectrum   = Spectrum()
            self.photoreceptors = Photoreceptors()
            Lcone       = self.spectrum['photoreceptor.L']
            Mcone       = self.spectrum['photoreceptor.M']
            Scone       = self.spectrum['photoreceptor.S']
            self.LL     = self.MM = self.SS = 1.0
            self.LM     = Lcone(self.wavelength['G'])
            self.LS     = Lcone(self.wavelength['B'])
            self.ML     = Mcone(self.wavelength['R'])
            self.MS     = Mcone(self.wavelength['B'])
            self.SL     = Scone(self.wavelength['R'])
            self.SM     = Scone(self.wavelength['G'])
            self.Lrow   = array([self.LL, self.LM, self.LS])
            self.Mrow   = array([self.ML, self.MM, self.MS])
            self.Srow   = array([self.SL, self.SM, self.SS])
            self.Lrow  /= self.Lrow.sum()
            self.Mrow  /= self.Mrow.sum()
            self.Srow  /= self.Srow.sum()
            self.xfer = array([self.Lrow, self.Mrow, self.Srow])
            self.LL, self.LM, self.LS = self.xfer[0]
            self.ML, self.MM, self.MS = self.xfer[1]
            self.SL, self.SM, self.SS = self.xfer[2]
            if kw.get('verbose', False):
                print 'photoreceptor transfer function'
                print self.xfer
            self.xfer   = self.xfer.flatten()

        #2222222222222222222222222222222222222222222222222222222222222222222222
        def initInitialParameters():
            self.test       = True
            self.slope      = 1e0
            self.scale      = 255.0
            self.char       = 'A'   # 'F' for cone signal
            self.iteration  = 0
            self.msg        = ''
            self.saturate   = False

            self.parameters(**kw)

            self.planeData  = {}
            self.stateData  = {}
            # Pre-allocate re-usable intermediate result array.
            self.keys     = {
                    'A': {'act': self.actA},
                    'B': {'act': self.actB},
                    'C': {'act': self.actC},
                    'D': {'act': self.actD},
                    'E': {'act': self.actE},
                    'F': {'act': self.actF},
                    'G': {'act': self.actG},
                    'H': {'act': self.actH},
                    'I': {'act': self.actI},
                    }
            self.signed = False
            # Careful! array labels do not match function labels.
            for L in self.keys.keys():
                self.planeData[L]= zeros((self.Y, self.X, 3), dtype=self.dtype)
            self.use('A')
            print 'LEGEND'
            for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if c in self.keys.keys():
                    self.aboutKey(c)
            print '\tSPACE:\ttoggle processing'
            print '\tPERIOD:\ttoggle test dots'
            print '\tESC:\tquit'
            print '-'*79
            self.aboutKey(self.char)

            # Local service functions for making shapes.
            def box(pattern, x0, y0, xr, yr):
                for y in arange(-yr, +yr+1):
                    for x in arange(-xr, +xr+1):
                        pattern += [(x0+x,y0+y),]
            def disk(x0, y0, r0): # Full filled circle
                for x, y in product(arange(-r0,+r0+1), repeat=2):
                    r = sqrt(x*x+y*y)
                    if r <= r0:
                        self.testW += [(x+x0,y+y0),]
            def curve(x0, y0, r0): # Quarter circle
                for x, y in product(arange(-r0,+r0+1), repeat=2):
                    r = sqrt(x*x+y*y)
                    if r > (r0-1) and r <= r0:
                        if x >= 0.0 and y >= 0.0:
                            self.testW += [(x+x0,y+y0),]

            # Find center and four half-diagonals
            x1  , y1   = self.X, self.Y
            x2  , y2   = x1  / 2, y1  / 2
            x4  , y4   = x2  / 2, y2  / 2
            x8  , y8   = x4  / 2, y4  / 2
            x16 , y16  = x8  / 2, y8  / 2
            x32 , y32  = x16 / 2, y16 / 2
            x64 , y64  = x32 / 2, y32 / 2
            x128, y128 = x64 / 2, y64 / 2
            N0, S0, E0, W0 = y2, y2, x2, x2
            N1, N2, N3 = N0-y16, N0-y8, N0-y4 # North
            S1, S2, S3 = S0+y16, S0+y8, S0+y4 # South
            E1, E2, E3 = E0+x16, E0+x8, E0+x4 # East
            W1, W2, W3 = W0-x16, W0-x8, W0-x4 # West
            self.testR, self.testG, self.testB = [], [], []
            self.testW = [
                    (E0,N0),
                    (W3,N2), (W3,S3), (E3,N3), (E3,S3),
                    (E2,N0), (E0,N2), (W2,S0), (W0,S2),
                    ]
            # Make a thin short bright horizontal line in the upper left.
            for x in arange(W2,W1):
                self.testW += [(x,N3),]
            # Make a thick short bright diagonal line in the upper right.
            for x in arange(E2,x2+x8+x32):
                self.testW += [(x  ,-x+y8-y64),]
                self.testW += [(x+1,-x+y8-y64),]
            # Make vertex between filled rectangles
            box(self.testR, W2        , S3    , x64, y64)
            box(self.testG, W2+x32    , S3    , x64, y64)
            box(self.testB, W2+x32-x64, S3+y32, x32, y64)
            # Filled circles and curved lines
            disk(W3, N2, x128)
            disk(E3, N2, x64 )
            curve(W3, S2, x128)
            curve(E3, S2, x64 )

        #1111111111111111111111111111111111111111111111111111111111111111111111
        # The order of execution for sub-init functions is important.
        self.newparams  = False # Set this true to read the JSON file.
        initOpenCV()
        initParaboloid()
        initTransforms()
        initRingKernel()
        initAiryKernel()
        initGaussKernel()
        initPhotoreceptors()
        initInitialParameters() # Must be last because of dependencies.

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def state(self, name):
        if not self.stateData.has_key(name):
            self.stateData[name] = zeros(self.shape, dtype=self.dtype)
        return self.stateData[name]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __call__(self):
        # Fetch the camera image.
        self.iteration += 1
        self.source     = asarray(
                GetMat(QueryFrame(self.capture))).astype(float)

        if self.test:
            # clear to black
            self.source[:,:,:] = 0

            # change every two seconds.
            value = 255.0 if (int(clock())/2) % 2 == 1 else 0.0

            # Put up blinking white dots
            #self.source[y2   ,x2   ,:] = value
            for x,y in self.testW: self.source[y,x,:] = value
            for x,y in self.testR: self.source[y,x,self.plane['R']] = value
            for x,y in self.testG: self.source[y,x,self.plane['G']] = value
            for x,y in self.testB: self.source[y,x,self.plane['B']] = value

        # Normalize input
        self.source /= self.scale
        # Run the chosen function.
        (self.full if self.active else self.noop)()
        # Display the result.
        ShowImage("Human refraction and diffraction", self.paste)
        return self.listen()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def parameters(self, **kw):
        self.kw       = kw
        if self.newparams:
            with open('Eye.json', 'r') as jsonfile:
                self.parameter = json.load(jsonfile)
        else:
            self.parameter = {}
        #elif self.iteration < 2:
            #self.parameter = {
                    #"pupil": self.pupil,
                    #"decay:Cone": 3e-1,
                    #"slope:cone": 1e0,
                    #"saturate": self.saturate,
                    #"active": True,
                    #}
        #self.report(
                #'Pupil: %d millimeters = %f' %
                #(self.pupil, self.aperture))
        #print self.parameter
        self.pupil    = self.parameter.get('pupil' , self.pupil)
        self.aperture = self.pupil * 1e-3
        #print self.pupil, self.aperture
        self.active   = kw.get('active', True)

        # Generate the convolution ring kernel
        ring = self.ring[self.pupil]
        self.Kring = self.paraboloid.ring[ring]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def copy(self, tgt, src):
        tgt[:,:,:] = src[:,:,:]
        return tgt

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def report(self, msg):
        print ' '*79 + '\r' + msg

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def tell(self, data = None):
        if data == None:
            print self.msg, self.iteration, '\r',
            self.msg = ''
            sys.stdout.flush()
        else:
            x,y = self.testW[0]
            self.msg += ' %+3.2e' % (data[y,x,0])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def noop(self):
        self.copy(self.target, self.source)
        self.tell(self.target)
        self.tell()
        self.final()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actA(self):
        """
        Source           (original scene)
        """
        self.signed = False
        self.copy(self.planeData['A'], self.source)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actB(self):
        """
        Refraction       (image after cornea and lens)
        """
        self.actA()
        self.signed = False
        self.refract()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actC(self):
        """
        Diffraction      (image after aperture)
        """
        self.actB()
        self.signed = False
        self.diffract()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actD(self):
        """
        Transfer         (image after cone absorption)
        """
        self.actC()
        self.signed = False
        self.transfer()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actE(self):
        """
        Absorption       (image after cone absorption decay)
        """
        self.actD()
        self.signed = True
        self.transduce() # Needs feedback from horizontal
        self.tsignal()
        self.horizontal()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actF(self):
        """
        Cone delta       (image of cone change)
        """
        self.actE()
        self.signed = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actG(self):
        """
        Horizontal       (image after temporospatial averaging)
        """
        self.actF()      # Generated in actE
        self.signed = False

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actH(self):
        """
        Horizontal delta (image of horizontal change)
        """
        self.actG()
        self.hsignal()
        self.signed = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actI(self):
        """
        Bipolar field    (image of delta between cone and horizontal delta)
        """
        self.actH()
        self.isignal()
        self.signed = False

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def actJ(self):
        """
        Bipolar transform (image of parabolic slice transient gradient vectors)

        Starting from an empty summation image,
        for each angle in spine set for chosen radius,
            correlate bipolar field with spine kernel,
            convert result to -1/0/+1 values by thresholding absolute value,
            then offset correlated field by spine kernel displacement,
            and add to summation image.
        Normalize to max of absolute values.
        """

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def refract(self):
        # Affine expand relative to wavelength for refraction.
        B = self.use('B')
        for b, m in [(self.plane[c], self.M[c]) for c in 'RGB']:
            B[:,:,b] = warpAffine(self.source[:,:,b], m, self.dsize)
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def use(self, c):
        return self.planeData[c]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def diffract(self):
        # Diffract: convolve with wave function having square above 1/255.
        # Square wave function for intensity.
        # filter2D actually correlates.  Use flip on kernel to convolve.
        # Symmetry makes this unnecessary.
        # K[pupil] is the kernel indexed by integer aperture in millimeters.
        blur = filter2D(self.planeData['B'], -1, self.KAiry[self.pupil]) ** 2
        #self.copy(self.use('C'), blur)
        self.copy(self.use('C'), blur / max(blur.max(), 1e-12))
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def transfer(self):
        # Cross channel transform
        # Photoreceptors absorb off-band photons.
        # For RGB photons from a computer monitor
        # these are the approximate efficiencies for
        # photon absorption by human photoreceptors.
        # Photoreceptors have types L(long), M(medium), and S(short)
        # for the wavelengths at which their principal peak is found.
        # Wavelengths recorded and produced by digital images (RGB)
        # have approximately similar types.
        # LL is the absorption coefficient of
        # photoreceptors of type L absorbing photons of type L.
        # LS is the absorption coefficient of
        # photoreceptors of type L absorbing photons of type S.
        # The transfer function for all such coefficients is a 3x3 matrix.
        LL, LM, LS, ML, MM, MS, SL, SM, SS = self.xfer
        L, M, S = R, G, B = 2, 1, 0

        # src is the RGB photon source, and fff are the LMS photoreceptors.
        src = self.planeData['C']
        tgt = self.use('D')

        # Perform the transfer.
        tgt[:,:,L] = (LL * src[:,:,L]) + (LM * src[:,:,M]) + (LS * src[:,:,S])
        tgt[:,:,M] = (ML * src[:,:,L]) + (MM * src[:,:,M]) + (MS * src[:,:,S])
        tgt[:,:,S] = (SL * src[:,:,L]) + (SM * src[:,:,M]) + (SS * src[:,:,S])
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def transduce(self):
        # Photoreceptors come into equilibrium with photon flux.
        # This function decays the photoreceptor state to equilibrium.
        # The difference between the state and the new flux
        # is considered signal.
        tgt = self.use('E')
        dif = self.planeData['F']
        fff = self.planeData['D']
        ggg = self.planeData['G']
        # Statefulness since last round

        self.copy(dif, 0.5 * (fff + ggg) - tgt)
        tgt[:,:,:] = tgt + self.decay1 * dif
        return self

    # DONE Adjust code to handle normalized input.
    # The problem is that the normalized values causes failures.
    # Engage the problems using the "-t" command-line option.

    # TODO understand the places marked "Why".
    # TODO Local averaging in horizontals biased by time average intensity.
    # TODO Bias comprises exp(-a*I) to account for reduced diffusion.
    # TODO Generate horizontal signal.
    # TODO Difference transduction signal with horizontal signal.
    # DONE Choose paraboloid height circle.
    # TODO Convolve receptor-horizontal difference with circle.
    # TODO Examine and adjust result to appear as ganglion-ready.

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def tsignal(self):
        # Signal is potentially negative so, to compensate,
        # the signal is biased to a median gray.
        self.use('F')
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def horizontal(self):
        src = self.planeData['E']   # Photoreceptor state
        tgt = self.use('G')         # Horizontal state
        dif = self.planeData['H']   # Horizontal change
        # TODO make self.KGauss dependent on average brightness
        # TODO rework math for horizontal
        self.copy(dif, src - tgt)
        tgt[:,:,:] = tgt + self.decay1 * dif
        blur = filter2D(-dif*src, -1, self.KGauss)
        self.copy(tgt, 0.5*(blur+src))    # cone + modified Gauss of neighborhood

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def hsignal(self):
        self.use('H')
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def isignal(self):
        dd = self.use('I')
        self.copy(dd, self.planeData['H'] * self.planeData['F'])
        threshold = -0.04
        dd[dd>=threshold] = 0.0
        dd[dd< threshold] = 1.0
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def final(self):
        # Normalize and scale.
        if not self.active:
            pass
        elif self.char in self.keys.keys():
            #if self.parameter.get("saturate", False) if self.newparams else self.saturate:
                #saturate = True
            #else:
                #saturate = False
            data = self.planeData[self.char]
            tmp  = zeros((self.Y, self.X, 3), dtype=self.dtype)
            self.copy(tmp, (data+1.0)/2.0 if self.signed else data)
            if self.saturate:
                self.copy(tmp, tanh(self.slope * tmp))
            self.copy(self.target, tmp * self.scale)
        else:
            self.noop()
        #if self.parameter.get("saturate", False) if self.newparams else self.saturate:
            #print 'saturating at', self.slope
            #self.copy(tmp, tanh(self.slope * tmp))
        #self.copy(self.target, tmp * self.scale)
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def full(self):
        if self.char in self.keys.keys():
            function = self.keys[self.char]['act']()
            self.tell(self.planeData[self.char])
        else:
            self.noop()
        self.final()
        return self

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def aboutKey(self, c):
        lines = self.keys.get(c, self.keys[c])['act'].__doc__.split('\n')
        self.report("\t"+c+": "+str.strip(lines[1] if len(lines) > 1 else lines[0]))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def listen(self):
        result = True
        # Check for keyboard input.
        key = WaitKey(6)    # milliseconds between polling (-1 if none).
        if key == -1:
            self.parameters()
            gc.collect()
            pass
        elif key == 27:
            result = False
        elif ord(' ') == key:
            self.active ^= True
            self.report('processing' if self.active else 'noop')
        elif ord('-') == key:
            if self.slope > 1.0: self.slope /= 1.1
            print 'slope', self.slope
        elif ord('+') == key or ord('=') == key:
            if self.slope < 1e3: self.slope *= 1.1
            print 'slope', self.slope
        elif ord('.') == key:
            self.test ^= True
            self.report('test pattern: ' + str(self.test))
        elif ord('!') == key and not self.newparams:
            self.saturate ^= True
            self.report('saturate: ' + str(self.saturate))
        elif ord('a') <= key <= ord('z'):
            c = chr(key - ord(' '))
            if c in self.keys.keys():
                self.char = c
                self.aboutKey(c)
        elif ord('1') <= key <= ord('8') and not self.newparams:
            self.pupil = key - ord('0')
            self.aperture = self.pupil * 1e-3
            self.report(
                    'Pupil: %d millimeters = %f' %
                    (self.pupil, self.aperture))
        else:
            #self.report('Unknown: %d' % (key))
            pass
        return result

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def pdf():
        with open("Eye.body.tex", "w") as target:
            with open(sys.argv[0]) as source:
                for line in source:
                    if line.startswith(';'):
                        #part['body'] += [line[1:].strip()]
                        print>>target, line[1:].strip()
        # run pdflatex, then bibtex, then pdflatex twice more.
        command = ["bibtex Eye", "pdflatex Eye.tex"]
        for i in range(4): os.system(command[i==1])
        return 'Eye.pdf'

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option( "-c", "--camera",
            type=int, default=0,
            help="choose a camera by int (default 0)")
    parser.add_option( "-v", "--verbose",
            action="store_true", default=False,
            help="announce actions and sizes")
    parser.add_option( "-p", "--pdf",
            action="store_true", default=False,
            help="generate TeX source")
    (opts, args) = parser.parse_args()
    kw = vars(opts)

    if opts.pdf:
        print 'read:', Eye.pdf()
    else:
        try:
            NamedWindow("Human refraction and diffraction", 1)
            eye = Eye(**kw)
            while eye(): pass
        finally:
            DestroyAllWindows()
"""
TeX block
; \bibliographystyle{plain}
; \bibliography{Eye}
; \appendix
;
; \pagebreak
; \section{How seen movement appears in the frog's optic nerve}\label{appendix:A}\cite{LettvinSeenMovement}
; Transcribed from a reprint
;
; Federation Proceedings Volume 18 Number 1 March 1959 Pages 393 and 354.
; H. Maturana, J. Y. Lettvin, W. H. Pitts, W. S. McCulloch
; Research Laboratory of Electronics, M.I.T. Cambridge, MA
; Transcribed in its entirety.
;
; \subsection{Part I (page 393)}
; The receptive field of a single optic nerve fiber
; (plotted by the on and off responses to small fixed spots)
; is often divisible into concentric cones.
; This suggests that the response of the fiber to a moving spot
; may be polar with respect to a reference point in the receptive field.
; Movement is indeed polarly encoded and there exists
; at least the following four types of fibers whose rate of firing depends on
; the centrifugal component of a movement
; with respect to some point internal to the receptive field
; (centripetal and tangential movements never cause discharge):
; Some fibers have wide receptive fields and low sensitivity.
; Of these some prefer the moving object darker than background,
; other prefer it lighter.
; A second group has constricted fields and high sensitivity.
; A third set shows a directional heavy weighting of the response.
; A fourth kind has annular fields.
; A fifth variety measures inversely
; the average intensity of illumination in a region.
; Its maximum rate is in the dark.
;
; \subsection{Part II (page 354)}
; The coding of movement described in Part I
; suggests that the frog's eye is designed
; (at least for land operation)
; to abstract the vector and size of a moving object
; and extrapolate the path.
; Because our evidence implies that there exists a coordinate system
; built into the retina and that the coding allows coordinates and velocity
; to arise from general operations on the whole output of the optic nerve,
; we propose some alternative guesses to account for
; Sperry's results on dislocated eyes.
; We do not propose that his notion of specific reconnection is wrong
; but that it is not necessary.
; We also present the law by which there is a point-to-point correspondence
; from receptors to optic nerve, vis.,
; if an object is moved within the visual field
; in a circular path of any diameter,
; the only fibers that show no response at any time
; are those that have the centers of their receptive fields
; at the center of the circle described.
"""

###############################################################################
