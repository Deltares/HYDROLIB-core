# Polyline/Polygon Files Documentation

## Overview

Polyline (.pli/.pliz) and polygon (.pol) files are basic spatial input files for a [D-Flow FM](glossary.md#d-flow-fm) model to select particular locations, and are used in various other input files. The `hydrolib.core.dflowfm.polyfile` module provides functionality for reading, writing, and manipulating these files.

Polyline files consist of one or more blocks, each containing:
1. An optional description (lines starting with `*`)
2. A name line
3. A dimensions line (number of rows and columns)
4. A series of points with coordinates and optional data

### File Format

A typical polyline file has the following structure:

```
* Optional description line 1
* Optional description line 2
name_of_polyline
2    3    # number_of_points number_of_columns
    10.0    20.0    0.0    # x y z
    30.0    40.0    0.0    # x y z
```

The file can contain multiple such blocks, each defining a separate polyline object.

## Class Diagram

```
┌───────────────┐     ┌───────────────┐
│  Description  │     │    Metadata   │
├───────────────┤     ├───────────────┤
│ content: str  │     │ name: str     │
└───────────────┘     │ n_rows: int   │
                      │ n_columns: int│
                      └───────────────┘
                             ▲
                             │
┌───────────────┐     ┌─────┴─────────┐     ┌───────────────┐
│     Point     │◄────│   PolyObject  │     │   PolyFile    │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ x: float      │     │ description   │◄────│ has_z_values  │
│ y: float      │     │ metadata      │     │ objects       │
│ z: Optional   │     │ points        │     └───────────────┘
│ data: List    │     └───────────────┘             │
└───────────────┘                                   │
                                                    ▼
                      ┌───────────────┐     ┌───────────────┐
                      │    Parser     │     │  Serializer   │
                      ├───────────────┤     ├───────────────┤
                      │ feed_line()   │     │ serialize_*() │
                      │ finalize()    │     └───────────────┘
                      └───────────────┘
```

## Core Classes

### PolyFile

`PolyFile` is the main class representing a polyline file. It inherits from `ParsableFileModel` and provides methods for reading, writing, and accessing polyline data.

Key methods:
- `x` property: Returns all x-coordinates as a list
- `y` property: Returns all y-coordinates as a list
- `get_z_sources_sinks()`: Gets z-values for source and sink points
- `number_of_points` property: Returns the total number of points

### PolyObject

`PolyObject` represents a single block in a polyline file, containing a description, metadata, and a list of points.

### Point

`Point` represents a single point in a polyline, with x and y coordinates, an optional z coordinate, and additional data values.

### Metadata

`Metadata` contains information about a polyline block, including the name, number of rows (points), and number of columns (values per point).

### Description

`Description` represents comments for a polyline block, with content starting with `*` in the file.

## Sequence Diagram: Reading a Polyfile

```
┌─────────┐          ┌──────────┐          ┌────────┐          ┌────────────┐
│  Client │          │ PolyFile │          │ Parser │          │ PolyObject │
└────┬────┘          └────┬─────┘          └───┬────┘          └─────┬──────┘
     │                     │                    │                     │
     │ PolyFile(filepath)  │                    │                     │
     │────────────────────>│                    │                     │
     │                     │                    │                     │
     │                     │ read_polyfile()    │                     │
     │                     │───────────────────>│                     │
     │                     │                    │                     │
     │                     │                    │ feed_line()         │
     │                     │                    │─────────────────────│
     │                     │                    │                     │
     │                     │                    │ finalize()          │
     │                     │                    │─────────────────────│
     │                     │                    │                     │
     │                     │<───────────────────│                     │
     │                     │                    │                     │
     │<────────────────────│                    │                     │
     │                     │                    │                     │
```

## Sequence Diagram: Writing a Polyfile

```
┌─────────┐          ┌──────────┐          ┌────────────┐          ┌────────────┐
│  Client │          │ PolyFile │          │ Serializer │          │    File    │
└────┬────┘          └────┬─────┘          └─────┬──────┘          └─────┬──────┘
     │                     │                      │                       │
     │ polyfile.save()     │                      │                       │
     │────────────────────>│                      │                       │
     │                     │                      │                       │
     │                     │ write_polyfile()     │                       │
     │                     │─────────────────────>│                       │
     │                     │                      │                       │
     │                     │                      │ serialize_poly_object()│
     │                     │                      │───────────────────────│
     │                     │                      │                       │
     │                     │                      │ write lines           │
     │                     │                      │───────────────────────│
     │                     │                      │                       │
     │                     │<─────────────────────│                       │
     │                     │                      │                       │
     │<────────────────────│                      │                       │
     │                     │                      │                       │
```

## Usage Examples

### Reading a Polyline File

```python
from pathlib import Path
from hydrolib.core.dflowfm.polyfile.models import PolyFile

# Read a polyline file
polyfile = PolyFile(filepath=Path("path/to/file.pli"))

# Access the polyline objects
for poly_obj in polyfile.objects:
    print(f"Name: {poly_obj.metadata.name}")
    print(f"Number of points: {len(poly_obj.points)}")

    # Access points
    for point in poly_obj.points:
        print(f"  Point: ({point.x}, {point.y})")
        if point.z is not None:
            print(f"  Z-value: {point.z}")
        if point.data:
            print(f"  Data: {point.data}")
```

### Creating and Writing a Polyline File

```python
from pathlib import Path
from hydrolib.core.dflowfm.polyfile.models import PolyFile, PolyObject, Metadata, Point, Description

# Create a new polyline file
polyfile = PolyFile(has_z_values=True)

# Create a polyline object
poly_obj = PolyObject(
    description=Description(content="This is a test polyline"),
    metadata=Metadata(name="test_polyline", n_rows=2, n_columns=3),
    points=[
        Point(x=10.0, y=20.0, z=0.0, data=[]),
        Point(x=30.0, y=40.0, z=1.0, data=[])
    ]
)

# Add the polyline object to the file
polyfile.objects = [poly_obj]

# Save the file
polyfile.save(filepath=Path("path/to/output.pli"))
```

### Accessing Coordinates

```python
from pathlib import Path
from hydrolib.core.dflowfm.polyfile.models import PolyFile

# Read a polyline file
polyfile = PolyFile(filepath=Path("path/to/file.pli"))

# Get all x and y coordinates
x_coords = polyfile.x
y_coords = polyfile.y

# Get the total number of points
total_points = polyfile.number_of_points

# Get z-values for source and sink points (for .pliz files)
z_source, z_sink = polyfile.get_z_sources_sinks()
```

## File Extensions

The module supports different file extensions:
- `.pli`: Standard polyline file
- `.pol`: Polygon file (same format as .pli)
- `.pliz`: Polyline file with z-values

## Error Handling

The parser includes robust error handling for various issues:
- Invalid dimensions
- Missing points
- Invalid point data
- Empty lines (generates warnings)
- Incomplete blocks

## API Reference

### Model
::: hydrolib.core.dflowfm.polyfile.models

### Parser
::: hydrolib.core.dflowfm.polyfile.parser

### Serializer
::: hydrolib.core.dflowfm.polyfile.serializer
