# BHSTools / Soft3121

**Open-source software/code for interfacing with Brinks BHS-3000/4000 alarm systems**

## Disclaimer

*While I have done my best to ensure this software is safe and functions as intended, it is provided AS IS. This software is neither supported nor endorsed by Brinks, ADT, Honeywell, IntelliSense, or any other third party, and was produced through reverse engineering. If you decide to use it on your hardware, you do so at your own risk. I am not responsible for any damage this software causes, including but not limited to malfunctioning or inoperative equipment, and any loss of life, limb, or property that may result from such malfunctions.*

*Also, please do not use my software on any equipment unless you own it, or otherwise have authorization from the owner, and make sure the owner is aware of the above disclaimer before proceeding. My intention is to make it possible to program one's own security equipment without hard-to-find hardware, as well as share technical discoveries about Brinks security equipment. My intention is NOT to aid in unauthorized tampering with security equipment.*

*The same applies to my work-in-progress implementation of the Vivaldi modem protocol. I am developing it for the purpose of personal experimentation, and am making it public for the use of anyone who is interested in the same, or has other legitimate uses for it. I am not sure whether or not this protocol can be used in a harmful way, but if it can, I do NOT encourage any such use. You take sole responsibility for your use of this software, so if you use it, do so responsibly. If anyone, including but not limited to ADT employees, is aware of any specific security concerns, you are encouraged to contact me about it; my email address is flarn2006@gmail.com.*

----

## How to program your panel

You're probably here because you want to program your Brinks system and don't have the special device the technicians use. Not a problem; with Soft3121, all you need is an easy-to-obtain UART or RS-485 interface, and you can program your system with your PC.

### Using the UART port

The best way to link a PC to a BHS-4000 or BHS-3000 is via the factory programming port on the main panel. This port has five pins, with a gap between two of them, and is labeled "J8". This provides a direct connection to the serial port on the panel's CPU. (More specifically, the "ASC0" port, for anyone familiar with the C161 series.) The pinout is as follows:

    [ 1 2 3 4   6 ]

	1: P0L.4 (used for bootloader access)
	2: TX (panel out, PC in) (MISO on Bus Pirate)
	3: RX (panel in, PC out) (MOSI on Bus Pirate)
	4: GND
	6: Like AUX, but always active (not needed here)

