# Copyright (C) 2015  Brunel Odegard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This LabRAD client identifies active serial COM ports.
For each port available, it queries the port with known
identification commands. If the port responds, the Serial
Device Manager will write an entry in the LabRAD registry
identifying the port as corresponding to a particular
type of device.
"""

# ports that the manager will always ignore.
global blacklistedPorts
blacklistedPorts = ['COM1']

# For now, host is defined here.
global host
host = 'localhost'

import time
import platform
import labrad

class serialDeviceManager(object):
	def __init__(self):
		self.serialConnect()

	def serialConnect(self):
		"""Initializes connection to LabRAD, the serial server, and the registry"""

		self.cxn = labrad.connect(host) # connect to labrad
		computerName = platform.node()  # get computer name

		# LabRAD prefaces the serial server name with the computer name
		# after shifting to lower case and replaceing spaces with underscores.
		self.serialServerName = computerName.lower().replace(' ','_') + '_serial_server'

		self.ser = self.cxn.servers[self.serialServerName] # connect to serial server
		self.reg = self.cxn.registry                       # connect to the registry

	def run(self):
		"""Tries to identify any ports found"""
		serialPorts = self.ser.list_serial_ports()                                      # all serial ports found
		activePorts = [port for port in serialPorts if (port not in blacklistedPorts)]  # filter out ports present in blacklistedPorts
		print("Found %i active serial port(s): %s"%(len(activePorts),str(activePorts))) # Print out number, names of ports found

		for port in activePorts:
			self.identifyPort(port)

	def regWrite(self,serverType,deviceName,port):
		"""Writes an entry in the registry linking 'port' to 'data'"""

		# If 'Servers' folder doesn't exist in registry root, make it.
		self.reg.cd('')
		if not ('Servers' in self.reg.dir()[0]):
			self.reg.mkdir('Servers')
			print('Folder "Servers" does not exist in registry. Creating it.')

		# In folder "Servers," create the folder serverType if it doesn't exist.
		self.reg.cd(['','Servers'])
		if not (serverType in self.reg.dir()[0]):
			self.reg.mkdir(serverType)
			print('Folder "%s" does not exist in "Server." Creating it.'%serverType)

		self.reg.cd(['','Servers',serverType]) # Finally, go the the pre-existing or newly created location
		keys = self.reg.dir()[1]               # Fetch list of existing keys

		if not (deviceName in keys):                              # If this device (deviceName) doesn't have a key already, make it.
			self.reg.set(deviceName,(self.serialServerName,port)) # Write the port info.
			print("Device %s of type %s not in registry. Adding it..."%(deviceName,serverType))

		else:                                          # If this device already has an entry
			existingPort = self.reg.get(deviceName)[1] # Get the port that supposedly corresponds to this device

				if port == existingPort: # Device already in registry, port number agree.
					print("Device %s of type %s is already in the registry with port %s"%(deviceName,serverType,port))

				else: # Device already in registry, port numbers disagree.
					print("Device %s of type %s is already in registry. Ports disagree. (OLD:%s, NEW:%s). Overwriting..."%(deviceName,serverType,existingPort,port))
					self.reg.set(deviceName,(self.serialServerName,port)) # Write the port info.

		# [!!!!] ADD THIS FUNCTIONALITY
		# search for other entries linked to the same port (not including this result. This should only happen if a port changes device.)
		# If none: do nothing
		# If one : prompt user - delete?
		# If many: prompt delete (a/s/n) all / selective / none


	def identifyPort(self,port):
		"""Attempts to idenfiy any given port"""

		print("")                              # 
		print("Connecting to port %s..."%port) # 
		self.ser.open(port)                    # connect to the given port
		
		#####################
		## ACbox and DCbox ##
		#####################
		print("Trying device type: AC/DC box") # 
		acdcBoxBaudrate = 115200               # baudrate for this device
		self.ser.baudrate(acdcBoxBaudrate)     # set the baudrate
		self.ser.write('\r\n');self.ser.read() # flush the interface
		ser.write("*IDN?\r\n")                 # query identification command
		response = ser.read_line()             # get response from device

		if response.startswith('DCBOX_DUAL_AD5764'):                         # For a DCBOX, the response to *IDN? will be "DCBOX_DUAL_AD5764(NAME)"
			print("Port %s identified as a DCBOX_DUAL_AD5764 device."%port)  # Print info that port has been identified
			self.regWrite('ad5764_dcbox',port)                               # Write a registry entry identifying this port as corresponding to a DCBOX_DUAL_AD5764 device
			return True                                                      # Returning True tells the run() function that the port has been identified.

		if response.startswith('ACBOX_DUAL_AD5764'):                         # For an ACBOX, the response to *IDN? will be "ACBOX_DUAL_AD5764(NAME)"
			print("Port %s identified as an ACBOX_DUAL_AD5764 device."%port) # Print info that port has been identified
			self.regWrite('ad5764_acbox',port)                               # Write a registry entry identifying this port as corresponding to an ACBOX_DUAL_AD5764 device.
			return True                                                      #

		time.sleep(1) # sleep 1 second between attempts to identify. This prevents flooding the port with signals too quickly.







if __name__ == '__main__':
	sdm = serialDeviceManager()
	sdm.run()
	raw_input("Finished. Press enter to exit.")
