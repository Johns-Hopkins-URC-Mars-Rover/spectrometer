import usb.core
import usb.util
import time
import numpy as np


def connect_spectrometer():
    # Find the Ocean Optics USB2000+ device
    device = usb.core.find(idVendor=0x2457, idProduct=0x101E)
    
    if device is None:
        raise ValueError("USB2000+ spectrometer not found")
    
    # Detach kernel driver if active
    if device.is_kernel_driver_active(0):
        device.detach_kernel_driver(0)
    
    # Set configuration
    device.set_configuration()
    
    return device

def initialize_spectrometer(device):
    # Initialize the spectrometer
    device.write(0x01, [0x01])  # Endpoint 1 Out, Command 0x01
    time.sleep(0.1)

def set_integration_time(device, time_ms):
    # Set integration time in milliseconds
    time_us = time_ms * 1000  # Convert to microseconds
    command = [0x02]
    command.extend([time_us & 0xFF, 
                  (time_us >> 8) & 0xFF, 
                  (time_us >> 16) & 0xFF, 
                  (time_us >> 24) & 0xFF])
    device.write(0x01, command)
    time.sleep(0.1)

def request_spectrum(device):
    # Request a spectrum
    device.write(0x01, [0x09])
    time.sleep(0.1)
    
    # Read the spectrum data
    data = []
    for i in range(8):  # 8 packets for full spectrum
        try:
            packet = device.read(0x82, 512)  # EP2 address
            data.extend(packet)
        except:
            break
    
    # Convert to pixel values
    pixels = []
    for i in range(0, len(data), 2):
        if i+1 < len(data):
            pixel_value = data[i] | (data[i+1] << 8)
            pixels.append(pixel_value)
    
    return pixels

def interpret_spectrum(active_pixels, start_wavelength=400, end_wavelength=700):
    """
    Interpret spectrometer data into human-readable format.

    Parameters:
        active_pixels (list): Intensity values for active pixels (20-2047).
        start_wavelength (float): Starting wavelength in nm (e.g., 400 nm).
        end_wavelength (float): Ending wavelength in nm (e.g., 700 nm).

    Returns:
        list: A list of tuples (wavelength, intensity).
    """
    # Number of active pixels
    num_pixels = len(active_pixels)
    
    # Generate corresponding wavelengths (linear mapping)
    wavelengths = np.linspace(start_wavelength, end_wavelength, num_pixels)
    
    # Combine wavelengths and intensities
    spectrum_data = list(zip(wavelengths, active_pixels))
    
    return spectrum_data

def print_spectrum(spectrum_data):
    """
    Print the spectrum data in a human-readable format.

    Parameters:
        spectrum_data (list): A list of tuples (wavelength, intensity).
    """
    print(f"{'Wavelength (nm)':<20}{'Intensity':<10}")
    print("-" * 30)
    for wavelength, intensity in spectrum_data:
        print(f"{wavelength:<20.2f}{intensity:<10}")


import matplotlib.pyplot as plt

def plot_spectrum(spectrum_data):
    """
    Plot the spectrum data as a wavelength vs intensity graph.

    Parameters:
        spectrum_data (list): A list of tuples (wavelength, intensity).
    """
    wavelengths, intensities = zip(*spectrum_data)
    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, intensities, label="Spectrum")
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity')
    plt.title('Wavelength vs Intensity')
    plt.grid(True)
    plt.legend()
    plt.show()




def main():
    try:
        print("Starting spectrometer connection...")
        # Connect to the spectrometer
        device = connect_spectrometer()
        print("conneted")
        # Initialize
        initialize_spectrometer(device)
        print("initialized")

        # Set integration time (100ms)
        set_integration_time(device, 100)
        print("integration time set")
        # Acquire spectrum
        spectrum = request_spectrum(device)
        print("spectrum acquired")
        # Process active pixels (20-2047)
        active_pixels = spectrum[20:2048]

        # Interpret the spectrum
        spectrum = interpret_spectrum(active_pixels)
        print("spectrum interpreted")
        # Print the spectrum in a human-readable format
        print_spectrum(spectrum)

        #Do something with spectrum variable, try to send it to jetson( array of tuples )


        plot_spectrum(spectrum)
        # Plot the spectrum
        # plt.figure(figsize=(10, 6))
        # plt.plot(active_pixels)
        # plt.xlabel('Pixel')
        # plt.ylabel('Intensity')
        # plt.title('USB2000+ Spectrum')
        # plt.grid(True)
        # plt.savefig('spectrum.png')
        # plt.show()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
