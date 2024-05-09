# Lattice
This repository contains experimental code for the Lattice experiment. It uses the [ACF framework](https://github.com/HaeffnerLab/acf).

## Installation
Move into the artiq working directory.
```bash
cd {artiq working directory}
```

Clone this repository.
```bash
git clone git@github.com:HaeffnerLab/lattice.git
```

Symlink folders out into the artiq working directory.
```bash
ln -s lattice/repository/ repository
ln -s lattice/acf_config/ acf_config
ln -s lattice/acf_sequences/ acf_sequences
```
