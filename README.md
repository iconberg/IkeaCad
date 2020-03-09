# IkeaCad
Bleander addon for creating simple geometry for furniture.

## short usage description
Executing the addon will create and open a textfile for editing. Input your desired objects. Close the editor and the addon create the objects. Unsaved .blend-files create a temporary file, saved files get a ikeacad.txt file beside the .blend-file.

Example: https://github.com/iconberg/IkeaCad/blob/master/media/ikeacad_example1.webm

### create/rotate/place
```
<dimension>x<dimension>   create plane, starting entry with a dimension is a must
r(x|y|z)<angle>           rotate around xyz-axis in given order
p(x|y|z)<location>        place at xyz-location
:<color>                  : for additional data, only object color yet

*modifier                 * to set an modifier for following commands
*solidify()               supported parameters: thickness, use_rim, use_rim_only, use_even_offset
                          (remove) for unset modifier, it removes the oldest
```
- You can place more than one command on a line seperated by TAB.
- Empty lines are allowed.
- Objects without location are arranged around the first defined object.

### example usage
```
100x100               gives a plane with 100x100
100x100rx90           rotate it 90 on the x-axis
100x100ry90x45  			rotate it 90 on the y-axis, then 45 on the x-axis
100x100px100y200			place it at x100 and y200
```
### enable/disable solidify
```
*solidify(thickness=.03:use_rim=true:use_rim_only=false:use_even_offset=true)
*solidify(remove)
```

### Example BILLY Bookcase
```
80x28:yellow
*solidify(thickness=.02:use_rim=true:use_rim_only=false:use_even_offset=true)
106x28ry90
106x28ry90
76x28
76x28
76x28
76x28
76x6rx90
```
