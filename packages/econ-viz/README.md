# econ-viz

`econ-viz` was renamed to **[utility-viz](https://pypi.org/project/utility-viz/)** in 2.0.

This package depends on `utility-viz` (the same version, pinned) and adds the compatibility layer for
existing 1.x code, throughout 2.x: the `econ_viz` import package and the `econ-viz` command. Using
either emits a deprecation warning. Both are removed in 3.0.

```bash
pip install utility-viz          # use this name from now on (no econ_viz, no econ-viz command)
```

While 2.x is only available as a pre-release (currently 2.0.0b3), upgrading an existing installation
needs `--pre`: `pip install --pre --upgrade econ-viz`.

See the migration guide: https://github.com/EconViz/utility-viz#migrating-from-econ-viz
