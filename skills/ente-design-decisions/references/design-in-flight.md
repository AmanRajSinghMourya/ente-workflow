# Design work in flight

Areas currently being designed. **Check this before closing any design decision.**

Match on the paths — if what you're about to touch is listed here, stop and read
the entry rather than answering locally. Work done in a live area gets discarded
by the redesign, or collides with it.

Maintained by the design pipeline: entries are added when a feature opens, and
updated when a gate is approved, parked or killed. Not maintained by hand.

Format:
```
### <area>
Paths:      <the file paths this covers>
In flight:  <what is being designed>
Mode:       Map | Decide | Make
Status:     active | parked <date>
Safe to do: <what a developer can still change here, if anything>
Ask first:  <what must not be touched>
```

---

### Location and places

```
Paths:      mobile/apps/photos/lib/ui/viewer/location/
            mobile/apps/photos/lib/services/location_service.dart
            mobile/apps/photos/lib/core/constants.dart (defaultRadiusValues)

In flight:  Remodel. "Location" currently means two different things — a photo's
            coordinates, and a saved named circle (location tag). The redesign
            splits the concept before touching any screen. Figma wireframes and
            nine prototype iterations exist.

Mode:       Decide
Status:     parked — 16 Sep 2026

Safe to do: bug fixes, crashes, performance, string typos that don't rename a
            concept.

Ask first:  the radius picker, the add/edit location sheets, anything using the
            words "location" or "place" in user-facing copy, and any change to
            how a photo joins a place.
```
