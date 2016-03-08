#############
Observation Scheduler
#############

The observation scheduler allows jobs to be queued-up and performed
with minimal human intervention.

While `acreroad_1420` only controls the drives, the scheduler is
capable of executing a program, for example an observing program.

Examples
========

The easiest way to understand the functionality of the scheduler is through some examples.

Drift Scan
----------

.. code-block:: python
   
		# Set up the scheduler
		from acreroad_1420 import drive, schedule
		import numpy as np
		import astropy
		# Make the connection to the drive
		connection = drive.Drive('/dev/ttyACM0', 9600, simulate=0)
		# Start the queue up
		jobs = schedule.Scheduler(drive=connection)

		##########################################################################

		# For convenience let's have the number of seconds in a day in a variable
		day = 24*3600

		# Make an observation
		jobs.at("08 03 2016 17:10:00",             # Start at 17:10 on 8/3/16
		script='/home/astro/srt2016/observing.py', # Run this GNURadio script
		position="h180.0 +56.08",                  # Point the telescope at az=180d, alt=+56d
		forsec=day                                 # Run the observation for 24*3600 seconds
		)



The classes described here run the observation scheduler for the radio
telescope.

Scheduler
=========
.. autoclass:: acreroad_1420.schedule.Scheduler
   :members:

