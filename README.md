# BHSTools / Soft3121

**Open-source software/code for interfacing with Brinks BHS-3000/4000 alarm systems**

## Disclaimer

*While I have done my best to ensure this software is safe and functions as intended, it is provided AS IS. This software is neither supported nor endorsed by Brinks, ADT, Honeywell, IntelliSense, or any other third party, and was produced through reverse engineering. If you decide to use it on your hardware, you do so at your own risk. I am not responsible for any damage this software causes, including but not limited to malfunctioning or inoperative equipment, and any loss of life, limb, or property that may result from such malfunctions.*

*Also, please do not use my software on any equipment unless you own it, or otherwise have authorization from the owner, and make sure the owner is aware of the above disclaimer before proceeding. My intention is to make it possible to program one's own security equipment without hard-to-find hardware, as well as share technical discoveries about Brinks security equipment. My intention is NOT to aid in unauthorized tampering with security equipment.*

----

## How to program your panel

You're probably here because you want to program your Brinks system and don't have the special device the technicians use. Not a problem; with Soft3121, all you need is an easy-to-obtain RS-485 or UART interface, and you can program your panel with your PC.

**If you are using RS-485, make sure the adapter is the kind with two or three terminals. Some have more than that; I am not sure if this kind will work.**

### Using RS-485

If you look at your alarm's main panel, you will see several screw terminals with wires in them. Two of them should be labeled "DATA" and "CLK". This is the IntelliBus port, to which keypads and other peripheral devices are wired.

You may also notice a small connector (labeled "J3") with four pins. This provides the same exact connection; the rightmost pin (looking at it with the screw terminals below the connector) is DATA, and the one immediately to the left of it is CLK. This is the programming port, for connecting the official programming device.

You will need to wire your RS-485 adapter to the panel, with the "A" terminal going to DATA, and the "B" terminal going to CLK. If your adapter's terminals are not labeled A and B, just guess which one goes to which; guessing wrong won't do any damage. If your adapter has three terminals instead of two, ignore the "GND" one, or optionally you can connect it to one of the "-" terminals on the panel, which I guess is recommended if you plan on leaving it attached permanently.

Now, it's easiest to wire it to the screw terminals, as you can use regular wire for that. However, if you have the right kind of connector, attaching it to the programming port will avoid the need to loosen the screws, so there's no risk of other wires falling out.

Once you have it wired, plug the adapter into your computer. You'll probably want to use a laptop for this, though something like a Raspberry Pi is ideal if you want something you can conveniently leave connected to the panel to access over a network. You'll need to determine what serial port the adapter appears as—if you're using Windows, it will most likely be COM3, though you may need to install a driver before it will work. Look in Device Manager to be sure. If you're on Linux, run `ls /dev/ttyUSB*`; if you just plugged in the adapter, it's probably the highest-numbered one.

### Using the UART port

Another option is to use the factory programming port, labeled "J8". This provides a direct connection to the serial port on the panel's CPU. (More specifically, the "ASC0" port, for anyone familiar with the C161 series.) This port has five pins, with a gap between two of them. The pinout is as follows:

    [ 1 2 3 4   6 ]

	1: P0L.4 (used for bootloader access)
	2: TX (panel out, PC in) (MOSI on Bus Pirate)
	3: RX (panel in, PC out) (MISO on Bus Pirate)
	4: GND
	6: Like AUX, but always active (not needed here)

If you are using a [Bus Pirate](http://dangerousprototypes.com/docs/Bus_Pirate), the following sequence of serial terminal commands will configure it properly:

	b 7
	     (set terminal to 38400 baud and press Space as prompted)
    m 3 7 1 1 1 1
	(1)
	     (type 'y' when prompted)

If all you need to do is program your panel in the traditional sense (as an installer would) then you will only need to use pins 2 (TX), 3 (RX), and 4 (GND). However, if you're interested in experimenting with your system at a lower level, you can ground pin 1 (P0L.4) while powering up the panel to enter BSL (Bootstrap Loader) mode. This will bypass the panel's firmware, and allow you to directly execute code on the processor. I'll soon post a script that uses this to dump the panel's ROM. For more information, see the [Infineon C161PI user manual](http://www.keil.com/dd/docs/datashts/infineon/c161pi_um.pdf), "The Bootstrap Loader", page 273.

### Next steps

Run `s3121.py`, giving the serial port as an argument. For example, `./s3121.py /dev/ttyUSB0` (Linux) or `s3121.py COM3` (Windows), though your command may be different.

Next, open a Web browser and point it to http://127.0.0.1:3121. If you're doing this remotely, such as over SSH to a Raspberry Pi, substitute that device's IP address. **Warning: By default, this software is currently configured to listen on all network interfaces; this means anyone on your network will be able to access your system's programming. If this is a problem, edit `s3121.py` and replace `0.0.0.0` with `127.0.0.1`, though this will make it impossible for you to access it from another device on the network as well.**

If all goes well, a Web page will load with an interface resembling the official programming device, and of course it should function like said device as well.

For more information on programming, refer to the [BHS-4000B installation manual](http://alpha.adt.com/content/dam/sop/sop/Product%20Knowledge/PanelPDFs/Install_Programming_Manual_4000B.pdf).
