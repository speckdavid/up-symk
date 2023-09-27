# Integration of SymK with the Unified Planning Library

This repository was created within the `Symbolic Search for Diverse Plans and Maximum Utility` project funded by the by the [AIPlan4EU project](https://www.aiplan4eu-project.eu/). 
This project aims to enhance the [unified planning library](https://github.com/aiplan4eu/unified-planning) with four expressive extensions to traditional classical planning using the symbolic search planner [SymK](https://github.com/speckdavid/symk).

## Installation
Currently, we are in the development phase. 
We recommend building our version of the [unified planning library](https://github.com/speckdavid/unified-planning) locally and then building this `up-symk` package locally.

Please note that many core functionalities have already been merged into the official unified planning library repository, and the stable pypi version is available. You can install everything with `pip install unified-planning` and `pip install up-symk`. 
However, it's important to be aware that the stable version 1.0.0 of unified-planning does not include all the necessary changes yet. 
Therefore, we recommend following the installation steps below to proceed:

Clone and install the unified-planning library.

```
git clone git@github.com:speckdavid/unified-planning.git
pip install unified-planning/
```

Then install this package using pip:
```
pip install up-symk
```

Alternatively, you can install it locally by following these steps:

Ensure you have the necessary packages to build Symk:

```
sudo apt-get -y install cmake g++ make python3 autoconf automake git
```

Clone and build the package.

```
git clone git@github.com:aiplan4eu/up-symk.git
pip install up-symk/
```

## Usages
In the [notebooks folder](notebooks/), you can find two examples of how to use the SymK planner within the unified planning library.
 - [Multi-Solution Generation: Using SymK in the Unified Planning Library](https://github.com/aiplan4eu/up-symk/blob/master/notebooks/symk_usage.ipynb)
 - [Optimizing Plan Utility: Using SymK in the Unified Planning Library](https://github.com/aiplan4eu/up-symk/blob/master/notebooks/symk_osp_usage.ipynb)
 - [Axioms and Derived Predicates in the Unified Planning Library](https://github.com/speckdavid/up-symk/blob/master/notebooks/axioms_usage.ipynb)
