# Public Data Validation Registry

Updated: July 12, 2026

## Verified Listening.bio Run

Listening.bio processed a real public recording through its production-shaped upload and BirdNET pipeline.

| Field | Value |
|---|---|
| Recording | Xeno-canto `XC364638` |
| Source label | American Robin (`Turdus migratorius`) |
| Recordist | Ted Floyd |
| Source | https://xeno-canto.org/364638 |
| License | CC BY-NC-SA 4.0 |
| Pipeline mode | Configured BirdNET inference |
| Job result | Completed |
| Candidate detections | 7 |
| Expected species detections | 4 American Robin windows |
| Strongest expected confidence | 0.768 |
| Result artifact | `work/demo/XC364638-listening-bio-result.json` |

This proves the software can ingest real audio, execute BirdNET, normalize results, and preserve the review trail. It does not prove field accuracy or ecological validity. The two low-confidence thrush candidates and one Western Tanager candidate demonstrate why thresholds, location/date context, and expert review matter.

## Approved Testing Sources

### Xeno-canto

Use recordings individually and preserve the recording-level license, recordist attribution, source URL, species label, location, and recording date. Do not assume every file has the same license. The current verified sample is noncommercial and share-alike, so it is appropriate for research/demo validation but not unrestricted commercial redistribution.

Recommended use: small, attributed functional tests and transparent demos.

### BirdCLEF

BirdCLEF provides large benchmark collections and annotated soundscapes. Use the dataset release associated with a specific challenge and follow that release's competition and redistribution terms. BirdCLEF 2018, for example, describes 36,496 training recordings and an annotated validation soundscape collection.

Recommended use: repeatable benchmarking after confirming the selected year's terms.

### Macaulay Library and eBird

Use eBird observation data and Macaulay media only under their applicable terms. Do not bulk download or redistribute media without confirming permission. These sources are better suited to partner-supported validation, metadata comparison, and expert review than to an assumed open training corpus.

## Next Validation Set

Build a 30-recording test pack before field deployment:

- 10 high-quality target-species recordings from the northeastern United States.
- 10 urban soundscapes with traffic, people, weather, and overlapping birds.
- 5 negative controls containing environmental sound but no known bird vocalization.
- 5 difficult clips with weak calls or multiple species.

For every file, store source, license, attribution, expected labels, date, coordinates, and allowed use. Report precision and recall only after a qualified reviewer has produced reference annotations.

## Source References

- Xeno-canto sample: https://xeno-canto.org/364638
- Creative Commons license: https://creativecommons.org/licenses/by-nc-sa/4.0/
- BirdCLEF 2018 dataset description: https://www.imageclef.org/node/230
- Cornell BirdNET Analyzer: https://birdnet.cornell.edu/analyzer/
