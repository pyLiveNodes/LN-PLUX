[![Format and Test](https://github.com/pyLiveNodes/LN-PLUX/actions/workflows/format_test.yml/badge.svg)](https://github.com/pyLiveNodes/LN-PLUX/actions/workflows/format_test.yml)
[![Publish](https://github.com/pyLiveNodes/LN-PLUX/actions/workflows/publish.yml/badge.svg)](https://github.com/pyLiveNodes/LN-PLUX/actions/workflows/publish.yml)

# LN PLUX

The Livenodes PLUX package provides recording nodes for the PLUX family of sensors including the MuscleBan, BiosignalsHub and RIoT sensor platforms.

[LiveNodes](https://livenodes.pages.csl.uni-bremen.de/livenodes/index.html) are small units of computation for digital signal processing in python. They are connected multiple synced channels to create complex graphs for real-time applications. Each node may provide a GUI or Graph for live interaction and visualization.

Any contribution is welcome! These projects take more time, than I can muster, so feel free to create issues for everything that you think might work better and feel free to create a MR for them as well!

Have fun and good coding!

Yale

## Installation

`pip install livenodes_plux `

## Docs

You can find the docs [here](https://livenodes.pages.csl.uni-bremen.de/packages/livenodes_plux/readme.html).

## Restrictions

Some, the nodes rely on PLUX's provided share objects. These are currently only added for linux based machines, but should be extended. See [issue #3](https://gitlab.csl.uni-bremen.de/livenodes/packages/livenodes_plux/-/issues/3).
