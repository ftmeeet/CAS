import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory
from org.orekit.propagation.analytical.tle import TLEPropagator,TLE

orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

line1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  9994"
line2 = "2 00005 034.2682 348.7242 1859667 331.7664 019.3264 10.82419157413667"
tle = TLE(line1,line2)
prop = TLEPropagator.selectExtrapolator(tle)
state = prop.propagate(tle.getDate().shiftedBy(3.0*86400))
print(state)
print(state.getPVCoordinates(FramesFactory.getTEME()))