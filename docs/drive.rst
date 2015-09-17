#############
Drive control
#############

The classes described here are used to control the radio telescope's
drives via an Arduino Due-based controller which runs qp
(https://bitbucket.org/nxg/qp) by Norman Gray.


Configuration
=============

The configuration settings for the drive class are checked for in the
main settings.cfg used for the entire package.

Earth location should be given as latitude and longitude, in degrees, and elevation, in metres.

Drive
=====
.. autoclass:: acreroad_1420.drive.Drive
   :members:
