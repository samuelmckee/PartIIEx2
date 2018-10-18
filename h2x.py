from sys import exit
from argparse import ArgumentParser
from os import listdir
from math import *
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np


def get_data(dir):
    """
    Takes all Gaussian output files in directory and reads geometry and energy

    Checks all files in dir for .out extension, and reads geometry and energy
    for any correctly formatted files. If no files are found or the directory
    is not found then the program exits.

    Args:
        dir (str): directory to take Gaussian files from

    Returns:
        list of (float, float, float): List of tuples containing
                                       (r, theta, energy) for each file
    """

    try:
        file_list = [str for str in listdir(dir) if str.endswith('.out')]
    except (FileNotFoundError, NotADirectoryError):
        print('Directory %s not found.' % dir)
        exit()

    data = [get_point(filename, dir) for filename
        in file_list if get_point(filename, dir) != None]

    if len(data) != 0:
        print('Loaded %d files \n' % len(data))
        return data
    else:
        print('No .out files found in directory')
        exit()


def get_point(filename, dir):
    """
    Takes a single Gaussian output file and reads geometry and energy

    Args:
        filename (str): name of file to be read
        dir (str): directory containing file

    Returns:
        (float, float, float): (r, theta, energy) tuple for specified file
        None: if filename or content of file not correctly formatted
    """

    try:
        r = get_r(filename)
        t = get_theta(filename)
        e = get_energy(dir + '/' + filename)
        return (r,t,e)
    except:
        print('Failed to get data point for ' + filename)


def get_theta(filename):
    """
    Reads bond angle from Gaussian output file

    Args:
        filename (str): name of file to be read

    Returns:
        float: bond angle from file
    """

    theta = filename.split('theta')[1][:-4]
    return float(theta)


def get_r(filename):
    """
    Reads bond length from Gaussian output file

    Args:
        filename (str): name of file to be read

    Returns:
        float: bond length from file
    """

    r = filename.split('theta')[0].split('r')[-1]
    return float(r)


def get_energy(file_path):
    """
    Reads energy from Gaussian output file

    Args:
        file_path (str): full path + name of file to be read

    Returns:
        float: energy read from file
    """

    f = open(file_path, 'r')
    for line in f:
        if 'SCF Done' in line:
            l = line.split()
            f.close()
            return float(l[4])


def write_output(r_eq, t_eq, e_eq, nu_1, nu_2, rtol, ttol, dir, out):
    """
    Writes equilibrium geometry and vibrational frequencies to .txt file

    Args:
        r_eq (float): equilibrium bond length (in Angstroms)
        t_eq (float): equilibrium bond angle (in Degrees)
        e_eq (float): equilibrium energy (in Hartrees)
        nu_1 (float): frequency of symmetric stretch (in cm^-1)
        nu_2 (float): frequency of bend (in cm^-1)
        rtol (float): maximum r dispacement from equilibrium used for fitting
        ttol (float): maximum theta dispacement from equilibrium used for fitting
        dir (str): directory from which Gaussian output files were reads
        out (str): prefix to put on output file names
    """

    f = open(out, 'w')

    f.write('Data read from %s \n\n\n' % dir)
    f.write('Equilibrium geometry: \n\n')
    f.write('Bond length = %.2f Angstroms\n' % r_eq)
    f.write('Bond angle = %.0f degrees\n' % t_eq)
    f.write('Energy = %f Hartrees\n\n\n' % e_eq)
    f.write('Vibrational frequencties:\n\n')
    f.write('Frequency of symmetric stretch = %f cm^-1\n' % nu_1)
    f.write('An r tolerance of %.2f Angstroms was used.\n\n' % rtol)
    f.write('Frequency of bending mode = %f cm^-1\n' % nu_2)
    f.write('A theta tolerance of %.1f degrees was used.' % ttol)
    f.close()
    print('Wrote calculated parameters data to ' + out)


def plot_surface(data, out):
    """
    Plots 3D surface plot from list of tuples and saves figure as png file

    Data is interpolated onto 100x100 grid to give smooth colour transitions
    on surface

    Args:
        data (list of (float, float, float)): input data for surface plot
        out (str): prefix to put on output file names
    """

    # Prepare points to be plotted
    r,t,e = zip(*data)
    r_space = np.linspace(min(r),max(r),100)
    t_space = np.linspace(min(t),max(t),100)
    grid_r, grid_t = np.meshgrid(r_space, t_space)
    grid_e = griddata((r, t), e, (grid_r, grid_t), method='cubic')

    #Plot points and save figure
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.view_init(30,285)
    ax.set_xlabel('r / Angstroms')
    ax.set_ylabel('theta / degrees')
    ax.set_zlabel('Energy / Hartrees')
    ax.grid(False)
    ax.plot_surface(grid_r,grid_t,grid_e, rstride=1, cstride=1,
        cmap='inferno')
    plt.savefig(out, dpi = 300)
    print('Saved surface plot as ' + out)
    plt.close()


