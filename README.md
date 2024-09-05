# lab-bc-client
Client-side source for F24 lab-bc build in 6.205 and, as needed 6.S965

# Instructions

Create a virtual Python environment. I _strongly_ recommend you do that rather than use system Python. You can do this quite easily with:

```
python3 -m venv 6205_python
```

Activate your Python virtual environment with:

```
source 6205_python/bin/activate
```

Clone this repository onto your machine.  Move into the repo and then run (with virtual environment activated):

```
pip install .
```

After installation in your terminal, you can use `lab-bc` at any time if you have your Python virtual environment activated.

Prior to your first run on `lab-bc`, make sure to run:

```
lab-bc configure
```

And provide your kerberos and MIT ID. These will be used to verify your submissions to the build server. You only need to run that once after the installation.

Any time you want to build, you can simply do:

```
lab-bc run project
```

Things will run, you'll get a readout and then all of your output files will appear in the `obj` folder inside your `project` folder when done.





_This project is based on an original version developed by Jay Lang as part of his [2023 M.Eng thesis at MIT](https://dspace.mit.edu/handle/1721.1/151412?show=full).  The version found in this repo is largely a ground-up rewrite done in Python for portability and maintainability. That should not be taken as a


For security reasons, other portions of the current lab-bc project (server and worker source code) are private, but if interested, reach out to me at jodalyst@mit.edu.
