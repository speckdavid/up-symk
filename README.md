# Integration of SymK with the Unified Planning Library

## Installation
Currently we are in the development phase and everything has to be built locally. First, build locally our version of the  [unified planning library](https://github.com/speckdavid/unified-planning) where we have registered SymK.

```
git clone git@github.com:speckdavid/unified-planning.git
pip install unified-planning/
```

Then install this package.

```
git clone git@github.com:speckdavid/up-symk.git
pip install up-symk
```

## Usages
In the [notebooks folder](notebooks/), you can find a minimal example that executes the selected optimal planner configuration using symbolic bidirectional blind search.