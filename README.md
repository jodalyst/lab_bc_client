# lab-bc-client

This is the client-side source for F25 lab-bc build infrastructure in 6.205 and, as needed, 6.S965. Assuming you are in "our system", this piece of software allows you to run builds for Xilinx series FPGAs as well as run simulations using [Cocotb](https://www.cocotb.org) with Vivado XSim hooks as enabled with [Vicoco](https://github.com/kiran-vuksanaj/vicoco/tree/main/test/sim).

# Installation

The lab-bc client software requires only Python. Greater than 3.12 is recommended, though I think back to 3.10 will probably work. Create a virtual Python environment. I _strongly_ recommend you do that rather than use system Python. You can do this quite easily with the following code which makes a virtual environment called `6205_python`:

```
python3 -m venv 6205_python
```

While not strictly necessary, you can also run the virtual environment creation with the `--copies` modifier to ensure the virtual environment is completely isolated from your system Python.

Once created, activate your Python virtual environment with:

```
source 6205_python/bin/activate
```

You should then be able to install this library by running the command:

```
pip install git+https://github.com/jodalyst/lab_bc_client
```

EZPZ.

# Usage

After installation in your terminal, you can use `lab-bc` at any time if you have your Python virtual environment activated.

## Configuration (Do One Time After Installation)

Prior to your first run on `lab-bc`, make sure to run:

```
lab-bc configure
```

And provide your kerberos (lowercase), MIT ID, the lab-bc server endpoint (for Fall 2025 6.205/6.S965 this is likely `fpga3.mit.edu/lab-bc2`). These will be used to verify your submissions to the build server. You only need to run `configure` once after the installation. The system should verify your credentials when you submit them. If you get a error/issue, read what it says...maybe you aren't in the class so your credentials aren't on the machine? Maybe you typed in the wrong server endpoint?

## Running Builds

Any time you want to build, you can simply do:

```
lab-bc build {project} {build_tcl_file}
```

For example, if you are in a project directory and your build script is called `build.tcl`, you would run:

```
lab-bc build ./ build.tcl
```

The output of a build will show up in a `obj` folder (including all logs and the bit file).

## Running Simulations

If you want to run a Cocotb simulation remotely (you should only be doing this when you need `vicoco` functionality), the command pattern is:

```
lab-bc simulate {project} {simulate_py_file}
```

For examp,e if you in a project directory and you have a simulate file called `sim_1.py` inside your `sim` folder, you would do:

```
lab-bc simulate ./ sim/sim_1.py
```

The simulation will run and the output content will show up in a `sim_build` folder placed in the root of your project folder.

## Throttling

We expect you to be verifying and testing your designs locally whenever possible.  Verilog syntax checking can very easily be done by just doing `iverilog -i -g2012 whatever.sv` where `whatever.sv` is the file you care about, the `g2012` flag tells it to use SystemVerilog and the `i` flag says to ignore modules that are used but not defined. If you choose not to do this and instead send repeated builds up to the server for things like syntax checking, this may get flagged. If you abuse `lab-bc` and/or use it to check syntax errors repeatedly (which really should be getting verified locally using icarus Verilog), the server may throttle and/or limit your submissions and/or put you into timeout.  Please be aware of this.  Additionally, if you start to prematurely terminate a lot of builds, the machine server may also start to throttle you and/or put you into timeout.

# Archiving

`lab-bc` will automatically make zipped snapshots of your project and its results every time you run it. These will be placed into the `_history` folder and be named using the timestamp of the submission. I added this since you students tend to be horrendous with version control.  Note, this archive can get large when you're doing many builds so feel free to delete files if you ever want.

# Included Files and Folders

In order to minimize sending junk to the server, only a particular subset of folders and files will get sent to the server on a build or simulation. By default only the following directories will be submitted: `xdc`, `sim`, `hdl`, `data`, `ip`. If for whatever reason you need to include additional resources, in the configuration file that is written when you run `lab-bc configure` (generally located wherever your computer places configuration files which on Mac/*Nix platforms is in `~/.config/lab-bc/config.ini`, there is an additional array that you can add additional files to. For example, if you have content inside a folder called `pirated_metallica_albums`, then you would modify `config.ini` to have `additional_allows = ['pirated_metallica_albums']` and that will then get zipped/included/sent up to the server when you build and/or simulate.

# Provenance

This project is based on an original version developed by Jay Lang as part of his [2023 M.Eng thesis at MIT](https://dspace.mit.edu/handle/1721.1/151412?show=full).  The version found in this repo is largely a ground-up rewrite done in Python for portability and maintainability. That should not be taken as a

For security reasons, other portions of the current lab-bc project (server and worker source code) are private, but if interested, reach out to me at jodalyst@mit.edu.
