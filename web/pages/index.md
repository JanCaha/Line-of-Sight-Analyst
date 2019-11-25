# Introduction

**Line of Sight Analyst** toolbox is a Python toolbox for *ArcGIS* of version *10.x*. The tool aims to extend possibilities provided by existing tools *Construct Sight Lines* and *Line of Sight* in *ArcGIS* *3D Analyst's Visibility* toolbox.

While *Line of Sight* can be used to determine if target points are visible from observer points, which parts of the line-of-sight (LoS) are visible and invisible and where is the main obstacle located on LoS. These informations form an important part of the visibility information, however, these are often inadequate for proper assessment of visibility. Complete visibility assessment requires calculation of several LoS characteristics that can not be done by existing tools in *ArcGIS*.

**Line of Sight Analyst** provides tools for easier creation of LoS, analysing LoS and extracting important points from LoS. Besides these functions that are directly related to the visibility analysis the toolbox contains a tool for optimization of point location based on raster values.

## Releases

Releases are available at [GitHub]({{ toolbox.github_relases}}). Last release is {{ toolbox.version }} and it is public since {{ toolbox.release_year }}.

## Licence

The toolbox is released under [{{toolbox.licence}}]({{toolbox.licence_link}})

## News

### ver. 0.7.0

- Parameter *Use earth curvature and refraction corrections?* is now by default checked for all tools.

### ver. 0.6.7

- Bug fixed in elevation difference to global horizon calculation.</li>

### ver. 0.6.6

- Minor bug fixes and description texts clarification.
			
### ver. 0.6.0

- Added Earth curvature and atmospheric refraction corrections for all relevant tools.

### ver. 0.5.1

- First public release.

## Known Issues

- No issues are known at this time.
- If you found an error feel free to create Issue at [GitHub]({{toolbox.github_issue}}).

## Future Plans

- Future versions will include suggestions from users and testers, if there will be any.
- There plans for tools that would deal with linear horizons (definition, extraction from the surface and evaluation).