def fit_mode(data, tol, eq, out, xlabel, ylabel):
    """
    Takes list of (x,y) points and fits to a quadratic. Plots fitted quadratic.

    The fitted quadratic is plotted and saved to a png file with the data used
    to plot it.

    Args:
        data (list of (float, float)): input data for quadratic fit
        tol (float): maximum dispacement from equilibrium used for fitting
        eq  (float): equilibrium position in x data
        out (str): prefix to put on output file names
        xlabel (str): label to use for x axis on plot
        ylabel (str): label to use for y axis on plot

    Returns:
        float: coefficient on x^2
    """
    # Get data points within tolerance
    data.sort(key = lambda tup: tup[0])
    ys = [y for (x,y) in data if abs(x - eq) < tol]
    xs = [x for (x,y) in data if abs(x - eq) < tol]

    # Fit data to polynomial
    p = np.polyfit(xs, ys, 2)

    # Produce array of points for plotting fitted polynomial
    xs_fit = np.linspace(min(xs), max(xs), 100)
    ys_fit = [np.polyval(p, x) for x in xs_fit]

    # Plot raw data / fitted polynomial then save figure
    plt.scatter(xs, ys, marker='+', linewidth=0.5,color='k')
    plt.plot(xs_fit, ys_fit, linewidth=0.8, color='r')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(out, dpi = 300)
    print('Saved plot of fitted mode to ' + out)
    plt.close()

    # Return coefficient on x^2
    return p[0]


def main():

    # Read command line input
    parser = ArgumentParser(
        description='Reads Gaussian output files for triatomic and '
        'plots surface / calculates vibrational frequencies')
    parser.add_argument('dir', type=str,
        help='directory to retrieve files from')
    parser.add_argument('-f', '--file', type=str,
        help='prefix for files produced')
    parser.add_argument('-r', '--rtol', type=float, default=0.11,
        help='maximum dispacement from r minimum (in Angstroms) when fitting')
    parser.add_argument('-t', '--ttol', type=float, default=20.,
        help='maximum dispacement from theta minimum (in Degrees) when fitting')

    args = parser.parse_args()
    dir = args.dir
    rtol = args.rtol
    ttol = args.ttol
    out = args.file
    if out == None:  # Generate file name if none supplied
        out = '%s_r%.2f_t%.1f' % (dir.split('/')[-1], rtol, ttol)

    # Read in data
    data = get_data(dir)

    # Get equilibrium geometry
    r_eq, t_eq, e_eq = min(data, key = lambda tup: tup[2])

    # Values used in calculations
    wavenumber = 3.335641e-11  # Convert Hz to cm-1
    angstrom = 1.0e-10         # Convert angstrom to metres
    degree = pi / 180.         # Convert degrees to radians
    hartree = 4.35974e-18      # Convert hartree to J
    mu_1 = 2.0 * 1.66e-27      # Reduced mass for streching
    mu_2 = 0.5 * 1.66e-27      # Reduced mass for bending

    # Fit data along symmetric stretch
    r_mode = [(r, e) for (r, t, e) in data if t == t_eq]  # Keep t = t_eq)
    k_r = 2. * fit_mode(r_mode, rtol, r_eq, '%s_STRETCH.png' % out,
        'r / Angstroms', 'Energy / Hartrees')
    # k in hartrees angstroms^-2. Convert to J m^-2
    k_r *= hartree / ((angstrom)**2)

    # Fit data along bending mode
    t_mode = [(t, e) for (r, t, e) in data if r == r_eq]  # Keep r = r_eq
    k_t = 2. * fit_mode(t_mode, ttol, t_eq, '%s_BEND.png' % out,
        'theta / Degrees', 'Energy / Hartrees')
    # k in hartrees degree^-2. Convert to J radian^-2
    k_t *= hartree / (degree**2)

    # Calculate vibrational frequencties in cm-1
    nu_1 = sqrt(k_r / mu_1) / (2. * pi)  * wavenumber
    nu_2 = sqrt(k_t / ((r_eq * angstrom)**2 * mu_2)) / (2. * pi) * wavenumber

    write_output(r_eq, t_eq, e_eq, nu_1, nu_2, rtol, ttol, dir,
        '%s_OUTPUT.txt' % out)
    plot_surface(data, '%s_SURFACE.png' % out)


if __name__ == '__main__': # Don't run main automatically if imported
    main()