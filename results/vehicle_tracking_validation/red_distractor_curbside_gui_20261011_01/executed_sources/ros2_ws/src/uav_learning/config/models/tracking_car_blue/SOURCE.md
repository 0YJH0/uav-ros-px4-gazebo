# Blue Vehicle Asset

- Source: https://app.gazebosim.org/OpenRobotics/fuel/models/Hatchback%20blue
- Publisher: OpenRobotics, Fuel model version 5.
- Download: https://fuel.gazebosim.org/1.0/OpenRobotics/models/Hatchback%20blue/5/Hatchback%20blue.zip
- License: CC0 1.0 Universal (https://creativecommons.org/publicdomain/zero/1.0/).
- Downloaded ZIP SHA256: `1659265c26d026ae5dbb7edf9106acf2a479073ba213da04ca5699fb39b34892`.
- Local modifications: model mesh URIs and body texture paths made relative for
  offline installation; missing remote wheel texture replaced by the existing
  red vehicle's dark wheel material; blue mesh, texture, and material names made
  unique to avoid the red vehicle's render cache. No runtime remote texture
  references remain.
- Original mesh SHA256 matches the red vehicle. Vertex, normal, UV, and face
  data remain identical after local material-name changes; only appearance differs.

Runtime validation snapshots hash these installed source assets. This asset is
only used by the separate different-color overtaking scenario, not by the
historical same-appearance crossing benchmark.
