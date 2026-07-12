# Assignment 1: Stage Design (TMX)

**Due:** Week 4 | **Points:** 100 | **Unit:** II (Vectors & Tilemaps)

## Objective

Design and implement a playable game stage using Tiled and the Legacy of InFest framework. You will create a `.tmx` tilemap that includes terrain, enemies, collectibles, player spawn, and checkpoints.

## Deliverables

| Item | Points | Location |
|---|---|---|
| TMX tilemap file | 30 | `assets/maps/your_stage_name.tmx` |
| Stage scene (Python) | 25 | `src/stages/your_stage/` |
| Player spawn & checkpoints | 15 | TMX object layers |
| Enemies placed correctly | 10 | `Enemies` layer in TMX |
| Collectibles | 10 | `Collectibles` tile layer |
| Metadata (author, zone, name) | 5 | TMX properties |
| Tileset integrity | 5 | Relative paths, no broken refs |

## Requirements

### TMX Map Requirements
- Width/height: 40x23 tiles minimum, 80x60 maximum
- Tile size: 32x32px (use `tileset_stage_template.tsx`)
- Required tile layers: `Terrain`, `Collectibles`, `Checkpoint`
- Optional tile layers: `Decorations`, `Hazards`
- Required object layer: `Objects`
- Must contain a `PlayerSpawn` object (type=`PlayerSpawn`) in `Objects`
- Must contain 1+ checkpoint objects (type=`Checkpoint`)

### Custom Properties (on map)
| Property | Type | Description |
|---|---|---|
| `author` | string | Your full name |
| `zone` | int | Zone number (1-8) |
| `stage_id` | string | e.g. `"1-1"` |
| `stage_name` | string | Display name of stage |
| `climate` | string | `"desert"`, `"forest"`, `"cemetery"`, `"ice"`, `"lava"`, `"factory"` |

### Enemies
- Add 2-5 enemy spawn points in `Enemies` layer
- Valid types: `Walker`, `Shooter`, `Flying`, `Charger`, `Boss`
- Each enemy object must have `type` property matching the class

### Collectibles
- At least 5 collectible tiles in `Collectibles` layer
- Coins are tile ID 1, gems are tile ID 2

## Grading Rubric

| Category | Points | Criteria |
|---|---|---|
| TMX Parses | 10 | No XML errors, valid Tiled format |
| Required Layers | 10 | Terrain, Collectibles, Checkpoint, Objects |
| Player Spawn | 10 | Exactly 1 PlayerSpawn object |
| Checkpoints | 5 | At least 1 checkpoint object |
| Enemies | 10 | Valid types, properly placed |
| Enemies count | 5 | 2-5 enemy spawns |
| Collectibles | 10 | 5+ collectible tiles |
| Metadata | 5 | author, zone, stage_id, stage_name |
| Tileset valid | 10 | Relative paths, valid images |
| Map bounds | 10 | Within 40x23-80x60 range |
| Climate valid | 5 | One of the valid climate strings |
| No broken refs | 10 | All tile references exist |

## Submission

Push your completed stage to your GitHub Classroom repo. The grading script will run automatically via CI.

```bash
git add assets/maps/your_stage.tmx src/stages/your_stage/
git commit -m "feat: complete stage design"
git push
```

Check your grade in the CI Actions tab.
