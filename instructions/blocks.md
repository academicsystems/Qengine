## Qengine - Blocks

The following is a list of the block types that come default with Qengine and are essential to understand in order to write questions.

#### qhtml
```
{%qhtml:namespace
    <p>Place HTML here</p>
%}
```
Any HTML here will be sent to the quiz front-end to be viewed by the student. You can use the Qengine shortcodes to automatically generate HTML input elements with the required attributes or to insert resources like images. Refer to [shortcodes.md](shortcodes.md) for a list of available shortcodes.

#### qcss
```
{%qcss:namespace
    p { color:red; }
%}
```
Any CSS styles you want to use with your HTML in a qhtml block can be set here.

#### files
```
{%files:namespace
    local_image.jpg
    https://example.com/some_remote_image.png
%}
```
You can use this block to retrieve files, which can be inserted into the qhtml block using a shortcode.

If referring to a remote file, do not use the entire url, only the actual file name.

Local files should be stored in the same folder as the `question` file.

#### qstore
```
{%qstore:namespace
    temp.namespace.variable
    perm.namespace.variable
%}
```

Variables generated by blocks or Qengine variables included in the first step, are not stored between question steps unless you use this block. Prepend variable names with `temp.` to keep them for only the next step. Prepend the variable names with `perm.` to keep them for all further steps.

#### qans
```
{%qans:namespace
    @@namespace.grade@@
%}
```

This block is used to report a grade of between 0 and 1 to the quiz front-end. Usually a grade is calculated in another block and stored in a variable, which is then put into this block. 

**!!!** *important →* This block can only be used once! Once it is used, no further steps will be processed.



