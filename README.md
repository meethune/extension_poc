# extension_poc

Proof of concept [X4: Foundations](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/) extension mod template.

Uses [x4cat](https://github.com/meethune/x4cat) to pack mod files into `.cat/.dat` catalogs.

## Structure

```
content.xml              — Extension manifest (loose file, required by X4)
src/                     — Mod files (packed into catalog)
  md/                    — Mission Director scripts
  aiscripts/             — AI behavior scripts
  libraries/             — Library XML overrides
dist/                    — Build output (do not commit)
schemas/                 — XSD schemas extracted from game (do not commit)
tests/                   — Build validation tests
```

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Build

```bash
make all              # validate, build, test
make build            # pack src/ into dist/ext_01.cat + copy content.xml
make validate         # XML well-formedness + structural checks
make test             # full test suite (includes build verification)
make clean            # remove dist/
```

## Schema validation

Optionally extract XSD schemas from your X4 install for full schema validation
of MD and AI scripts:

```bash
make schemas X4_GAME_DIR="/path/to/X4 Foundations"
make schema-validate
```

Note: full XSD validation is slow (~70s) due to the size of Egosoft's schemas.
The default `make all` uses fast structural checks instead.

## Installing

Copy the contents of `dist/` into your X4 extensions directory:
```
<X4 install>/extensions/extension_poc/
```

The directory should contain `content.xml`, `ext_01.cat`, and `ext_01.dat`.

## License

MIT
