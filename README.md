# lxc-calibrate

_Note: This is very much not for production use_

A toy I built to investigate the idea of calibrating the CPU of your local LXC container (using cgroups)
to match the CPU of your remote production / staging server(s).

## Usage

### Profile

You first need to profile your remote server:

```bash
python lxc-stress.py
```

This will give you an average run time for the stress test. You need to provide this when calibrating
your container.

_Note: You'll probably also want to profile your local machine. If the stress test takes longer
to run on your local machine then there's no way to calibrate your local container to match_

### Calibrate

Now that you have the average run time for the stress test you can calibrate your local container to
match:

```bash
python lxc-calibrate.py [Container Name] [Live Server Profile Time]
```

This should search for the correct settings to make the stress test run on your local container
in the same time it took on your remote server.