If you are using a [Bus Pirate](http://dangerousprototypes.com/docs/Bus_Pirate), the following sequence of serial terminal commands will configure it properly:

	b 7
	     (set terminal to 38400 baud and press Space as prompted)
    m 3 7 1 1 1 1
	(1)
	     (type 'y' when prompted)

The reason UART is the best option is because this way, your PC will have its own link to the panel separate from other devices that are hooked up. Furthermore, the system is capable of booting via this port, which will enable you to restore the system if its programming or firmware ever becomes corrupted to the point where it won't boot normally. (You shouldn't be able to corrupt the programming to this extent using the regular programming menus, but I've seen it happen seemingly at random before.)

I have had bad luck using the Raspberry Pi's built-in UART for this purpose; the Pi can receive data from the panel just fine but the panel hasn't responded to anything I've tried sending to it. Though your mileage may vary; maybe it will work fine for you. Interestingly, this issue doesn't always occur with BSL communications (more on that shortly) though I have still encountered issues in the past.

### Using RS-485

The other way to connect your PC is through the system's data bus, the same way that keypads and other peripherals communicate with the panel. For this, you will need an RS-485 adapter. **If you are buying an adapter for this purpose, make sure it has either two or three terminals on it. Some have four or five, and I don't think those are compatible.**

If you look at your alarm's main panel, you will see several screw terminals with wires in them. Two of them should be labeled "DATA" and "CLK". This is the IntelliBus port, to which keypads and other peripheral devices are wired.

You may also notice a small connector (labeled "J3") with four pins. This provides the same exact connection; the rightmost pin (looking at it with the screw terminals below the connector) is DATA, and the one immediately to the left of it is CLK. This is the installer programming port, which is where a Brinks technician would plug in the handheld programmer that Soft3121 replaces.

You will need to wire your RS-485 adapter to the panel, with the "A" terminal going to DATA, and the "B" terminal going to CLK. If your adapter's terminals are not labeled A and B, just guess which one goes to which; guessing wrong won't do any damage. If your adapter has three terminals instead of two, ignore the "GND" one, or optionally you can connect it to one of the "-" terminals on the panel, which I guess is recommended if you plan on leaving it attached permanently.

*(If you're familiar with RS-485, you might be a bit confused by the use of "DATA" and "CLK", as RS-485 doesn't use a clock signal. The truth is, the "CLK" terminal is mislabeled. It actually carries the complementary data line, not a clock signal.)*

Now, it's easiest to wire it to the screw terminals, as you can use regular wire for that. However, if you have the right kind of connector ([this kind](https://www.allelectronics.com/item/con-244/4-pin-connector-w/header-0.10/1.html) fits perfectly, but any standard male-to-female jumper wire should work), attaching it to the programming port will avoid the need to loosen the screws, so there's no risk of other wires falling out.

Once you have it wired, plug the adapter into your computer. You'll probably want to use a laptop for this, though something like a Raspberry Pi is ideal if you want something you can conveniently leave connected to the panel to access over a network. You'll need to determine what serial port the adapter appears as—if you're using Windows, it will most likely be COM3 or a higher-numbered port, though you may need to install a driver before it will work. Look in Device Manager to be sure. If you're on Linux, run `ls /dev/ttyUSB*`; if you just plugged in the adapter, it's probably the highest-numbered one.

### Next steps

Run `s3121.py`, giving the serial port as an argument. For example, `./s3121.py /dev/ttyUSB0` (Linux) or `s3121.py COM3` (Windows), though your command may be different.

Next, open a Web browser and point it to http://127.0.0.1:3121. If you're doing this remotely, such as over SSH to a Raspberry Pi, substitute that device's IP address. **Warning: By default, this software is currently configured to listen on all network interfaces; this means anyone on your network will be able to access your system's programming. If this is a problem, edit `s3121.py` and replace `0.0.0.0` with `127.0.0.1`, though this will make it impossible for you to access it from another device on the network as well.**

If all goes well, a Web page will load. If you happen to have caught a glimpse of the handheld programmer your installer used to configure your system (the S3121), then this screen may look familiar to you—Soft3121 is a software-based clone of that same device, which your alarm panel will see as if it's the real thing.

Since all of the menu screens are generated by the system itself (with the programmer acting as more of a "dumb terminal"), you will still be prompted to enter the installer's access code (which you most likely don't have) before the system will grant you access to the programming interface. The good news is that Soft3121 can trick your system into revealing this code for you: just click Download Programming to start the process.

How does this work? These systems contain the capability to have ~~Brinks~~ ADT remotely dial in and access the system's programming, a connection which may take place over the built-in modem, or possibly via an external communicator such as a cellular modem. When you click Start on that screen, Soft3121 will simulate an "upload" request from ADT, and proceed to talk the panel through the process of uploading all of its configuration data (including the installer code) to your PC. (For this reason, if you access the event log, you will likely see this event listed as a "Host comm Config Upload".)

For more information on programming, refer to the [BHS-4000B installation manual](https://archive.org/details/bhsmanuals/Install_Programming_Manual_4000B/mode/2up). In case you have a BHS-3000, the [BHS-3000C manual](https://archive.org/stream/bhsmanuals/BHS-3000C%20Installation%20%26%20Programming%20Manual#mode/2up) is also available, but the 4000B manual is much more detailed and a lot of it applies to BHS-3000 systems as well. (Tip: If you download the manual and save it as "manual.pdf" in the "static" directory, overwriting the file that's already there, it will be viewable inside the Soft3121 Web interface.)

See the [Frequently Asked Questions](https://github.com/flarn2006/BHSTools/wiki/faq) page; there are in fact many questions I've been frequently asked, so if you have any questions, they may very well be answered there.

### Taking full control

The Infineon C161PI, which powers the BHS-3000 and BHS-4000 panels, contains a built-in Bootstrap Loader that allows for booting the system via a serial connection in place of the connected ROM chip. As I mentioned above, C161PI-based Brinks panels conveniently expose all the connections needed to do so on port J8. By sending custom boot code to the panel via this port, you can do pretty much anything you want with the system, including:

* Creating a full dump of the panel's EEPROM (firmware + programming data)
* Restoring a "bricked" panel by reflashing it
* Modifying or replacing the panel's firmware
* Directly executing arbitrary code on the panel's CPU

The `bsl` directory contains some scripts for taking advantage of this functionality. For more information about the bootstrap loader, see the [Infineon C161PI user manual](http://www.keil.com/dd/docs/datashts/infineon/c161pi_um.pdf), "The Bootstrap Loader", page 273.
