import usb_cdc

# Enable both the REPL (console) and data serial ports
usb_cdc.enable(console=True, data=True)