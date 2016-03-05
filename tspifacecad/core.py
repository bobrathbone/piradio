import tspifacecommon.mcp23s17
import tspifacecommon.interrupts
import tspifacecad.lcd


DEFAULT_SPI_BUS = 0
DEFAULT_SPI_CHIP_SELECT = 1
NUM_SWITCHES = 8


class NoTspifacecadDetectedError(Exception):
    pass


class Tspifacecad(tspifacecommon.mcp23s17.MCP23S17,
                tspifacecommon.interrupts.GPIOInterruptDevice):
    """A PiFace Control and Display board.

    :attribute: switch_port -- See
        :class:`tspifacecommon.mcp23s17.MCP23S17RegisterNeg`.
    :attribute: switches --
        list containing :class:`tspifacecommon.mcp23s17.MCP23S17RegisterBitNeg`.
    :attribute: lcd -- See :class:`tspifacecad.lcd.PiFaceLCD`.

    Example:

    >>> cad = tspifacecad.Tspifacecad()
    >>> hex(cad.switch_port.value)
    0x02
    >>> cad.switches[1].value
    1
    >>> cad.lcd.write("Hello, PiFaceLCD!")
    >>> cad.lcd.backlight_on()
    """
    def __init__(self,
                 hardware_addr=0,
                 bus=DEFAULT_SPI_BUS,
                 chip_select=DEFAULT_SPI_CHIP_SELECT,
                 init_board=True):
        super(Tspifacecad, self).__init__(hardware_addr, bus, chip_select)

        self.switch_port = tspifacecommon.mcp23s17.MCP23S17RegisterNeg(
            tspifacecommon.mcp23s17.GPIOA, self)

        self.switches = [tspifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
            i, tspifacecommon.mcp23s17.GPIOA, self)
            for i in range(NUM_SWITCHES)]

        if init_board:
            self.init_board()

        self.lcd = tspifacecad.lcd.PiFaceLCD(
            control_port=tspifacecad.lcd.HD44780ControlPort(self),
            data_port=tspifacecad.lcd.HD44780DataPort(self),
            init_lcd=init_board)

    def enable_interrupts(self):
        self.gpintena.value = 0xFF
        self.gpio_interrupts_enable()

    def disable_interrupts(self):
        self.gpintena.value = 0x00
        self.gpio_interrupts_disable()

    def init_board(self):
        ioconfig = (
            tspifacecommon.mcp23s17.BANK_OFF |
            tspifacecommon.mcp23s17.INT_MIRROR_OFF |
            tspifacecommon.mcp23s17.SEQOP_ON |
            tspifacecommon.mcp23s17.DISSLW_OFF |
            tspifacecommon.mcp23s17.HAEN_ON |
            tspifacecommon.mcp23s17.ODR_OFF |
            tspifacecommon.mcp23s17.INTPOL_LOW
        )
        self.iocon.value = ioconfig
        if self.iocon.value != ioconfig:
            raise NoTspifacecadDetectedError(
                "No PiFace Control and Display board detected "
                "(hardware_addr={h}, bus={b}, chip_select={c}).".format(
                    h=self.hardware_addr, b=self.bus, c=self.chip_select))
        else:
            # finish configuring the board
            self.iodira.value = 0xFF  # GPIOA as inputs
            self.gppua.value = 0xFF  # input pullups on
            self.gpiob.value = 0
            self.iodirb.value = 0  # GPIOB as outputs
            self.enable_interrupts()


class SwitchEventListener(tspifacecommon.interrupts.PortEventListener):
    """Listens for events on the switches and calls the mapped callback
    functions.

    >>> def print_flag(event):
    ...     print(event.interrupt_flag)
    ...
    >>> listener = tspifacecad.SwitchEventListener()
    >>> listener.register(0, tspifacecad.IODIR_ON, print_flag)
    >>> listener.activate()
    """
    def __init__(self, chip=None):
        if chip is None:
            chip = Tspifacecad()
        super(SwitchEventListener, self).__init__(
            tspifacecommon.mcp23s17.GPIOA, chip)
